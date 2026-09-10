"""## Executive summary (read this first)

Run leakage-safe pseudo-asof comparisons across every public Track 2 card. A cutoff is chosen from
the common dated history, each model sees only observations at or before that cutoff, and the
forecast is compared with the first panel observation on or after the requested business-day
horizon.

The official metric primitives are imported from the pinned public toolkit. Private normalization
scales and realized card answers are unavailable and are not recreated. To prevent high-unit assets
from dominating this diagnostic, candidate components are paired with the frozen Numeric v1 result
for the same unit and cutoff before equal-weight aggregation across historical cases.
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import tomllib
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from qfbench2_common.scoring.crps import crps_marginal, variogram_score

from qfbench2_track_forecasting.cli import _read_panels, _series
from qfbench2_track_forecasting.numeric_v1 import (
    V1_CONFIG,
    NumericConfig,
    _observation_period_business_days,
    forecast_numeric,
)
from qfbench2_track_forecasting.numeric_v2 import V2_CONFIG
from qfbench2_track_forecasting.numeric_v21 import V21_CONFIG
from qfbench2_track_forecasting.tail import tail_pinball

_TAIL_LEVELS = (0.01, 0.05, 0.95, 0.99)
_WEIGHTS = {"marginal": 0.5, "joint": 0.3, "tail": 0.2}


@dataclass(frozen=True)
class UniverseCase:
    """One public target grid and its histories, with no realized private outcome."""

    unit_id: str
    family: str
    target_type: str
    target_frequency: str
    assets: list[str]
    horizons: list[int]
    histories: dict[str, pd.Series]


def load_universe(root: pathlib.Path) -> list[UniverseCase]:
    """Load every public card in stable unit-id order."""
    cases: list[UniverseCase] = []
    for card_path in sorted((root / "units").glob("*/card.toml")):
        unit = card_path.parent
        card = tomllib.loads(card_path.read_text(encoding="utf-8"))
        target = card["targets"]
        assets = [str(asset) for asset in target["asset_ids"]]
        panels = _read_panels(unit)
        histories = {
            asset: _series(panels, asset, card["provenance"]["data_cutoff"]) for asset in assets
        }
        cases.append(
            UniverseCase(
                unit_id=unit.name,
                family=str(card["metadata"]["category"]),
                target_type=str(target["target_type"]),
                target_frequency=str(target.get("target_frequency", "daily")),
                assets=assets,
                horizons=[int(horizon) for horizon in target["horizons"]],
                histories=histories,
            )
        )
    return cases


def cutoff_dates(case: UniverseCase, count: int) -> list[str]:
    """Choose evenly spaced cutoffs with enough prior state and future calendar coverage."""
    common = pd.DatetimeIndex(pd.to_datetime(pd.DataFrame(case.histories).dropna().index))
    aligned = pd.DataFrame(case.histories).dropna()
    observation_period = _observation_period_business_days(aligned)
    if observation_period <= 2:
        calendar_eligible = list(range(30, len(common) - max(case.horizons)))
    else:
        final_target = common[-1]
        calendar_eligible = [
            position
            for position in range(30, len(common))
            if common[position] + pd.offsets.BDay(max(case.horizons)) <= final_target
        ]
    if not calendar_eligible:
        raise ValueError(f"{case.unit_id} has too little history for pseudo-asof evaluation")
    last_eligible = calendar_eligible[-1]
    first = 140 if last_eligible >= 140 else max(30, last_eligible // 2)
    eligible = [position for position in calendar_eligible if position >= first]
    chosen = np.linspace(0, len(eligible) - 1, num=min(count, len(eligible)), dtype=int)
    return [str(common[eligible[int(index)]].date()) for index in sorted(set(chosen.tolist()))]


def future_observations(case: UniverseCase, cutoff: str) -> np.ndarray:
    """Read outcomes at the first available observation on or after each BD horizon."""
    aligned = pd.DataFrame(case.histories).dropna()
    dates = pd.DatetimeIndex(pd.to_datetime(aligned.index))
    origin_matches = np.flatnonzero(dates == pd.Timestamp(cutoff))
    if len(origin_matches) != 1:
        raise ValueError(f"cutoff {cutoff} is not unique in {case.unit_id}")
    origin = int(origin_matches[0])
    observation_period = _observation_period_business_days(aligned)
    observed = np.empty((len(case.assets), len(case.horizons)), dtype=float)
    for horizon_index, horizon in enumerate(case.horizons):
        if observation_period <= 2:
            target_position = origin + horizon
            target_date = dates[target_position]
        else:
            target_date = dates[origin] + pd.offsets.BDay(horizon)
            target_position = int(dates.searchsorted(target_date, side="left"))
        if target_position >= len(dates):
            raise ValueError(f"{case.unit_id} has no observation after {target_date.date()}")
        for asset_index, asset in enumerate(case.assets):
            if case.target_type == "log_return":
                observed[asset_index, horizon_index] = float(
                    aligned[asset].iloc[origin + 1 : target_position + 1].sum()
                )
            else:
                observed[asset_index, horizon_index] = float(aligned[asset].iloc[target_position])
    return observed.reshape(-1)


def _seed(unit_id: str, cutoff: str, seed_salt: str) -> int:
    digest = hashlib.sha256(f"{unit_id}|{cutoff}|{seed_salt}".encode()).digest()
    return int.from_bytes(digest[:4], "big")


def calibration_seed(unit_id: str, cutoff: str, family: str, n_draws: int, seed_salt: str) -> int:
    """Bind proxy A/B randomness to the complete public case and draw configuration."""
    return _seed(unit_id, cutoff, f"{family}|{n_draws}|{seed_salt}")


def _components(samples: np.ndarray, observed: np.ndarray) -> dict[str, float]:
    return {
        "marginal": crps_marginal(samples, observed),
        "joint": variogram_score(samples, observed) if observed.size > 1 else 0.0,
        "tail": tail_pinball(samples, observed, _TAIL_LEVELS),
    }


def summarize_paired(detail: pd.DataFrame, baseline_name: str) -> pd.DataFrame:
    """Summarize scale-free paired ratios; this is diagnostic, not the official score."""
    keys = ["unit_id", "family", "cutoff"]
    baseline = detail[detail["candidate"] == baseline_name].set_index(keys)
    rows: list[dict[str, Any]] = []
    for record in detail.to_dict(orient="records"):
        key = (record["unit_id"], record["family"], record["cutoff"])
        base = baseline.loc[[key]].iloc[0]
        weighted = 0.0
        available_weight = 0.0
        component_ratios: dict[str, float] = {}
        for component, weight in _WEIGHTS.items():
            denominator = float(base[component])
            if denominator <= 1e-12:
                continue
            ratio = float(record[component]) / denominator
            component_ratios[f"{component}_ratio"] = ratio
            weighted += weight * ratio
            available_weight += weight
        rows.append(
            {
                **{field: record[field] for field in (*keys, "candidate")},
                **component_ratios,
                "paired_composite_ratio": weighted / available_weight,
            }
        )
    paired = pd.DataFrame(rows)
    summaries: list[dict[str, Any]] = []
    for candidate, frame in paired.groupby("candidate"):
        values = frame["paired_composite_ratio"].clip(lower=1e-12)
        summaries.append(
            {
                "candidate": candidate,
                "cases": len(frame),
                "geometric_mean_ratio": float(np.exp(np.log(values).mean())),
                "median_ratio": float(values.median()),
                "win_rate": float((values < 1.0).mean()),
                "worst_decile_ratio": float(values.quantile(0.90)),
            }
        )
    return pd.DataFrame(summaries).set_index("candidate").sort_values("geometric_mean_ratio")


def run_universe_backtest(
    root: pathlib.Path,
    cutoff_count: int,
    n_draws: int,
    configs: tuple[NumericConfig, ...] = (V1_CONFIG, V2_CONFIG, V21_CONFIG),
    seed_salt: str = "",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run every public target grid and return detail plus paired diagnostics."""
    rows: list[dict[str, Any]] = []
    for case in load_universe(root):
        for cutoff in cutoff_dates(case, cutoff_count):
            histories = {
                asset: series[series.index.astype(str).str.slice(0, 10) <= cutoff]
                for asset, series in case.histories.items()
            }
            observed = future_observations(case, cutoff)
            for config in configs:
                forecast = forecast_numeric(
                    histories,
                    case.assets,
                    case.horizons,
                    case.target_type,
                    n_draws,
                    _seed(case.unit_id, cutoff, seed_salt),
                    config,
                    target_frequency=case.target_frequency,
                )
                rows.append(
                    {
                        "unit_id": case.unit_id,
                        "family": case.family,
                        "cutoff": cutoff,
                        "candidate": config.name,
                        **_components(forecast.samples.reshape(n_draws, -1), observed),
                    }
                )
    detail = pd.DataFrame(rows)
    return detail, summarize_paired(detail, V1_CONFIG.name)


def main() -> int:
    parser = argparse.ArgumentParser(description="All-card pseudo-asof numeric comparison")
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path("."))
    parser.add_argument("--cutoffs", type=int, default=3)
    parser.add_argument("--n-draws", type=int, default=300)
    parser.add_argument("--seed-salt", default="universe-v1")
    args = parser.parse_args()
    detail, summary = run_universe_backtest(
        args.root, args.cutoffs, args.n_draws, seed_salt=args.seed_salt
    )
    print(f"public cards: {detail['unit_id'].nunique()}")
    print(f"historical cases: {detail[['unit_id', 'cutoff']].drop_duplicates().shape[0]}")
    print("\nPaired V1-normalized diagnostics (lower is better):")
    print(summary.to_string(float_format=lambda value: f"{value:.6f}"))
    print("\nGeometric mean paired ratio by family:")
    paired = detail.merge(
        detail[detail["candidate"] == V1_CONFIG.name],
        on=["unit_id", "family", "cutoff"],
        suffixes=("", "_baseline"),
    )
    paired["marginal_ratio"] = paired["marginal"] / paired["marginal_baseline"]
    family = paired.groupby(["candidate", "family"])["marginal_ratio"].agg(
        lambda values: float(np.exp(np.log(values.clip(lower=1e-12)).mean()))
    )
    print(family.unstack().to_string(float_format=lambda value: f"{value:.6f}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

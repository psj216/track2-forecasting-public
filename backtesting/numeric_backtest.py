"""## Executive summary (read this first)

Run leakage-safe pseudo-asof comparisons on the public F1-F4 panels. Each case cuts a panel at an
earlier date, forecasts from data available at that cutoff, and compares the distribution with
the later public observations already present in the same panel.

The metric implementations are imported from the pinned public toolkit and Track 2 package. This
file does not copy scorer formulas, use private normalization scales, or write card answers. Raw
component totals are normalized against Numeric v1 only after all historical cases are summed.
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
    forecast_numeric,
)
from qfbench2_track_forecasting.numeric_v2 import V2_CONFIG
from qfbench2_track_forecasting.tail import tail_pinball

_TAIL_LEVELS = (0.01, 0.05, 0.95, 0.99)
_DEFAULT_UNITS = (
    "t2-F1-greater-confidence-2024",
    "t2-F2-eur-parity-2022",
    "t2-F3-brexit-joint-2016",
    "t2-F4-short-vol-2018",
)


@dataclass(frozen=True)
class HistoricalCase:
    """One public panel, target grid and family used for rolling evaluation."""

    unit_id: str
    family: str
    target_type: str
    assets: list[str]
    horizons: list[int]
    histories: dict[str, pd.Series]


def candidate_configs() -> tuple[NumericConfig, ...]:
    """One-factor perturbations around V1, so an effect can be attributed."""
    return (
        V1_CONFIG,
        NumericConfig(
            name="v2-block3",
            block_size=3,
        ),
        NumericConfig(
            name="v2-block10",
            block_size=10,
        ),
        NumericConfig(
            name="v2-recent60",
            recent_weight_base=0.60,
        ),
        NumericConfig(
            name="v2-recent80",
            recent_weight_base=0.80,
        ),
        NumericConfig(
            name="v2-widen0",
            uncertainty_fragility_scale=0.0,
        ),
        NumericConfig(
            name="v2-widen50",
            uncertainty_fragility_scale=0.50,
        ),
        NumericConfig(
            name="v2-drift10",
            drift_shrinkage=0.10,
        ),
        NumericConfig(
            name="v2-drift30",
            drift_shrinkage=0.30,
        ),
        NumericConfig(
            name="v2-fragility-slope0",
            recent_weight_fragility_slope=0.0,
        ),
        NumericConfig(
            name="v2-fragility-slope50",
            recent_weight_fragility_slope=0.50,
        ),
        NumericConfig(
            name="v2-full1260",
            full_window=1260,
        ),
        NumericConfig(
            name="v2-state25",
            state_match_share=0.25,
        ),
        NumericConfig(
            name="v2-state50",
            state_match_share=0.50,
        ),
        V2_CONFIG,
    )


def _load_case(root: pathlib.Path, unit_id: str) -> HistoricalCase:
    unit = root / "units" / unit_id
    card = tomllib.loads((unit / "card.toml").read_text(encoding="utf-8"))
    target = card["targets"]
    assets = [str(asset) for asset in target["asset_ids"]]
    histories = {
        asset: _series(_read_panels(unit / "panels"), asset, card["provenance"]["data_cutoff"])
        for asset in assets
    }
    return HistoricalCase(
        unit_id=unit_id,
        family=str(card["metadata"]["category"]),
        target_type=str(target["target_type"]),
        assets=assets,
        horizons=[int(horizon) for horizon in target["horizons"]],
        histories=histories,
    )


def _cutoff_dates(case: HistoricalCase, count: int) -> list[str]:
    common = pd.DataFrame(case.histories).dropna().index.astype(str)
    first = 504
    last = len(common) - max(case.horizons) - 1
    if last <= first:
        raise ValueError(f"{case.unit_id} has too little history for pseudo-asof evaluation")
    positions = np.linspace(first, last, num=min(count, last - first + 1), dtype=int)
    return [str(common[position])[:10] for position in sorted(set(positions.tolist()))]


def _future_observations(case: HistoricalCase, cutoff: str) -> np.ndarray:
    aligned = pd.DataFrame(case.histories).dropna()
    dates = aligned.index.astype(str).str.slice(0, 10)
    matches = np.flatnonzero(dates == cutoff)
    if len(matches) != 1:
        raise ValueError(f"cutoff {cutoff} is not unique in {case.unit_id}")
    origin = int(matches[0])
    observed = np.empty((len(case.assets), len(case.horizons)), dtype=float)
    for asset_index, asset in enumerate(case.assets):
        for horizon_index, horizon in enumerate(case.horizons):
            if case.target_type == "log_return":
                observed[asset_index, horizon_index] = float(
                    aligned[asset].iloc[origin + 1 : origin + horizon + 1].sum()
                )
            else:
                observed[asset_index, horizon_index] = float(aligned[asset].iloc[origin + horizon])
    return observed.reshape(-1)


def _seed(unit_id: str, cutoff: str, seed_salt: str) -> int:
    digest = hashlib.sha256(f"{unit_id}|{cutoff}|{seed_salt}".encode()).digest()
    return int.from_bytes(digest[:4], "big")


def _components(samples: np.ndarray, observed: np.ndarray) -> dict[str, float]:
    return {
        "marginal": crps_marginal(samples, observed),
        "joint": variogram_score(samples, observed) if observed.size > 1 else 0.0,
        "tail": tail_pinball(samples, observed, _TAIL_LEVELS),
    }


def run_backtest(
    root: pathlib.Path,
    cutoff_count: int,
    n_draws: int,
    configs: tuple[NumericConfig, ...] | None = None,
    seed_salt: str = "",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return case-level raw components and V1-normalized aggregate ratios."""
    rows: list[dict[str, Any]] = []
    cases = [_load_case(root, unit_id) for unit_id in _DEFAULT_UNITS]
    selected_configs = configs or candidate_configs()
    for case in cases:
        for cutoff in _cutoff_dates(case, cutoff_count):
            histories = {
                asset: series[series.index.astype(str).str.slice(0, 10) <= cutoff]
                for asset, series in case.histories.items()
            }
            observed = _future_observations(case, cutoff)
            for config in selected_configs:
                forecast = forecast_numeric(
                    histories,
                    case.assets,
                    case.horizons,
                    case.target_type,
                    n_draws,
                    _seed(case.unit_id, cutoff, seed_salt),
                    config,
                )
                components = _components(forecast.samples.reshape(n_draws, -1), observed)
                rows.append(
                    {
                        "unit_id": case.unit_id,
                        "family": case.family,
                        "cutoff": cutoff,
                        "candidate": config.name,
                        **components,
                    }
                )

    detail = pd.DataFrame(rows)
    totals = detail.groupby("candidate")[["marginal", "joint", "tail"]].sum()
    baseline = totals.loc[V1_CONFIG.name]
    ratios = totals.div(baseline.where(baseline > 0.0, 1.0))
    ratios["historical_composite_ratio"] = (
        0.5 * ratios["marginal"] + 0.3 * ratios["joint"] + 0.2 * ratios["tail"]
    )
    ratios = ratios.sort_values("historical_composite_ratio")
    return detail, ratios


def main() -> int:
    parser = argparse.ArgumentParser(description="Pseudo-asof comparison for Numeric v2")
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path("."))
    parser.add_argument("--cutoffs", type=int, default=12)
    parser.add_argument("--n-draws", type=int, default=300)
    args = parser.parse_args()

    detail, ratios = run_backtest(args.root, args.cutoffs, args.n_draws)
    print(f"historical cases: {detail[['unit_id', 'cutoff']].drop_duplicates().shape[0]}")
    print("\nV1-normalized aggregate ratios (lower is better):")
    print(ratios.to_string(float_format=lambda value: f"{value:.6f}"))
    print("\nFamily marginal totals by candidate:")
    print(
        detail.pivot_table(
            index="candidate", columns="family", values="marginal", aggfunc="sum"
        ).to_string(float_format=lambda value: f"{value:.6f}")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

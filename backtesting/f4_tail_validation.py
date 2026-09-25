"""Leakage-safe F4-only tail calibration against the frozen Numeric V3 baseline.

This experiment uses only public historical panel observations. It creates global chronological
fit/select/holdout splits, fits one Q10/Q90 tail pair on the oldest F4 single-cell cases, then
evaluates that frozen pair on later F4 cases. F1/F2/F3 are never modified.

The output is a diagnostic relative to our own Numeric V3. It is not an official Development
score and must not be tuned to hidden leaderboard outcomes.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from qfbench2_track_forecasting.numeric_tail import calibrate_single_cell_tails
from qfbench2_track_forecasting.numeric_v3 import forecast_numeric_v3
from qfbench2_track_forecasting.scoring import _composite

from .universe_backtest import (
    UniverseCase,
    _components,
    _observation_period_business_days,
    calibration_seed,
    cutoff_dates,
    future_observations,
    load_universe,
)

TAIL_GRID = tuple(itertools.product((0.85, 1.0, 1.15), repeat=2))
TAIL_LEVELS = (0.01, 0.05, 0.95, 0.99)
SEEDS = ("f4-tail-17", "f4-tail-43")


@dataclass
class Opportunity:
    """One pseudo-asof forecast whose full target interval is known before splitting."""

    case: UniverseCase
    cutoff: str
    end: str
    identity: str
    split: str = ""


def opportunities(root: Path, count: int) -> list[Opportunity]:
    """Deduplicate equivalent public histories and target intervals."""
    unique: dict[str, Opportunity] = {}
    for case in load_universe(root):
        aligned = pd.DataFrame(case.histories).dropna()
        dates = pd.DatetimeIndex(pd.to_datetime(aligned.index))
        period = _observation_period_business_days(aligned)
        for cutoff in cutoff_dates(case, count):
            origin = int(dates.get_loc(pd.Timestamp(cutoff)))
            if period <= 2:
                end_position = origin + max(case.horizons)
            else:
                target = pd.Timestamp(cutoff) + pd.offsets.BDay(max(case.horizons))
                end_position = int(dates.searchsorted(target, side="left"))
            prefix = aligned.iloc[: end_position + 1]
            spec = json.dumps(
                [
                    case.family,
                    case.assets,
                    case.horizons,
                    case.target_type,
                    case.target_frequency,
                    cutoff,
                ]
            )
            identity = hashlib.sha256(
                spec.encode() + pd.util.hash_pandas_object(prefix, index=True).values.tobytes()
            ).hexdigest()
            unique.setdefault(
                identity,
                Opportunity(case, cutoff, str(dates[end_position].date()), identity),
            )
    return sorted(unique.values(), key=lambda item: (item.cutoff, item.identity))


def assign_splits(items: list[Opportunity]) -> tuple[str, str]:
    """Use global chronological boundaries and purge targets crossing a boundary."""
    dates = sorted({item.cutoff for item in items})
    if len(dates) < 10:
        raise ValueError("at least ten distinct pseudo-asof dates are required")
    select_start = dates[int(0.40 * len(dates))]
    holdout_start = dates[int(0.70 * len(dates))]
    for item in items:
        if item.cutoff < select_start:
            item.split = "fit" if item.end < select_start else "purged"
        elif item.cutoff < holdout_start:
            item.split = "select" if item.end < holdout_start else "purged"
        else:
            item.split = "holdout"
    return select_start, holdout_start


def eligible(item: Opportunity) -> bool:
    """Only F4 one-asset/one-horizon cards receive the transform."""
    case = item.case
    return case.family == "T2-F4" and len(case.assets) * len(case.horizons) == 1


def evaluate(
    item: Opportunity, draws: int, seed_salt: str
) -> tuple[np.ndarray, np.ndarray, dict[str, float], int]:
    """Build the exact V3 distribution using observations available at the cutoff."""
    case = item.case
    histories = {
        asset: series[series.index.astype(str).str.slice(0, 10) <= item.cutoff]
        for asset, series in case.histories.items()
    }
    seed = calibration_seed(case.unit_id, item.cutoff, case.family, draws, seed_salt)
    base = forecast_numeric_v3(
        histories,
        case.assets,
        case.horizons,
        case.target_type,
        case.target_frequency,
        draws,
        seed,
        case.family,
    )
    observed = future_observations(case, item.cutoff)
    components = _components(base.samples.reshape(draws, -1), observed)
    return base.samples, observed, components, seed


def paired_metrics(
    samples: np.ndarray, observed: np.ndarray, base: dict[str, float]
) -> dict[str, float]:
    """Compare with V3 after using V3 components as scale-only diagnostics."""
    scales = {key: max(value, 1e-12) for key, value in base.items()}
    result = _composite(
        samples.reshape(len(samples), -1),
        observed,
        weights=(5 / 7, 0.0, 2 / 7),
        tail_levels=TAIL_LEVELS,
        joint="variogram",
        tail_metric="pinball",
        ref_scale=scales,
    )
    return {
        "ratio": float(result["composite"]),
        "marginal_ratio": float(result["marginal"] / scales["marginal"]),
        "tail_ratio": float(result["tail"] / scales["tail"]),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Average seeds within each historical opportunity before admission tests."""
    if not rows:
        return {"cases": 0, "pass": False}
    frame = pd.DataFrame(rows)
    grouped = frame.groupby(["identity", "cutoff"])[
        ["ratio", "marginal_ratio", "tail_ratio"]
    ].mean()
    ratios = grouped["ratio"].clip(lower=1e-12)
    seed_geo = {
        str(seed): float(np.exp(np.log(part["ratio"].clip(lower=1e-12)).mean()))
        for seed, part in frame.groupby("seed")
    }
    result: dict[str, Any] = {
        "cases": len(grouped),
        "distinct_dates": len(set(grouped.index.get_level_values("cutoff"))),
        "geometric_ratio": float(np.exp(np.log(ratios).mean())),
        "median_ratio": float(ratios.median()),
        "win_rate": float((ratios < 1.0).mean()),
        "worst_decile": float(ratios.quantile(0.90)),
        "marginal_ratio": float(
            np.exp(np.log(grouped["marginal_ratio"].clip(lower=1e-12)).mean())
        ),
        "tail_ratio": float(np.exp(np.log(grouped["tail_ratio"].clip(lower=1e-12)).mean())),
        "seed_geometric_ratios": seed_geo,
    }
    result["pass"] = bool(
        result["cases"] >= 20
        and result["distinct_dates"] >= 6
        and result["geometric_ratio"] < 1.0
        and result["median_ratio"] <= 1.02
        and result["worst_decile"] <= 1.10
        and result["marginal_ratio"] <= 1.02
        and result["tail_ratio"] <= 1.0
        and max(seed_geo.values()) <= 1.01
    )
    return result


def run(root: Path, out: Path, cutoffs: int, draws: int) -> dict[str, Any]:
    """Fit once, freeze the factor pair, then evaluate select and holdout once."""
    root, out = root.resolve(), out.resolve()
    if out == root or root in out.parents:
        raise ValueError("validation output must live outside the repository")
    out.mkdir(parents=True, exist_ok=False)

    items = opportunities(root, cutoffs)
    boundaries = assign_splits(items)
    protocol = {
        "protocol": "f4-tail-validation-v1",
        "baseline_commit": "31224eff97f9f06808dd52b7f2ee5457594cb387",
        "draws": draws,
        "cutoffs": cutoffs,
        "seeds": SEEDS,
        "boundaries": boundaries,
        "tail_grid": TAIL_GRID,
        "scope": "T2-F4 single-cell only",
        "leaderboard_tuning": False,
    }
    (out / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")

    fit_scores: dict[tuple[float, float], list[float]] = {pair: [] for pair in TAIL_GRID}
    fit_ids: set[str] = set()
    for item in items:
        if item.split != "fit" or not eligible(item):
            continue
        for seed_salt in SEEDS:
            base_samples, observed, base_components, _ = evaluate(item, draws, seed_salt)
            for pair in TAIL_GRID:
                candidate = calibrate_single_cell_tails(base_samples, *pair)
                fit_scores[pair].append(paired_metrics(candidate, observed, base_components)["ratio"])
        fit_ids.add(item.identity)

    if len(fit_ids) < 20:
        raise RuntimeError(f"too few F4 fit cases: {len(fit_ids)}")
    tail_pair = min(
        fit_scores,
        key=lambda pair: float(
            np.exp(np.log(np.maximum(fit_scores[pair], 1e-12)).mean())
        ),
    )
    fit_report = {
        "cases": len(fit_ids),
        "tail_pair": tail_pair,
        "grid": {
            str(pair): float(np.exp(np.log(np.maximum(values, 1e-12)).mean()))
            for pair, values in fit_scores.items()
        },
    }
    (out / "fit.json").write_text(json.dumps(fit_report, indent=2) + "\n")

    reports: dict[str, Any] = {"fit": fit_report}
    for split in ("select", "holdout"):
        rows: list[dict[str, Any]] = []
        for item in items:
            if item.split != split or not eligible(item):
                continue
            for seed_salt in SEEDS:
                base_samples, observed, base_components, _ = evaluate(item, draws, seed_salt)
                candidate = calibrate_single_cell_tails(base_samples, *tail_pair)
                metrics = paired_metrics(candidate, observed, base_components)
                rows.append(
                    {
                        "identity": item.identity,
                        "unit_id": item.case.unit_id,
                        "family": item.case.family,
                        "cutoff": item.cutoff,
                        "seed": seed_salt,
                        "lower": tail_pair[0],
                        "upper": tail_pair[1],
                        **metrics,
                    }
                )
        pd.DataFrame(rows).to_csv(out / f"{split}-ratios.csv", index=False)
        reports[split] = summarize(rows)

    reports["decision"] = (
        "CANDIDATE_FOR_NUMERIC_IMAGE"
        if tail_pair != (1.0, 1.0)
        and reports["select"]["pass"]
        and reports["holdout"]["pass"]
        else "RETAIN_V3"
    )
    (out / "summary.json").write_text(json.dumps(reports, indent=2) + "\n")
    print(json.dumps(reports, indent=2), flush=True)
    return reports


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cutoffs", type=int, default=6)
    parser.add_argument("--draws", type=int, default=1000)
    args = parser.parse_args()
    if args.cutoffs < 6 or args.draws < 1000:
        raise SystemExit("frozen protocol requires at least 6 cutoffs and 1000 draws")
    run(args.root, args.out, args.cutoffs, args.draws)


if __name__ == "__main__":
    main()

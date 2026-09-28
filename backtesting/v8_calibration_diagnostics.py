"""## Executive summary (read this first)

Replay frozen V5.1 on public, dated panel prefixes and describe its predictive
distribution. The output is a diagnostic dataset, not a fitted calibrator or an
official score. Write outcomes only to a directory outside this public repository.
Public panel histories may contain revised values, and repeated cells are dependent.
"""

from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path

import numpy as np
import pandas as pd

from backtesting.v4_ablation import assign_splits, evaluate_case, opportunities
from qfbench2_track_forecasting.text_first_v5 import apply_text_first_v5

COVERAGES = (0.50, 0.80, 0.90, 0.95, 0.98)
QUANTILES = (0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99)


def _cell(samples: np.ndarray, actual: float) -> dict[str, float | bool]:
    """Empirical midrank PIT and central interval indicators for one target cell."""
    values = np.asarray(samples, dtype=float)
    if not np.isfinite(values).all() or not np.isfinite(actual):
        raise ValueError("non-finite sample or observed value")
    quantiles = np.quantile(values, QUANTILES)
    median = float(quantiles[4])
    iqr_sd = max(float((quantiles[5] - quantiles[3]) / 1.349), 1e-10)
    pit = (
        np.count_nonzero(values < actual) + 0.5 * np.count_nonzero(values == actual)
    ) / len(values)
    result: dict[str, float | bool] = {
        "actual": float(actual),
        "pit": float(pit),
        "median": median,
        "iqr_sd": iqr_sd,
        "signed_z": float((actual - median) / iqr_sd),
        "abs_z": float(abs(actual - median) / iqr_sd),
        "median_abs_error": float(abs(actual - median)),
        "q01": float(quantiles[0]),
        "q05": float(quantiles[1]),
        "q10": float(quantiles[2]),
        "q25": float(quantiles[3]),
        "q75": float(quantiles[5]),
        "q90": float(quantiles[6]),
        "q95": float(quantiles[7]),
        "q99": float(quantiles[8]),
    }
    for coverage in COVERAGES:
        lower, upper = np.quantile(values, ((1 - coverage) / 2, (1 + coverage) / 2))
        result[f"cover_{int(coverage * 100)}"] = bool(lower <= actual <= upper)
    return result


def _horizon_bucket(days: int) -> str:
    return "short (1-5)" if days <= 5 else "medium (6-21)" if days <= 21 else "long (22+)"


def _fragility_bucket(value: float) -> str:
    return "low (<0.2)" if value < 0.2 else "mid (0.2-0.4)" if value < 0.4 else "high (>=0.4)"


def _volatility_bucket(value: float) -> str:
    return "low (<0.8)" if value < 0.8 else "mid (0.8-1.25)" if value <= 1.25 else "high (>1.25)"


def run(root: Path, out: Path, cutoffs: int, draws: int, seed_salt: str) -> dict:
    root, out = root.resolve(), out.resolve()
    if root == out or root in out.parents:
        raise ValueError("outcomes must be written outside the public repository")
    out.mkdir(parents=True, exist_ok=False)
    items = opportunities(root, cutoffs)
    boundaries = assign_splits(items)
    rows: list[dict] = []
    cases: list[dict] = []
    for index, item in enumerate(items, 1):
        if item.split == "purged":
            continue
        case = item.case
        histories, forecast, actual, seed = evaluate_case(item, draws, seed_salt)
        card = tomllib.loads((root / "units" / case.unit_id / "card.toml").read_text())
        samples, head = apply_text_first_v5(
            forecast.samples,
            histories if case.family in {"T2-F1", "T2-F4"} else {},
            case.assets,
            case.horizons,
            case.target_type,
            case.target_frequency,
            case.family,
            item.cutoff,
            seed,
            root / "units" / case.unit_id / "text",
            card["targets"].get("value_unit", ""),
            interpreter_version="v5.1",
        )
        if samples.shape != (draws, len(case.assets), len(case.horizons)):
            raise ValueError("forecast shape changed unexpectedly")
        regime = forecast.metadata["regime"]
        fragility = float(regime["fragility"])
        cases.append({"identity": item.identity, "cutoff": item.cutoff, "family": case.family,
                      "split": item.split, "text_active": bool(head["applied"])})
        for asset_index, asset in enumerate(case.assets):
            vol_ratio = float(regime["vol_ratio_20_long"][asset])
            for horizon_index, horizon in enumerate(case.horizons):
                offset = asset_index * len(case.horizons) + horizon_index
                cell = _cell(samples[:, asset_index, horizon_index], float(actual[offset]))
                rows.append({
                    "identity": item.identity, "cutoff": item.cutoff, "end": item.end,
                    "split": item.split, "family": case.family, "single_cell": len(actual) == 1,
                    "asset": asset, "target_type": case.target_type,
                    "frequency": case.target_frequency,
                    "horizon": horizon, "horizon_bucket": _horizon_bucket(horizon),
                    "fragility": fragility, "fragility_bucket": _fragility_bucket(fragility),
                    "vol_ratio": vol_ratio, "volatility_bucket": _volatility_bucket(vol_ratio),
                    "momentum_z": float(regime["momentum_20_z"][asset]),
                    "history_rows": int(forecast.metadata["n_history_rows"]),
                    "text_active": bool(head["applied"]), **cell,
                })
        if index % 50 == 0:
            print(f"V5.1 replay: {index}/{len(items)} historical cases", flush=True)
    frame = pd.DataFrame(rows)
    case_frame = pd.DataFrame(cases)
    frame.to_parquet(out / "diagnostic_cells.parquet", index=False)
    case_frame.to_parquet(out / "diagnostic_cases.parquet", index=False)
    manifest = {
        "baseline": "frozen V5.1 (Numeric V3 + v5.1 text interpreter; no tail transform)",
        "source_commit": "3c9b870", "cutoffs_per_card": cutoffs, "draws": draws,
        "seed_salt": seed_salt, "boundaries": boundaries, "opportunities": len(items),
        "purged": sum(item.split == "purged" for item in items),
        "cases": len(case_frame), "cells": len(frame),
        "active_text_cases": int(case_frame.text_active.sum()),
        "splits": case_frame.split.value_counts().to_dict(),
        "limits": ["Repeated public-history diagnostic, not a fresh holdout or private score.",
                   "Public panels may contain revisions; true historical vintages are unavailable.",
                   "Overlapping horizons and repeated cutoff dates cause dependence.",
                   "Text at historical cutoffs is often absent; numeric behavior dominates."],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cutoffs", type=int, default=8)
    parser.add_argument("--draws", type=int, default=500)
    parser.add_argument("--seed-salt", default="v8-diagnostic-locked-01")
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.out, args.cutoffs, args.draws, args.seed_salt), indent=2))


if __name__ == "__main__":
    main()

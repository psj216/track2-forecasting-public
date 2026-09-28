"""## Executive summary (read this first)

Replay frozen V5.1 and one preselected single-cell tail transform on dated public
panel prefixes. This is a repeated public diagnostic, not a fresh or official holdout.
Write every result outside the repository; never publish realized card outcomes.
"""

from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path

import numpy as np
import pandas as pd

from backtesting.universe_backtest import _components
from backtesting.v4_ablation import (
    assign_splits,
    evaluate_case,
    opportunities,
    paired_metrics,
)
from qfbench2_track_forecasting.numeric_v4 import calibrate_single_cell_tails
from qfbench2_track_forecasting.text_first_v5 import apply_text_first_v5


def metrics(records: list[dict]) -> dict:
    if not records:
        return {"cases": 0}
    frame = pd.DataFrame(records)
    # Random seeds are repeated measurements of one forecast case.
    case = frame.groupby(["identity", "cutoff", "family"], as_index=False).ratio.mean()
    ratios = case.ratio.clip(lower=1e-12)
    return {
        "cases": len(case),
        "dates": case.cutoff.nunique(),
        "geometric_ratio": float(np.exp(np.log(ratios).mean())),
        "q90": float(ratios.quantile(0.9)),
        "win_rate": float((ratios < 1).mean()),
        "by_family": {
            family: float(np.exp(np.log(part.ratio.clip(lower=1e-12)).mean()))
            for family, part in case.groupby("family")
        },
        "by_seed": {
            seed: float(np.exp(np.log(part.ratio.clip(lower=1e-12)).mean()))
            for seed, part in frame.groupby("seed")
        },
    }


def run(root: Path, draws: int, seeds: tuple[str, ...], cutoffs: int) -> dict:
    items = opportunities(root, cutoffs)
    boundaries = assign_splits(items)
    holdout = [item for item in items if item.split == "holdout"]
    rows = []
    text_active = 0
    single_cases = 0
    for index, item in enumerate(holdout, 1):
        case = item.case
        eligible = case.family != "T2-F3" and len(case.assets) * len(case.horizons) == 1
        if eligible:
            single_cases += 1
        card = tomllib.loads((root / "units" / case.unit_id / "card.toml").read_text())
        for salt in seeds:
            histories, forecast, y, seed = evaluate_case(item, draws, salt)
            base, head = apply_text_first_v5(
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
            text_active += int(head["applied"])
            if not eligible:
                continue  # Exact V5.1 preservation is checked by the CLI parity test.
            candidate = calibrate_single_cell_tails(base, 0.85, 0.85)
            scales = _components(base.reshape(draws, -1), y)
            paired = paired_metrics(candidate, y, scales)
            rows.append(
                {
                    "identity": item.identity,
                    "cutoff": item.cutoff,
                    "family": case.family,
                    "seed": salt,
                    "ratio": paired["ratio"],
                }
            )
        if index % 30 == 0:
            print(f"{draws} draws: {index}/{len(holdout)} holdout cases", flush=True)
    single = metrics(rows)
    unchanged = len(holdout) - single_cases
    non_f3 = sum(item.case.family != "T2-F3" for item in holdout)
    return {
        "draws": draws,
        "seeds": seeds,
        "split_boundaries": boundaries,
        "holdout_cases": len(holdout),
        "single_cell_cases": single_cases,
        "unchanged_cases": unchanged,
        "text_active_replays": text_active,
        "tail_factors": [0.85, 0.85],
        "single_cell": single,
        "all_excluding_f3_ratio": float(
            np.exp(np.log(single["geometric_ratio"]) * single_cases / max(1, non_f3))
        ),
        "qualification": (
            "Previously inspected public cutoffs; not independent validation "
            "or a leaderboard estimate."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cutoffs", type=int, default=6)
    parser.add_argument("--draws", type=int, default=500)
    parser.add_argument(
        "--seeds", nargs="+", default=["tail-seed-17", "tail-seed-43", "tail-seed-71"]
    )
    args = parser.parse_args()
    report = run(args.root.resolve(), args.draws, tuple(args.seeds), args.cutoffs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "qualification"}, indent=2))


if __name__ == "__main__":
    main()

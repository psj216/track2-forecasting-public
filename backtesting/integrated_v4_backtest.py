"""## Executive summary (read this first)

Compare predeclared integrated V4 candidates with paired Numeric V3 draws on
chronological rolling pseudo-as-of folds. Purge labels across boundaries, count
seeds as repetitions rather than new cases, and refuse the newer folds unless
older folds clear the submission-scale improvement gate. Public histories have
been examined before; this cannot create a globally untouched holdout.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from qfbench2_track_forecasting.integrated_v4 import CONFIGS, apply_integrated_v4

from .universe_backtest import _components
from .v4_ablation import evaluate_case, opportunities, paired_metrics

SEEDS = ("integrated-v4-17", "integrated-v4-43", "integrated-v4-71")


def folds(items: list) -> tuple[list, list[str]]:
    dates = sorted({item.cutoff for item in items})
    if len(dates) < 20:
        raise ValueError("too few distinct public dates")
    boundaries = [dates[int(len(dates) * fraction)] for fraction in (0.25, 0.5, 0.75)]
    kept = []
    for item in items:
        fold = sum(item.cutoff >= boundary for boundary in boundaries)
        if fold < 3 and item.end >= boundaries[fold]:
            continue
        kept.append((item, fold))
    return kept, boundaries


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return {"cases": 0, "gate": False}
    grouped = frame.groupby(["identity", "cutoff", "family", "fold"], as_index=False).agg(
        ratio=("ratio", "mean"),
        changed=("changed", "max"),
        vol_state=("vol_state", "first"),
    )
    ratio = grouped.ratio.clip(lower=1e-12)
    by_family = {
        family: float(np.exp(np.log(part.ratio.clip(lower=1e-12)).mean()))
        for family, part in grouped.groupby("family")
    }
    by_fold = {
        str(fold): float(np.exp(np.log(part.ratio.clip(lower=1e-12)).mean()))
        for fold, part in grouped.groupby("fold")
    }
    by_state = {
        state: {
            "cases": len(part),
            "ratio": float(np.exp(np.log(part.ratio.clip(lower=1e-12)).mean())),
        }
        for state, part in grouped.groupby("vol_state")
    }
    by_seed = {
        seed: float(np.exp(np.log(part.ratio.clip(lower=1e-12)).mean()))
        for seed, part in frame.groupby("seed")
    }
    result = {
        "cases": len(grouped),
        "dates": grouped.cutoff.nunique(),
        "geometric_ratio": float(np.exp(np.log(ratio).mean())),
        "win_rate": float((ratio < 1).mean()),
        "worst_decile": float(ratio.quantile(0.9)),
        "family_ratios": by_family,
        "fold_ratios": by_fold,
        "state_ratios": by_state,
        "seed_ratios": by_seed,
        "changed_cases": int(grouped.changed.sum()),
        "changed_families": {
            family: int(part.changed.sum()) for family, part in grouped.groupby("family")
        },
    }
    active_states = [state for state in ("normal", "stress") if state in by_state]
    result["gate"] = bool(
        result["cases"] >= 60
        and result["dates"] >= 20
        and result["geometric_ratio"] <= 0.97
        and result["worst_decile"] <= 1.05
        and all(value <= 1.005 for value in by_family.values())
        and all(value < 1 for value in by_fold.values())
        and all(value < 1 for value in by_seed.values())
        and all(by_state[state]["ratio"] <= 1.005 for state in active_states)
        and len(active_states) == 2
        and all(by_state[state]["cases"] >= 10 for state in active_states)
        and all(
            result["changed_families"].get(family, 0) >= 10
            for family in ("T2-F1", "T2-F2", "T2-F4")
        )
    )
    return result


def evaluate(items: list, configs: tuple, draws: int, seeds: tuple[str, ...]) -> dict[str, Any]:
    rows = {config.name: [] for config in configs}
    for i, (item, fold) in enumerate(items):
        for salt in seeds:
            histories, baseline, observed, seed = evaluate_case(item, draws, salt)
            scales = _components(baseline.samples.reshape(draws, -1), observed)
            text_dir = Path("units") / item.case.unit_id / "text"
            for config in configs:
                candidate, meta = apply_integrated_v4(
                    baseline.samples,
                    histories,
                    item.case.assets,
                    item.case.horizons,
                    item.case.target_type,
                    item.case.target_frequency,
                    item.case.family,
                    item.cutoff,
                    seed,
                    config,
                    text_dir,
                )
                ratio = paired_metrics(candidate, observed, scales)["ratio"]
                vol = meta.get("vol_ratio", 1.0)
                rows[config.name].append(
                    {
                        "identity": item.identity,
                        "cutoff": item.cutoff,
                        "family": item.case.family,
                        "fold": fold,
                        "seed": salt,
                        "ratio": ratio,
                        "changed": not np.array_equal(candidate, baseline.samples),
                        "vol_state": "stress" if vol >= 1.4 else "normal",
                    }
                )
        if (i + 1) % 40 == 0:
            print("cases", i + 1, "/", len(items), flush=True)
    return {key: summarize(value) for key, value in rows.items()}


def run(root: Path, out: Path, cutoffs: int = 6) -> dict[str, Any]:
    root, out = root.resolve(), out.resolve()
    if out == root or root in out.parents:
        raise ValueError("outcomes must be outside public repository")
    out.mkdir(parents=True, exist_ok=False)
    all_items = [
        item
        for item in opportunities(root, cutoffs)
        if item.case.family in {"T2-F1", "T2-F2", "T2-F4"}
    ]
    grouped, boundaries = folds(all_items)
    (out / "protocol.json").write_text(
        json.dumps(
            {
                "name": "integrated-v4-rolling-v1",
                "cutoffs": cutoffs,
                "boundaries": boundaries,
                "seeds": SEEDS,
                "candidates": [asdict(c) for c in CONFIGS],
                "counts": {str(fold): sum(f == fold for _, f in grouped) for fold in range(4)},
                "prior_exposure": (
                    "public histories examined previously; no genuinely untouched holdout"
                ),
            },
            indent=2,
        )
        + "\n"
    )
    older = [(item, fold) for item, fold in grouped if fold < 2]
    select = evaluate(older, CONFIGS, 500, SEEDS[:1])
    (out / "selection.json").write_text(json.dumps(select, indent=2) + "\n")
    accepted = [c for c in CONFIGS if select[c.name]["gate"]]
    if not accepted:
        result = {
            "decision": "RETAIN_V3",
            "reason": "selection_gate_failed",
            "holdout_evaluated": False,
            "selection": select,
        }
    else:
        winner = min(accepted, key=lambda c: select[c.name]["geometric_ratio"])
        newer = [(item, fold) for item, fold in grouped if fold >= 2]
        results: dict[str, Any] = {}
        for draws in (500, 1000):
            results[str(draws)] = evaluate(newer, (winner,), draws, SEEDS)[winner.name]
            if not results[str(draws)]["gate"]:
                break
        result = {
            "decision": "RETAIN_V3",
            "frozen": asdict(winner),
            "holdout_evaluated": True,
            "results": results,
            "fully_untouched": False,
        }
    (out / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cutoffs", type=int, default=6)
    args = parser.parse_args()
    if args.cutoffs < 6:
        parser.error("at least six origins required")
    run(args.root, args.out, args.cutoffs)


if __name__ == "__main__":
    main()

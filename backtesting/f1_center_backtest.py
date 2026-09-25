"""## Executive summary (read this first)

Fit an F1-only standardized center bias from older public panel origins. Select
shrinkage on a purged middle period; evaluate one frozen model on the newest
period with paired Numeric V3 worlds. Outcomes stay outside the public repo.
Previously explored public histories do not qualify as a completely new holdout.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from qfbench2_track_forecasting.f1_center import (
    CenterBias,
    apply_center_bias,
    frequency_group,
    horizon_group,
)

from .universe_backtest import _components
from .v4_ablation import assign_splits, evaluate_case, opportunities, paired_metrics, summary

GRID = ((0.1, 0.1), (0.25, 0.1), (0.25, 0.2), (0.4, 0.1), (0.4, 0.2))
SEEDS = ("f1-center-17", "f1-center-43", "f1-center-71")


def residuals(items, draws: int, salt: str) -> list[dict]:
    """Each asset/horizon residual is expressed in its own V3 forecast spread."""
    rows = []
    for item in items:
        _, base, observed, _ = evaluate_case(item, draws, salt)
        for ai in range(len(item.case.assets)):
            for hi, horizon in enumerate(item.case.horizons):
                spread = max(float(base.samples[:, ai, hi].std()), 1e-9)
                rows.append(
                    dict(
                        key=f"{frequency_group(item.case.target_frequency)}:{horizon_group(horizon)}",
                        standardized_error=float(
                            (
                                observed.reshape(len(item.case.assets), -1)[ai, hi]
                                - np.median(base.samples[:, ai, hi])
                            )
                            / spread
                        ),
                        date=item.end,
                    )
                )
    return rows


def fit(items, draws: int = 500) -> tuple[dict[str, float], str]:
    rows = residuals(items, draws, SEEDS[0])
    table = pd.DataFrame(rows)
    biases = {}
    for key, part in table.groupby("key"):
        if len(part) < 10:
            continue
        clipped = np.clip(part.standardized_error.to_numpy(), -1.0, 1.0)
        biases[key] = float(np.mean(clipped) * len(clipped) / (len(clipped) + 20.0))
    return biases, max(row["date"] for row in rows)


def assess(items, model: CenterBias, draws: int, seeds: tuple[str, ...]) -> dict:
    rows = []
    for item in items:
        for salt in seeds:
            _, base, observed, _ = evaluate_case(item, draws, salt)
            scales = _components(base.samples.reshape(draws, -1), observed)
            adjusted = apply_center_bias(
                base.samples,
                item.case.horizons,
                item.case.target_frequency,
                item.case.target_type,
                item.case.family,
                item.cutoff,
                model,
            )
            rows.append(
                dict(
                    identity=item.identity,
                    cutoff=item.cutoff,
                    family=item.case.family,
                    seed=salt,
                    **paired_metrics(adjusted, observed, scales),
                )
            )
    result = summary(rows)
    result["shifted_cases"] = len({r["identity"] for r in rows if abs(r["ratio"] - 1) > 1e-12})
    result["strict_gate"] = bool(
        result["cases"] >= 30
        and result["distinct_dates"] >= 10
        and result["shifted_cases"] >= 30
        and result["geometric_ratio"] < 0.98
        and result["win_rate"] >= 0.65
        and result["worst_decile"] <= 1.05
        and all(value < 1 for value in result["seed_geometric_ratios"])
    )
    return result


def run(root: Path, out: Path, cutoffs: int = 12) -> dict:
    root, out = root.resolve(), out.resolve()
    if out == root or root in out.parents:
        raise ValueError("public historical outcomes must remain outside the repository")
    out.mkdir(parents=True, exist_ok=False)
    all_items = opportunities(root, cutoffs)
    boundaries = assign_splits(all_items)
    selected = [item for item in all_items if item.case.family == "T2-F1"]
    splits = {
        s: [item for item in selected if item.split == s] for s in ("fit", "select", "holdout")
    }
    if min(map(len, splits.values())) < 30:
        raise ValueError("too few independent F1 cases in one split")
    protocol = {
        "baseline": "Numeric V3",
        "selection_grid": GRID,
        "boundaries": boundaries,
        "seeds": SEEDS,
        "cutoffs_per_card": cutoffs,
        "split_counts": {key: len(value) for key, value in splits.items()},
        "prior_exposure": (
            "Public histories were inspected in prior experiments; "
            "this is NOT a fully untouched holdout."
        ),
    }
    (out / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    bias, end = fit(splits["fit"])
    candidates = []
    for strength, cap in GRID:
        model = CenterBias(end, strength, cap, bias)
        metrics = assess(splits["select"], model, 500, SEEDS[:1])
        candidates.append((model, metrics))
        print("select", strength, cap, metrics["geometric_ratio"], flush=True)
    winner, selection = min(candidates, key=lambda pair: pair[1]["geometric_ratio"])
    (out / "select.json").write_text(
        json.dumps([{"model": asdict(m), "metrics": r} for m, r in candidates], indent=2) + "\n"
    )
    if not selection["strict_gate"]:
        results = {
            "selection": selection,
            "selected_parameters": {"strength": winner.strength, "cap": winner.cap},
            "decision": "RETAIN_V3",
            "reason": "older selection period did not meet the strict F1 gain gate",
            "holdout_evaluated": False,
            "full_holdout_gate": False,
            "prior_exposure": protocol["prior_exposure"],
        }
        (out / "summary.json").write_text(json.dumps(results, indent=2) + "\n")
        return results
    # The grid is frozen after selection; only earlier labels are added to the bias estimate.
    bias, end = fit(splits["fit"] + splits["select"])
    frozen = CenterBias(end, winner.strength, winner.cap, bias)
    (out / "frozen.json").write_text(json.dumps(asdict(frozen), indent=2) + "\n")
    print("frozen", asdict(frozen), flush=True)
    results = {
        "selection": selection,
        "frozen": asdict(frozen),
        "prior_exposure": protocol["prior_exposure"],
    }
    # Predeclared order: 500, then 1000; every seed must improve at each count.
    for draws in (500, 1000):
        results[str(draws)] = assess(splits["holdout"], frozen, draws, SEEDS)
        print("holdout", draws, results[str(draws)], flush=True)
        if not results[str(draws)]["strict_gate"]:
            break
    results["decision"] = "RETAIN_V3"
    results["full_holdout_gate"] = False  # Reused public evidence cannot satisfy this requirement.
    (out / "summary.json").write_text(json.dumps(results, indent=2) + "\n")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cutoffs", type=int, default=12)
    args = parser.parse_args()
    if args.cutoffs < 12:
        parser.error("at least twelve origins per card required")
    run(args.root, args.out, args.cutoffs)


if __name__ == "__main__":
    main()

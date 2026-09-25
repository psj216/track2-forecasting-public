"""## Executive summary (read this first)

Fit a declared F1 calibration grid on older public histories, freeze each choice,
and evaluate two expanding chronological date-purged folds. All metrics use the imported official
scorer. The previously examined public histories are not a new unseen holdout.
Write all outcomes outside the public repository. No leaderboard forecast follows.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import pandas as pd

from qfbench2_track_forecasting.family_calibration import (
    FamilyCalibration,
    apply_family_calibration,
    candidate_grid,
)

from .universe_backtest import _components
from .v4_ablation import assign_splits, evaluate_case, opportunities, paired_metrics, summary


def choose_from_training(rows: list[dict[str, Any]]) -> str:
    """Select only among configurations passing predeclared training safety gates."""
    reports = {
        name: summary([r for r in rows if r["candidate"] == name])
        for name in sorted({r["candidate"] for r in rows})
    }
    admitted = [name for name, report in reports.items() if report["pass"]]
    return (
        min(admitted, key=lambda name: reports[name]["geometric_ratio"]) if admitted else "identity"
    )


def run(root: Path, out: Path, draws: int = 1000, cutoffs: int = 6) -> dict[str, Any]:
    root, out = root.resolve(), out.resolve()
    if out == root or root in out.parents:
        raise ValueError("outcomes must remain outside the public repository")
    out.mkdir(parents=True, exist_ok=False)
    items = opportunities(root, cutoffs)
    boundaries = assign_splits(items)
    items = [item for item in items if item.case.family == "T2-F1"]
    grid = candidate_grid()
    seeds = ("family-calibration-17", "family-calibration-43")
    protocol = {
        "name": "f1-calibration-1",
        "draws": draws,
        "seeds": seeds,
        "boundaries": boundaries,
        "candidates": [asdict(c) for c in grid],
        "selection": "expanding walk-forward: fit -> select; fit+select -> holdout",
        "minimum_fit_cases": 30,
        "limitations": (
            "reused public panel history; possible revised vintages; "
            "not official M0 normalization"
        ),
        "cases": [
            dict(identity=x.identity, cutoff=x.cutoff, end=x.end, split=x.split) for x in items
        ],
    }
    (out / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    reports: dict[str, Any] = {}
    chosen = FamilyCalibration()
    training_rows: list[dict[str, Any]] = []
    fold_reports: dict[str, Any] = {}
    for split in ("fit", "select", "holdout"):
        rows: list[dict[str, Any]] = []
        configs = grid if split in {"fit", "select"} else (chosen,)
        eligible = [item for item in items if item.split == split]
        for index, item in enumerate(eligible):
            for salt in seeds:
                histories, base, y, _ = evaluate_case(item, draws, salt)
                scales = _components(base.samples.reshape(draws, -1), y)
                for config in configs:
                    samples = apply_family_calibration(
                        base.samples,
                        histories,
                        item.case.assets,
                        item.case.horizons,
                        item.case.target_type,
                        item.case.family,
                        item.cutoff,
                        config,
                    )
                    rows.append(
                        dict(
                            identity=item.identity,
                            cutoff=item.cutoff,
                            family=item.case.family,
                            seed=salt,
                            candidate=config.name,
                            **paired_metrics(samples, y, scales),
                        )
                    )
            if (index + 1) % 20 == 0:
                print(split, index + 1, "/", len(eligible), flush=True)
        reports[split] = {
            config.name: summary([r for r in rows if r["candidate"] == config.name])
            for config in configs
        }
        pd.DataFrame(rows).to_csv(out / f"{split}-ratios.csv", index=False)
        if split != "fit":
            fold_reports[split] = {"config": asdict(chosen), "metrics": reports[split][chosen.name]}
        if split in {"fit", "select"}:
            training_rows.extend(rows)
            reports[f"training_after_{split}"] = {
                config.name: summary([r for r in training_rows if r["candidate"] == config.name])
                for config in grid
            }
            name = choose_from_training(training_rows)
            chosen = replace(
                next(c for c in grid if c.name == name),
                trained_through=max(
                    item.end
                    for item in items
                    if item.split in ({"fit"} if split == "fit" else {"fit", "select"})
                ),
            )
            (out / f"frozen-after-{split}.json").write_text(
                json.dumps(asdict(chosen), indent=2) + "\n"
            )
            print("Frozen", asdict(chosen), flush=True)
    accepted = chosen.name != "identity" and all(
        fold_reports[split]["metrics"]["pass"] for split in ("select", "holdout")
    )
    reports.update(
        walk_forward=fold_reports,
        selected=asdict(chosen),
        decision="CANDIDATE_FOR_OFFICIAL_AB" if accepted else "RETAIN_V3",
        leaderboard_prediction=None,
    )
    (out / "summary.json").write_text(json.dumps(reports, indent=2) + "\n")
    print(json.dumps(reports, indent=2), flush=True)
    return reports


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--draws", type=int, default=1000)
    parser.add_argument("--cutoffs", type=int, default=6)
    args = parser.parse_args()
    if args.draws < 1000 or args.cutoffs < 6:
        parser.error("use at least 1000 draws and six cutoffs")
    run(args.root, args.out, args.draws, args.cutoffs)


if __name__ == "__main__":
    main()

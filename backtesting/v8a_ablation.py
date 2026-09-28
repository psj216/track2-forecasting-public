"""## Executive summary (read this first)

Fit only two family-level affine V8-A maps on old pseudo-asof V5.1 cases.
Freeze the result before chronological select/later evaluation at 500, 1000,
and 2000 draws with three seeds. The loss imports the canonical scorer through
the existing paired proxy; private reference scales are unavailable. Nothing
here changes the submission model. Outputs with outcomes stay outside the repo.
"""

from __future__ import annotations

import argparse
import json
import tomllib
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from backtesting.universe_backtest import _components
from backtesting.v4_ablation import assign_splits, evaluate_case, opportunities, paired_metrics
from qfbench2_track_forecasting.calibration_v8 import V8AConfig, transform_v8a
from qfbench2_track_forecasting.text_first_v5 import apply_text_first_v5

BIAS_GRID = (-0.05, 0.0, 0.05)
SCALE_GRID = (0.95, 1.0, 1.05, 1.10)
FAMILIES = ("T2-F1", "T2-F2")
SEEDS = ("v8a-seed-17", "v8a-seed-43", "v8a-seed-71")
DRAWS = (500, 1000, 2000)


def _replay(item, root: Path, draws: int, salt: str):
    case = item.case
    histories, forecast, actual, seed = evaluate_case(item, draws, salt)
    card = tomllib.loads((root / "units" / case.unit_id / "card.toml").read_text())
    samples, text_meta = apply_text_first_v5(
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
        raise ValueError("V5.1 sample shape differs from the declared target")
    return samples, actual, bool(text_meta["applied"])


def _ratio(samples: np.ndarray, actual: np.ndarray, baseline_scales: dict[str, float]) -> float:
    return float(paired_metrics(samples, actual, baseline_scales)["ratio"])


def _summary(records: list[dict]) -> dict:
    if not records:
        return {"cases": 0}
    frame = pd.DataFrame(records)
    ratios = frame.ratio.clip(lower=1e-12)
    return {
        "cases": len(frame),
        "distinct_dates": frame.cutoff.nunique(),
        "geometric_ratio": float(np.exp(np.log(ratios).mean())),
        "arithmetic_ratio": float(ratios.mean()),
        "median_ratio": float(ratios.median()),
        "win_rate": float((ratios < 1).mean()),
        "q90_ratio": float(ratios.quantile(0.90)),
        "by_family": {
            name: float(np.exp(np.log(part.ratio.clip(lower=1e-12)).mean()))
            for name, part in frame.groupby("family")
        },
    }


def _fit(items, root: Path) -> tuple[V8AConfig, dict]:
    """Use the first seed and 500 draws in fit only; do not inspect later labels."""
    grid = [(b, a) for b in BIAS_GRID for a in SCALE_GRID]
    results: dict[str, dict[tuple[float, float], list[float]]] = {
        family: {candidate: [] for candidate in grid} for family in FAMILIES
    }
    counts = {family: 0 for family in FAMILIES}
    for index, item in enumerate(items, 1):
        family = item.case.family
        if item.split != "fit" or family not in FAMILIES:
            continue
        base, y, _ = _replay(item, root, 500, SEEDS[0])
        scales = _components(base.reshape(len(base), -1), y)
        counts[family] += 1
        for b, a in grid:
            config = (V8AConfig(f1_bias=b, f1_scale=a) if family == "T2-F1"
                      else V8AConfig(f2_bias=b, f2_scale=a))
            candidate = transform_v8a(base, family, config)
            results[family][(b, a)].append(_ratio(candidate, y, scales))
        if index % 100 == 0:
            print(f"fit progress: {index}/{len(items)}", flush=True)
    # The objective is arithmetic mean of paired canonical composite ratios,
    # with exact identity preferred in a numerical tie; no coverage targeting.
    choices = {}
    fit_result = {}
    for family in FAMILIES:
        if counts[family] < 30:
            raise ValueError(f"too few independent cases for {family}")
        ranked = sorted(grid, key=lambda pair: (
            float(np.mean(results[family][pair])),
            abs(pair[0]) + abs(pair[1] - 1.0),
        ))
        choices[family] = ranked[0]
        fit_result[family] = {
            "cases": counts[family],
            "selected": {"bias": ranked[0][0], "scale": ranked[0][1]},
            "selected_arithmetic_ratio": float(np.mean(results[family][ranked[0]])),
            "identity_arithmetic_ratio": float(np.mean(results[family][(0.0, 1.0)])),
            "grid": [
                {"bias": b, "scale": a, "arithmetic_ratio": float(np.mean(results[family][b, a]))}
                for b, a in grid
            ],
        }
    f1b, f1a = choices["T2-F1"]
    f2b, f2a = choices["T2-F2"]
    return V8AConfig(f1b, f1a, f2b, f2a), fit_result


def _evaluate(items, root: Path, config: V8AConfig) -> dict:
    outcomes = {}
    for draws in DRAWS:
        for salt in SEEDS:
            records = []
            active_text = 0
            for index, item in enumerate(items, 1):
                if item.split not in {"select", "holdout"}:
                    continue
                family = item.case.family
                # F3/F4 are exact reference for the entire experiment. One seed
                # checks actual arrays; their ratios are 1 on the other replays.
                if family not in FAMILIES and (draws, salt) != (500, SEEDS[0]):
                    records.append({"split": item.split, "family": family,
                                    "identity": item.identity, "cutoff": item.cutoff, "ratio": 1.0})
                    continue
                base, y, active = _replay(item, root, draws, salt)
                active_text += int(active)
                candidate = transform_v8a(base, family, config)
                if family not in FAMILIES:
                    if candidate is not base or candidate.tobytes() != base.tobytes():
                        raise AssertionError(f"frozen {family} changed samples")
                    ratio = 1.0
                else:
                    scales = _components(base.reshape(len(base), -1), y)
                    ratio = _ratio(candidate, y, scales)
                records.append({"split": item.split, "family": family,
                                "identity": item.identity, "cutoff": item.cutoff, "ratio": ratio})
                if index % 100 == 0:
                    print(f"validation {draws}/{salt}: {index}/{len(items)}", flush=True)
            outcome = {
                split: {"all": _summary([r for r in records if r["split"] == split]),
                        "active": _summary([r for r in records
                                            if r["split"] == split and r["family"] in FAMILIES])}
                for split in ("select", "holdout")
            }
            outcome["text_active_replays"] = active_text
            outcomes[f"{draws}:{salt}"] = outcome
            print(f"done {draws}/{salt}: " + json.dumps({
                split: outcome[split]["all"]["geometric_ratio"]
                for split in ("select", "holdout")
            }), flush=True)
    return outcomes


def _gate(outcomes: dict) -> dict:
    all_rows = []
    for key, outcome in outcomes.items():
        split_ratios = [outcome[s]["all"]["geometric_ratio"]
                        for s in ("select", "holdout")]
        family_ratios = [outcome[s]["all"]["by_family"][family]
                         for s in ("select", "holdout") for family in FAMILIES]
        case_counts = [outcome[s]["all"]["cases"] for s in ("select", "holdout")]
        # Both independent chronological blocks and both affected families
        # must improve for each seed/draw configuration.
        all_rows.append({"configuration": key,
                         "combined_ratio": float(np.exp(np.average(
                             np.log(split_ratios), weights=case_counts))),
                         "split_ratios": split_ratios, "family_ratios": family_ratios})
    worst_combined = max(row["combined_ratio"] for row in all_rows)
    return {"pass": bool(worst_combined <= 0.97 and all(
        max(row["split_ratios"]) < 1 and max(row["family_ratios"]) <= 1
        for row in all_rows)),
        "worst_combined_ratio": worst_combined, "details": all_rows,
        "requires_exact_f3_f4": True,
        "threshold": "combined <=0.97; select/later <1; F1/F2 <=1; every seed and draw count",
    }


def run(root: Path, out: Path, cutoffs: int = 8) -> dict:
    root, out = root.resolve(), out.resolve()
    if out == root or root in out.parents:
        raise ValueError("write diagnostics outside the public repository")
    out.mkdir(parents=True, exist_ok=False)
    items = opportunities(root, cutoffs)
    boundaries = assign_splits(items)
    config, fit = _fit(items, root)
    # Persist only after fit, before any validation outcomes are generated.
    (out / "frozen_fit.json").write_text(json.dumps({"config": asdict(config),
        "fit": fit, "fit_draws": 500, "fit_seed": SEEDS[0], "boundaries": boundaries,
        "grid": {"bias": BIAS_GRID, "scale": SCALE_GRID}}, indent=2) + "\n")
    outcomes = _evaluate(items, root, config)
    gate = _gate(outcomes)
    result = {"protocol": "v8-a-predeclared-1", "baseline": "frozen V5.1", "config": asdict(config),
              "fit": fit, "validation": outcomes, "gate": gate,
              "limitations": ["Public pseudo-asof, previously inspected; no independent holdout.",
                              "Private official scales unavailable; use paired proxy.",
                              "F3/F4 unchanged; overlapping events/horizons remain dependent."]}
    (out / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cutoffs", type=int, default=8)
    args = parser.parse_args()
    result = run(args.root, args.out, args.cutoffs)
    print(json.dumps({"config": result["config"], "gate": result["gate"]}, indent=2))


if __name__ == "__main__":
    main()

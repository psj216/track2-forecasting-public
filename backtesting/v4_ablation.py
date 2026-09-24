"""## Executive summary (read this first)

Freeze a date-purged fit/selection/holdout experiment before evaluating Numeric V4.
Only public pre-card panel observations are used. Exact duplicate target histories
are removed. Tail parameters are fitted on the oldest split, candidate choices on
the middle split, and one frozen choice is judged on the newest split. No official
Development outcomes or private reference scales enter this program.

Outputs MUST live outside the public repository. Ratios compare with OUR Numeric
V3, not the organizer baseline, and cannot be multiplied by a leaderboard score.
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

from qfbench2_track_forecasting.numeric_v1 import NumericForecast
from qfbench2_track_forecasting.numeric_v3 import forecast_numeric_v3
from qfbench2_track_forecasting.numeric_v4 import (
    V4_A,
    V4_AB,
    V4_B,
    calibrate_single_cell_tails,
    forecast_numeric_v4,
    mixture_draws,
)
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

BASE = "numeric-v3"
TAIL_GRID = tuple(itertools.product((0.85, 1.0, 1.15), repeat=2))
LEVELS = (0.01, 0.05, 0.95, 0.99)


@dataclass
class Opportunity:
    """A historical forecast with its entire evaluation interval known before splitting."""

    case: UniverseCase
    cutoff: str
    end: str
    identity: str
    split: str = ""


def opportunities(root: Path, count: int) -> list[Opportunity]:
    """Deduplicate equivalent inputs/targets even if their public card names differ."""
    unique: dict[str, Opportunity] = {}
    for case in load_universe(root):
        aligned = pd.DataFrame(case.histories).dropna()
        dates = pd.DatetimeIndex(pd.to_datetime(aligned.index))
        period = _observation_period_business_days(aligned)
        for cutoff in cutoff_dates(case, count):
            origin = int(dates.get_loc(pd.Timestamp(cutoff)))
            end_position = (
                origin + max(case.horizons)
                if period <= 2
                else int(
                    dates.searchsorted(pd.Timestamp(cutoff) + pd.offsets.BDay(max(case.horizons)))
                )
            )
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
                identity, Opportunity(case, cutoff, str(dates[end_position].date()), identity)
            )
    return sorted(unique.values(), key=lambda item: (item.cutoff, item.identity))


def assign_splits(items: list[Opportunity]) -> tuple[str, str]:
    """Global chronological splits; purge labels extending into the following split."""
    dates = sorted({item.cutoff for item in items})
    if len(dates) < 10:
        raise ValueError("at least ten distinct cutoff dates are required")
    selection_start = dates[int(0.4 * len(dates))]
    holdout_start = dates[int(0.7 * len(dates))]
    for item in items:
        if item.cutoff < selection_start:
            item.split = "fit" if item.end < selection_start else "purged"
        elif item.cutoff < holdout_start:
            item.split = "select" if item.end < holdout_start else "purged"
        else:
            item.split = "holdout"
    return selection_start, holdout_start


def paired_metrics(
    samples: np.ndarray, observed: np.ndarray, base: dict[str, float]
) -> dict[str, float]:
    """Delegate all scoring to the existing scorer; normalization is diagnostic only."""
    scales = {key: max(value, 1e-12) for key, value in base.items()}
    result = _composite(
        samples.reshape(len(samples), -1),
        observed,
        weights=(5 / 7, 0.0, 2 / 7) if observed.size == 1 else (0.5, 0.3, 0.2),
        tail_levels=LEVELS,
        joint="variogram",
        tail_metric="pinball",
        ref_scale=scales,
    )
    return {
        "ratio": result["composite"],
        **{f"{key}_ratio": result[key] / scales[key] for key in ("marginal", "joint", "tail")},
    }


def summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Average seeds within each case; exclude frozen F3 from candidate admission gates."""
    if not rows:
        return {"cases": 0, "pass": False}
    frame = pd.DataFrame(rows)
    active = frame[frame.family != "T2-F3"]
    grouped = active.groupby(["identity", "cutoff", "family"])[
        ["ratio", "marginal_ratio", "tail_ratio"]
    ].mean()
    if grouped.empty:
        return {"cases": 0, "pass": False}
    ratios = grouped.ratio.clip(lower=1e-12)
    result: dict[str, Any] = {
        "cases": len(grouped),
        "distinct_dates": len(set(grouped.index.get_level_values("cutoff"))),
        "geometric_ratio": float(np.exp(np.log(ratios).mean())),
        "median_ratio": float(ratios.median()),
        "win_rate": float((ratios < 1).mean()),
        "worst_decile": float(ratios.quantile(0.9)),
        "marginal_ratio": float(np.exp(np.log(grouped.marginal_ratio.clip(lower=1e-12)).mean())),
        "tail_ratio": float(np.exp(np.log(grouped.tail_ratio.clip(lower=1e-12)).mean())),
    }
    result["families"] = {
        family: float(np.exp(np.log(part.ratio.clip(lower=1e-12)).mean()))
        for family, part in grouped.groupby(level="family")
    }
    # One seed cannot rescue another seed's aggregate loss. Seeds are not independent cases.
    seed_geos = [
        float(np.exp(np.log(part.ratio.clip(lower=1e-12)).mean()))
        for _, part in active.groupby("seed")
    ]
    result["seed_geometric_ratios"] = seed_geos
    result["pass"] = bool(
        len(grouped) >= 30
        and result["distinct_dates"] >= 10
        and result["geometric_ratio"] < 1.0
        and result["median_ratio"] <= 1.02
        and result["win_rate"] >= 0.5
        and result["worst_decile"] <= 1.10
        and result["marginal_ratio"] <= 1.03
        and result["tail_ratio"] <= 1.05
        and max(seed_geos) <= 1.01
        and max(result["families"].values()) <= 1.03
    )
    return result


def evaluate_case(
    item: Opportunity, draws: int, seed_salt: str
) -> tuple[dict[str, pd.Series], NumericForecast, np.ndarray, int]:
    case = item.case
    histories = {
        asset: series[series.index.astype(str).str.slice(0, 10) <= item.cutoff]
        for asset, series in case.histories.items()
    }
    # Identity includes held-out observations only for deduplication, not RNG or model inputs.
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
    return histories, base, future_observations(case, item.cutoff), seed


def run(root: Path, out: Path, cutoffs: int, draws: int, seeds: tuple[str, ...]) -> dict[str, Any]:
    """Fit, select, freeze, and evaluate once. Refuse overwriting previous experiments."""
    root, out = root.resolve(), out.resolve()
    if out == root or root in out.parents:
        raise ValueError("experiment outputs must be outside the public repository")
    out.mkdir(parents=True, exist_ok=False)
    items = opportunities(root, cutoffs)
    boundaries = assign_splits(items)
    manifest = {
        "protocol": "v4-ablation-1",
        "draws": draws,
        "seeds": seeds,
        "boundaries": boundaries,
        "tail_grid": TAIL_GRID,
        "baseline": BASE,
        "candidates": [V4_A.name, V4_B.name, "v4-c-tail"],
        "minimum_tail_fit_cases": 40,
        "limits": (
            "public historical diagnostic; not private Development score; "
            "public panels may have revised vintages"
        ),
        "cases": [
            dict(
                identity=x.identity,
                unit_id=x.case.unit_id,
                cutoff=x.cutoff,
                end=x.end,
                split=x.split,
                family=x.case.family,
            )
            for x in items
        ],
    }
    (out / "protocol.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        "Frozen splits:",
        {s: sum(x.split == s for x in items) for s in ("fit", "select", "holdout", "purged")},
        flush=True,
    )

    fit: dict[tuple[float, float], list[float]] = {pair: [] for pair in TAIL_GRID}
    fit_ids: set[str] = set()
    for item in items:
        case = item.case
        if (
            item.split != "fit"
            or case.family == "T2-F3"
            or len(case.assets) * len(case.horizons) != 1
        ):
            continue
        for salt in seeds:
            _, base, y, _ = evaluate_case(item, draws, salt)
            scale = _components(base.samples.reshape(draws, -1), y)
            for pair in TAIL_GRID:
                fit[pair].append(
                    paired_metrics(calibrate_single_cell_tails(base.samples, *pair), y, scale)[
                        "ratio"
                    ]
                )
        fit_ids.add(item.identity)
    tail_pair = (
        min(fit, key=lambda p: np.mean(np.log(np.maximum(fit[p], 1e-12))))
        if len(fit_ids) >= 40
        else (1.0, 1.0)
    )
    fitted = {
        "tail_pair": tail_pair,
        "fit_cases": len(fit_ids),
        "grid": {
            str(pair): float(np.exp(np.log(np.maximum(values, 1e-12)).mean())) if values else None
            for pair, values in fit.items()
        },
    }
    (out / "fit.json").write_text(json.dumps(fitted, indent=2) + "\n")
    print("Fit complete:", tail_pair, "cases", len(fit_ids), flush=True)

    reports: dict[str, Any] = {"fit": fitted}
    selection = "baseline"
    # Selection caches only model draws, kept in memory and discarded before holdout.
    for split in ("select", "holdout"):
        rows: dict[str, list[dict[str, Any]]] = {n: [] for n in (V4_A.name, V4_B.name, "v4-c-tail")}
        cached: list[
            tuple[Opportunity, str, int, dict[str, pd.Series], NumericForecast, np.ndarray]
        ] = []
        eligible = [x for x in items if x.split == split]
        for index, item in enumerate(eligible):
            case = item.case
            for salt in seeds:
                histories, base, y, seed = evaluate_case(item, draws, salt)
                scale = _components(base.samples.reshape(draws, -1), y)
                candidates = {
                    c.name: forecast_numeric_v4(
                        histories,
                        case.assets,
                        case.horizons,
                        case.target_type,
                        case.target_frequency,
                        draws,
                        seed,
                        case.family,
                        c,
                        base,
                    ).samples
                    for c in (V4_A, V4_B)
                }
                candidates["v4-c-tail"] = (
                    calibrate_single_cell_tails(base.samples, *tail_pair)
                    if case.family != "T2-F3"
                    else base.samples.copy()
                )
                if split == "holdout":
                    candidates["frozen-selection"] = _selected_draws(
                        selection, item, histories, base, draws, seed, tail_pair
                    )
                else:
                    cached.append((item, salt, seed, histories, base, y))
                for name, samples in candidates.items():
                    if case.family == "T2-F3" and not np.array_equal(samples, base.samples):
                        raise AssertionError("F3 changed")
                    rows.setdefault(name, []).append(
                        {
                            "identity": item.identity,
                            "unit_id": case.unit_id,
                            "family": case.family,
                            "cutoff": item.cutoff,
                            "seed": salt,
                            "candidate": name,
                            **paired_metrics(samples, y, scale),
                        }
                    )
            if (index + 1) % 20 == 0:
                print(split, index + 1, "/", len(eligible), flush=True)
        if split == "select":
            admitted = [name for name, records in rows.items() if summary(records)["pass"]]
            # Combination is permitted only when BOTH one-factor ablations passed selection.
            if V4_A.name in admitted and V4_B.name in admitted:
                admitted.append("v4-ab")
            for name in list(admitted):
                for variant in ([name] if name == "v4-ab" else []) + ["ensemble:" + name]:
                    for item, salt, seed, histories, base, y in cached:
                        samples = _selected_draws(
                            variant, item, histories, base, draws, seed, tail_pair
                        )
                        rows.setdefault(variant, []).append(
                            {
                                "identity": item.identity,
                                "unit_id": item.case.unit_id,
                                "family": item.case.family,
                                "cutoff": item.cutoff,
                                "seed": salt,
                                "candidate": variant,
                                **paired_metrics(
                                    samples, y, _components(base.samples.reshape(draws, -1), y)
                                ),
                            }
                        )
            summaries = {name: summary(records) for name, records in rows.items()}
            valid = [name for name, report in summaries.items() if report["pass"]]
            selection = (
                min(valid, key=lambda n: summaries[n]["geometric_ratio"]) if valid else "baseline"
            )
            (out / "frozen-selection.json").write_text(
                json.dumps(
                    {
                        "selection": selection,
                        "tail_pair": tail_pair,
                        "selection_summary": summaries,
                    },
                    indent=2,
                )
                + "\n"
            )
            print("Frozen candidate:", selection, flush=True)
        reports[split] = {name: summary(records) for name, records in rows.items()}
        pd.DataFrame([r for records in rows.values() for r in records]).to_csv(
            out / f"{split}-ratios.csv", index=False
        )
        cached.clear()
    reports["selection"] = selection
    reports["decision"] = (
        "CANDIDATE_FOR_DEVELOPMENT_AB"
        if selection != "baseline" and reports["holdout"]["frozen-selection"]["pass"]
        else "RETAIN_BASELINE"
    )
    reports["leaderboard_prediction"] = None
    (out / "summary.json").write_text(json.dumps(reports, indent=2) + "\n")
    print(json.dumps(reports, indent=2), flush=True)
    return reports


def _selected_draws(
    name: str,
    item: Opportunity,
    histories: dict[str, pd.Series],
    base: NumericForecast,
    draws: int,
    seed: int,
    tail_pair: tuple[float, float],
) -> np.ndarray:
    ensemble = name.startswith("ensemble:")
    name = name.removeprefix("ensemble:")
    case = item.case
    if case.family == "T2-F3" or name == "baseline":
        return base.samples.copy()
    if name == "v4-c-tail":
        samples = calibrate_single_cell_tails(base.samples, *tail_pair)
    else:
        configs = {c.name: c for c in (V4_A, V4_B, V4_AB)}
        samples = forecast_numeric_v4(
            histories,
            case.assets,
            case.horizons,
            case.target_type,
            case.target_frequency,
            draws,
            seed,
            case.family,
            configs[name],
            base,
        ).samples
    return mixture_draws(base.samples, samples, 0.30, seed) if ensemble else samples


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cutoffs", type=int, default=6)
    parser.add_argument("--draws", type=int, default=1000)
    args = parser.parse_args()
    if args.draws < 1000 or args.cutoffs < 6:
        raise SystemExit("use at least 1000 draws and 6 cutoffs for this frozen protocol")
    run(args.root, args.out, args.cutoffs, args.draws, ("v4-seed-17", "v4-seed-43"))


if __name__ == "__main__":
    main()

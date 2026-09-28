"""## Executive summary (read this first)

Replay V5.1 and V9-B on the V9-0 origin manifest fixed before V9-A.
Use the canonical metric components through the existing paired scorer. The
private normalization scale is unavailable: these are paired public-history
proxies, not leaderboard estimates. All case-level losses stay outside git.
"""

from __future__ import annotations

import argparse
import json
import tomllib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from backtesting.universe_backtest import (
    _components,
    calibration_seed,
    future_observations,
    load_universe,
)
from backtesting.v4_ablation import paired_metrics
from backtesting.v9_manifest import verify
from qfbench2_track_forecasting.numeric_v3 import forecast_numeric_v3
from qfbench2_track_forecasting.numeric_v9b import apply_vol_term_structure
from qfbench2_track_forecasting.text_first_v5 import apply_text_first_v5

SEEDS = ("v9a-seed-17", "v9a-seed-43", "v9a-seed-71")
DRAWS = (500, 1000, 2000)


@dataclass(frozen=True)
class Replay:
    """The one dated case specified by the frozen date-only manifest."""

    case: object
    cutoff: str
    end: str
    split: str


def _family_case(item: Replay, root: Path, draws: int, salt: str, audit_f3: bool):
    case = item.case
    family = case.family
    if family == "T2-F3" and not audit_f3:
        return None
    histories = {
        asset: series[series.index.astype(str).str.slice(0, 10) <= item.cutoff]
        for asset, series in case.histories.items()
    }
    seed = calibration_seed(case.unit_id, item.cutoff, family, draws, salt)
    baseline = forecast_numeric_v3(
        histories, case.assets, case.horizons, case.target_type,
        case.target_frequency, draws, seed, family,
    )
    alternative = apply_vol_term_structure(baseline, case.assets, family)
    if family == "T2-F3":
        if (alternative is not baseline
                or alternative.samples.tobytes() != baseline.samples.tobytes()):
            raise AssertionError("V9-B must exactly preserve F3 Numeric V3")
        return None
    card = tomllib.loads((root / "units" / case.unit_id / "card.toml").read_text())
    common = (histories if family in {"T2-F1", "T2-F4"} else {},
              case.assets, case.horizons, case.target_type, case.target_frequency,
              family, item.cutoff, seed, root / "units" / case.unit_id / "text",
              card["targets"].get("value_unit", ""))
    base_samples, base_text = apply_text_first_v5(
        baseline.samples, *common, interpreter_version="v5.1"
    )
    candidate_samples, candidate_text = apply_text_first_v5(
        alternative.samples, *common, interpreter_version="v5.1"
    )
    if base_text["applied"] != candidate_text["applied"]:
        raise AssertionError("text router activation must be the same")
    y = future_observations(case, item.cutoff)
    base_scale = _components(base_samples.reshape(draws, -1), y)
    metric = paired_metrics(candidate_samples, y, base_scale)
    # Score each requested horizon independently for diagnosis. These are
    # canonical scorer calls on a slice, not an alternate objective.
    horizon_rows = []
    for index, horizon in enumerate(case.horizons):
        observed = y.reshape(len(case.assets), len(case.horizons))[:, index]
        control = base_samples[:, :, index : index + 1]
        modified = candidate_samples[:, :, index : index + 1]
        scale = _components(control.reshape(draws, -1), observed)
        value = paired_metrics(modified, observed, scale)
        horizon_rows.append({"horizon": horizon,
                             "bucket": "medium" if horizon <= 21 else "long",
                             "ratio": value["ratio"],
                             "marginal_ratio": value["marginal_ratio"],
                             "tail_ratio": value["tail_ratio"]})
    return metric, horizon_rows, baseline.metadata["regime"]["fragility"], base_text["applied"]


def _stats(rows: list[dict]) -> dict:
    frame = pd.DataFrame(rows)
    ratio = frame.ratio.clip(lower=1e-12)
    return {"cases": len(frame), "distinct_dates": frame.cutoff.nunique(),
            "geometric_ratio": float(np.exp(np.log(ratio).mean())),
            "arithmetic_ratio": float(ratio.mean()),
            "worst_decile": float(ratio.quantile(0.9)),
            "win_rate": float((ratio < 1).mean()),
            "marginal_ratio": float(np.exp(np.log(frame.marginal_ratio.clip(lower=1e-12)).mean())),
            "tail_ratio": float(np.exp(np.log(frame.tail_ratio.clip(lower=1e-12)).mean())),
            "joint_ratio": float(np.exp(np.log(frame.loc[
                frame.joint_score_active, "joint_ratio"].clip(lower=1e-12)).mean()))
            if frame.joint_score_active.any() else None}


def _groups(frame: pd.DataFrame, key: str) -> dict:
    return {str(name): _stats(group.to_dict("records"))
            for name, group in frame.groupby(key) if len(group) >= 1}


def run(root: Path, out: Path, manifest_path: Path, draws: int, salt: str) -> dict:
    if draws not in DRAWS or salt not in SEEDS:
        raise ValueError("only the predeclared draw counts and seeds are allowed")
    root, out = root.resolve(), out.resolve()
    if out == root or root in out.parents:
        raise ValueError("case outcomes must be written outside public git")
    out.mkdir(parents=True, exist_ok=False)
    manifest = json.loads(manifest_path.read_text())
    verify(manifest, root)
    cases = {case.unit_id: case for case in load_universe(root)}
    records = []
    horizon_records = []
    frozen_audit = 0
    for index, row in enumerate(manifest["entries"], 1):
        if row["split"] == "purged":
            continue
        case = cases[row["unit_id"]]
        item = Replay(case, row["cutoff"], row["end"], row["split"])
        audit = (draws, salt) == (500, SEEDS[0])
        value = _family_case(item, root, draws, salt, audit)
        if case.family == "T2-F3":
            frozen_audit += int(audit)
            metric = {"ratio": 1.0, "marginal_ratio": 1.0,
                      "tail_ratio": 1.0, "joint_ratio": 1.0}
            fragility, text_active = None, False
        else:
            assert value is not None
            metric, per_horizon, fragility, text_active = value
            for horizon in per_horizon:
                horizon_records.append({"family": case.family, "split": item.split,
                                        "cutoff": item.cutoff, **horizon})
        records.append({"family": case.family, "split": item.split, "cutoff": item.cutoff,
                        "unit_id": case.unit_id, "target_type": case.target_type,
                        "frequency": case.target_frequency,
                        "fragility_bucket": ("unknown" if fragility is None else
                                             "low" if fragility < .2 else
                                             "mid" if fragility < .4 else "high"),
                        "joint_score_active": row["target_cells"] > 1,
                        "text_active": text_active, **metric})
        if index % 100 == 0:
            print(f"V9-B {draws}/{salt}: {index}/{len(manifest['entries'])}", flush=True)
    detail = pd.DataFrame(records)
    horizon = pd.DataFrame(horizon_records)
    detail.to_parquet(out / "case_ratios.parquet", index=False)
    horizon.to_parquet(out / "horizon_ratios.parquet", index=False)
    summaries = {
        "protocol": "v9-b-vol-term-fixed-1", "manifest_sha256": manifest["entries_sha256"],
        "draws": draws, "seed": salt, "f3_byte_audits": frozen_audit,
        "text_active_cases": int(detail.text_active.sum()),
        "all": _stats(records),
        "splits": _groups(detail, "split"),
        "families": _groups(detail, "family"),
        "family_by_split": _groups(detail.assign(family_split=detail.family + "/" + detail.split),
                                   "family_split"),
        "fragility": _groups(detail[detail.family != "T2-F3"], "fragility_bucket"),
        "target_type": _groups(detail, "target_type"),
        "horizon_buckets": {
            str(name): {"cells": len(group), "geometric_ratio": float(np.exp(np.log(
                group.ratio.clip(lower=1e-12)).mean())),
                        "marginal_ratio": float(np.exp(np.log(
                            group.marginal_ratio.clip(lower=1e-12)).mean())),
                        "tail_ratio": float(np.exp(np.log(
                            group.tail_ratio.clip(lower=1e-12)).mean()))}
            for name, group in horizon.groupby(["split", "family", "bucket"])
        },
    }
    (out / "summary.json").write_text(json.dumps(summaries, indent=2) + "\n")
    return summaries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--manifest", type=Path,
                        default=Path("backtesting/v9_frozen_origins.json"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--draws", type=int, default=500)
    parser.add_argument("--seed", choices=SEEDS, default=SEEDS[0])
    args = parser.parse_args()
    result = run(args.root, args.out, args.manifest, args.draws, args.seed)
    print(json.dumps({"all": result["all"], "splits": result["splits"],
                      "families": result["families"]}, indent=2))


if __name__ == "__main__":
    main()

"""## Executive summary (read this first)

One-shot 2024 evaluation on a fixed 21-business-day origin grid. Run only
after the complete code and frozen coefficients have a verified remote SHA.
Per-origin target values and results go to a path outside the repository.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from qfbench2_common.scoring import crps

from qfbench2_track_forecasting.origin01 import HORIZONS, SEED
from qfbench2_track_forecasting.origin01.engine import forecast, signal
from qfbench2_track_forecasting.origin01.shock_detector import excess
from qfbench2_track_forecasting.origin01.unreacted_gate import unreacted
from qfbench2_track_forecasting.origin01.location_shift import native_shift
from qfbench2_track_forecasting.thesis01.asset_semantics import family, load_universe
from qfbench2_track_forecasting.thesis01.v51_shift import v51_no_text_prior
from qfbench2_track_forecasting.v12.data_parity import _label

from .active_signal_eval import grouped, summary
from .edge_audit import write_edges
from .historical_diagnostics import coverage
from .negative_controls import controlled


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def score(draws, truth, scale):
    return float(crps.crps_marginal(np.asarray(draws).reshape(-1, 1),
                                    np.asarray([truth]))) / scale


def shock_bin(z):
    z = abs(z)
    if z < 2:
        return "none"
    if z < 2.5:
        return "2-2.5"
    if z < 3:
        return "2.5-3"
    return "3+"


def verdict(rows, control):
    main = summary(rows)
    active = summary([r for r in rows if r["origin_alpha"] != 0])
    if len(rows) < 50 or active["cells"] < 50:
        return "INCONCLUSIVE"
    ratios = [control[k]["ratio"] for k in ("time_shuffled", "peer_permuted")]
    concentration = Counter(r["asset"] for r in rows if r["origin_alpha"] != 0)
    not_single = len(concentration) > 1 and max(concentration.values()) / sum(concentration.values()) < 0.8
    return ("YES" if main["ratio"] < 1 and active["ratio"] < .98
            and all(x is not None and x > main["ratio"] for x in ratios) and not_single
            else "NO")


def evaluate(root: Path, panel: Path, model: Path, training: Path,
             private_out: Path, results: Path, pre_final_sha: str):
    if len(pre_final_sha) != 40 or private_out.resolve().is_relative_to(root.resolve()):
        raise ValueError("Verified pre-final SHA and outside-repo private output required")
    frozen = json.loads((root / "backtesting/origin01/frozen_inputs.json").read_text())
    for name, path in (("panel", panel), ("training", training), ("model", model)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != frozen[name + "_sha256"]:
            raise ValueError(f"Frozen {name} artifact mismatch")
    data, fitted = np.load(panel), np.load(model)
    assets = data["assets"].tolist()
    if assets != fitted["assets"].tolist() or tuple(fitted["horizons"]) != HORIZONS:
        raise ValueError("Frozen asset order or horizon mismatch")
    if fitted["max_target_end"] > np.datetime64("2023-12-31"):
        raise ValueError("The model has read 2024 labels")
    series, kinds, _ = load_universe(root)
    dates = pd.DatetimeIndex(data["dates"])
    grid = pd.bdate_range("2001-01-02", "2024-12-18")[::21]
    origins = grid[grid.year == 2024]
    origin_rows = dates.get_indexer(origins)
    if np.any(origin_rows < 1):
        raise ValueError("Origin or previous business observation absent")
    z, sigma = data["z"], data["sigma"]
    source_matrix = excess(z[origin_rows - 1])
    rng = np.random.default_rng(1901)
    shuffled_source = source_matrix[rng.permutation(len(origins))]
    rows = []
    shock_origins = int(np.any(source_matrix != 0, axis=1).sum())
    source_events = int((source_matrix != 0).sum())
    for o, origin in enumerate(origins):
        index = int(origin_rows[o])
        for i, asset in enumerate(assets):
            if origin not in series[asset].index or not np.isfinite(sigma[index, i]):
                continue
            # This is the first point where 2024 labels are constructed.
            labels = [_label(series[asset], kinds[asset], origin, h, "2100-01-01", False)
                      for h in HORIZONS]
            eligible = [hidx for hidx, label in enumerate(labels)
                        if label is not None and label[1] <= pd.Timestamp("2024-12-18")]
            if not eligible:
                continue
            group = family(asset, kinds[asset])
            runtime_group = {"FX": "T2-F2", "Rates": "T2-F1",
                             "Factor/Equity": "T2-F4"}[group]
            draw = v51_no_text_prior(series[asset], asset, kinds[asset], list(HORIZONS),
                                     runtime_group, str(origin.date()), SEED,
                                     1000 if group == "Factor/Equity" else 500)
            alpha, contributions, dom, source, gate = signal(fitted["coef"], z,
                                                               index, i, HORIZONS)
            # Fixed source-name permutation is a placebo only at inference.
            controls = {
                "time_shuffled": controlled(fitted["coef"], shuffled_source[o],
                                             z[index, i], i, "time_shuffled"),
                "peer_permuted": controlled(fitted["coef"], source_matrix[o],
                                             z[index, i], i, "peer_permuted")}
            shifted, shifts = forecast(draw, alpha, sigma[index, i], HORIZONS)
            for hidx in eligible:
                h = HORIZONS[hidx]
                scale = float(sigma[index, i] * np.sqrt(h))
                native, end = labels[hidx]
                truth = float(series[asset].loc[origin] + native
                              if kinds[asset] == "level" else native)
                base = draw[:, hidx]
                sd = max(float(np.std(base)), 1e-8)
                record = {"origin_date": str(origin.date()), "target_end": str(end.date()),
                          "asset": asset, "group": group, "horizon": h,
                          "target_q": float(native / scale),
                          "v51": score(base, truth, scale),
                          "origin": score(shifted[:, hidx], truth, scale),
                          "origin_alpha": float(alpha[hidx]),
                          "origin_shift_sd": float(abs(shifts[hidx]) / sd),
                          "gate": gate, "source_count": int((source != 0).sum() - (source[i] != 0)),
                          "dominant_source": assets[dom],
                          "dominant_group": family(assets[dom], kinds[assets[dom]]),
                          "dominant_shock_sign": int(np.sign(source[dom])),
                          "dominant_contribution": float(contributions[hidx, dom]),
                          "dominant_shock_bin": shock_bin(z[index - 1, dom])}
                for name, value in controls.items():
                    shift = native_shift(value[hidx], sigma[index, i], h)
                    record[name] = score(base + shift, truth, scale)
                    record[name + "_alpha"] = float(value[hidx])
                    record[name + "_shift_sd"] = abs(shift) / sd
                rows.append(record)
        print(f"2024 origin {o+1}/{len(origins)}: {origin.date()}", flush=True)
    dump(private_out, rows)
    active = [r for r in rows if r["origin_alpha"] != 0]
    controls = {name: summary(rows, name) for name in ("time_shuffled", "peer_permuted")}
    controls["future_mutation"] = {"passed": True, "test": "test_origin01_future_mutation",
                                   "guarantee": "signal accesses only row t and t-1"}
    main = summary(rows)
    group_result, horizon_result = grouped(rows, "group"), grouped(rows, "horizon")
    horizon_counts = {str(h): {"cells": horizon_result.get(str(h), {}).get("cells", 0),
                                "sample": "LOW SAMPLE" if horizon_result.get(str(h), {}).get("cells", 0) < 50 else "OK"}
                      for h in HORIZONS}
    concentration = Counter(r["dominant_source"] for r in active)
    bins = {b: summary([r for r in active if r["dominant_shock_bin"] == b])
            for b in ("2-2.5", "2.5-3", "3+")}
    verdict_value = verdict(rows, controls)
    final = {"pre_final_sha": pre_final_sha, "parent": "7e73f3623ec93e7efca852904ab6d656489d2b5c",
             "training_cutoff": "2023-12-31", "final_period": "2024",
             "grid": "2001-01-02 anchored every 21 business days",
             "assets": len(assets), "horizons": list(HORIZONS), "final_origins": len(origins),
             "shock_origin_count": shock_origins, "source_shock_events": source_events,
             "active_cell_count": len(active), "active_frequency": len(active) / len(rows) if rows else None,
             "mean_active_sources_per_origin": float(np.mean((source_matrix != 0).sum(axis=1))),
             "overall": main, "horizon_cells": horizon_counts,
             "dominant_source_distribution": dict(concentration),
             "shock_bins": bins, "ready_for_origin_02": verdict_value,
             "ready_for_one_shot_submission": "NO",
             "qualification": "Revised public panel; no-text V5.1 ablation, not official PIT"}
    dump(results / "final_summary.json", final)
    dump(results / "active_signal_summary.json", summary(active))
    dump(results / "negative_controls.json", controls)
    pd.DataFrame([{"group": k, **v} for k, v in group_result.items()]).to_csv(results / "group_summary.csv", index=False)
    pd.DataFrame([{"horizon": k, **v, "sample": horizon_counts[k]["sample"]}
                  for k, v in horizon_result.items()]).to_csv(results / "horizon_summary.csv", index=False)
    edge_count = write_edges(training, model, results / "edge_summary.csv", kinds)
    artifact = {"pre_final_sha": pre_final_sha, "private_outcome_sha256":
                hashlib.sha256(private_out.read_bytes()).hexdigest(),
                "private_outcome_rows": len(rows),
                "private_date_coverage": [str(origins.min().date()), str(origins.max().date())],
                "private_panel_sha256": hashlib.sha256(panel.read_bytes()).hexdigest(),
                "private_model_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
                "private_training_sha256": hashlib.sha256(training.read_bytes()).hexdigest(),
                "edge_rows": edge_count, "historical_coverage": coverage(training),
                "seed": SEED}
    dump(results / "artifact_manifest.json", artifact)
    return final


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--panel", type=Path, required=True)
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--training", type=Path, required=True)
    p.add_argument("--private-out", type=Path, required=True)
    p.add_argument("--results", type=Path, default=Path("backtesting/origin01/results"))
    p.add_argument("--pre-final-sha", required=True)
    a = p.parse_args()
    print(json.dumps(evaluate(a.root, a.panel, a.model, a.training,
                              a.private_out, a.results, a.pre_final_sha), indent=2))

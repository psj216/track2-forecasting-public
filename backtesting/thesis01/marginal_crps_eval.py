"""## Executive summary (read this first)

Run one frozen sparse-grid chronological evaluation. All candidates share the
same real V5.1 code-path draws with empty origin text. Only location changes.
Write individual outcomes outside Git; publish grouped, unit-normalized CRPS.
"""

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from qfbench2_common.scoring import crps

from qfbench2_track_forecasting.thesis01.asset_semantics import family, load_universe
from qfbench2_track_forecasting.thesis01.v51_shift import shift_only, v51_no_text_prior
from qfbench2_track_forecasting.v12.joint_dataset import HORIZONS

from .diagnostics import aggregate, correlation, group
from .era_analysis import episode
from .rolling_signal_eval import prepared

SEED = 19
SIGNALS = ("same", "lag", "time_shuffled", "peer_permuted")


def _crps(draws: np.ndarray, truth: float) -> float:
    return float(crps.crps_marginal(draws.reshape(-1, 1), np.asarray([truth])))


def _period(date: pd.Timestamp) -> str:
    if date.year <= 2012:
        return "development"
    if date.year <= 2017:
        return "validation"
    return "final"


def _dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def evaluate(root: Path, panel: Path, private_out: Path, results: Path) -> dict:
    if private_out.resolve().is_relative_to(root.resolve()):
        raise ValueError("Individual results must remain outside Git")
    data, signals, betas, counts = prepared(panel)
    series, kinds, first = load_universe(root)
    assets = data["assets"].tolist()
    origins = pd.to_datetime(data["origins"])
    rows = []
    controls = []
    for o, origin in enumerate(origins):
        period = _period(origin)
        if period == "development":
            continue
        row = int(data["grid_rows"][o])
        stamp = str(origin.date())
        for a, asset in enumerate(assets):
            eligible_h = [h for h in range(len(HORIZONS))
                          if np.isfinite(data["native"][o, a, h])
                          and np.isfinite(data["sigma"][row, a])
                          and all(np.isfinite(betas[name][a, h]) and
                                  np.isfinite(signals[name][o, a]) for name in SIGNALS)]
            if not eligible_h or origin not in series[asset].index:
                continue
            group_name = family(asset, kinds[asset])
            runtime_family = {"FX": "T2-F2", "Rates": "T2-F1",
                              "Factor/Equity": "T2-F4"}[group_name]
            draws = v51_no_text_prior(series[asset], asset, kinds[asset],
                                      list(HORIZONS), runtime_family, stamp, SEED,
                                      1000 if runtime_family == "T2-F4" else 500)
            anchor = float(series[asset].loc[origin])
            for h in eligible_h:
                horizon = HORIZONS[h]
                reference = draws[:, h]
                native = float(data["native"][o, a, h])
                truth = anchor + native if kinds[asset] == "level" else native
                scale = float(data["sigma"][row, a] * np.sqrt(horizon))
                base_crps = _crps(reference, truth)
                sd = max(float(np.std(reference)), 1e-8)
                scores = {}
                for name in SIGNALS:
                    delta = float(betas[name][a, h] * signals[name][o, a] * scale)
                    scores[name] = {"shift": delta,
                                    "crps": _crps(shift_only(reference, betas[name][a, h],
                                                             signals[name][o, a],
                                                             data["sigma"][row, a], horizon), truth)}
                common = {"origin": stamp, "asset": asset, "group": group_name,
                          "horizon": horizon, "period": period,
                          "episode": episode(origin.year), "exposed_card_history":
                          stamp >= first[asset], "base_norm": base_crps / scale,
                          "target_q": float(data["normalized"][o, a, h])}
                for name in SIGNALS:
                    shift = scores[name]["shift"]
                    row_result = {**common, "signal": name,
                                  "tension": float(signals[name][o, a]),
                                  "beta": float(betas[name][a, h]),
                                  "thesis_norm": scores[name]["crps"] / scale,
                                  "shift": shift, "shift_over_sd": abs(shift) / sd,
                                  "correct_sign": bool(np.sign(shift) == np.sign(native))
                                  if shift != 0 and native != 0 else None}
                    (controls if name in {"time_shuffled", "peer_permuted"} else rows).append(row_result)
        if o % 20 == 0:
            print(f"evaluated {stamp} ({o + 1}/{len(origins)})", flush=True)
    _dump(private_out, {"primary": rows, "controls": controls})
    main = [r for r in rows if r["signal"] == "lag"]
    same = [r for r in rows if r["signal"] == "same"]
    output = {"kind": "REVISED_PUBLIC_PANEL_NO_TEXT_V51_LOCATION_ONLY",
              "split": {"development": "2001-2012 (mature by 2012-12-31)",
                        "validation": "2013-2017", "final": "2018-2023"},
              "grid": "2001-01-02 anchored every 21 business days",
              "lag_safe": {"overall": aggregate(main),
                           "validation": aggregate([r for r in main if r["period"] == "validation"]),
                           "final": aggregate([r for r in main if r["period"] == "final"]),
                           "final_group": group([r for r in main if r["period"] == "final"], "group"),
                           "final_horizon": group([r for r in main if r["period"] == "final"], "horizon")},
              "same_day": {"overall": aggregate(same),
                           "final": aggregate([r for r in same if r["period"] == "final"])},
              "eligible_final_assets": sorted({r["asset"] for r in main if r["period"] == "final"}),
              "final_exposed_card_history_fraction": float(np.mean([
                  r["exposed_card_history"] for r in main if r["period"] == "final"])),
              "warning": "Revised-history public panels and no-text V5.1 ablation; not official or PIT"}
    neg = {name: {"final": aggregate([r for r in controls
                                      if r["signal"] == name and r["period"] == "final"]),
                  "validation": aggregate([r for r in controls
                                            if r["signal"] == name and r["period"] == "validation"])}
           for name in ("time_shuffled", "peer_permuted")}
    signal_out = {"dense": {name: {"n": int(np.isfinite(data[name]).sum()),
                                    "median_abs": float(np.nanmedian(np.abs(data[name]))),
                                    "p95_abs": float(np.nanpercentile(np.abs(data[name]), 95))}
                            for name in ("same", "lag")},
                  "development_beta": {name: {"finite": int(np.isfinite(betas[name]).sum()),
                                               "median": float(np.nanmedian(betas[name])),
                                               "positive": int(np.nansum(betas[name] > 0)),
                                               "negative": int(np.nansum(betas[name] < 0)),
                                               "min_fit_pairs": int(counts[name][np.isfinite(betas[name])].min())}
                                       for name in ("same", "lag")}}
    for name in ("same", "lag"):
        for period in ("development", "validation", "final"):
            mask = np.asarray([_period(t) == period for t in origins])
            # Flattening is descriptive only; asset/horizon IC follows below.
            repeated = np.broadcast_to(signals[name][:, :, None], data["normalized"].shape)
            signal_out[f"{name}_{period}_raw_ic"] = correlation(
                repeated[mask].ravel(), data["normalized"][mask].ravel())
    era = {}
    for name in ("same", "lag"):
        subset = [r for r in rows if r["signal"] == name]
        era[name] = {ep: aggregate([r for r in subset if r["episode"] == ep])
                     for ep in sorted({r["episode"] for r in subset})}
    asset_rows = []
    for asset in assets:
        for hidx, horizon in enumerate(HORIZONS):
            subset = [r for r in main if r["asset"] == asset and r["horizon"] == horizon
                      and r["period"] == "final"]
            if not subset:
                continue
            idx = assets.index(asset)
            mask = np.asarray([_period(t) == "final" for t in origins])
            ic = correlation(signals["lag"][mask, idx], data["normalized"][mask, idx, hidx])
            stats = aggregate(subset)
            asset_rows.append({"asset": asset, "group": subset[0]["group"], "horizon": horizon,
                               "beta": float(betas["lag"][idx, hidx]),
                               "n": stats["cells"], "pearson": ic["pearson"],
                               "spearman_ic": ic["spearman"],
                               "sign_accuracy": stats["directional_sign_accuracy"],
                               "mean_shift": stats["mean_signed_shift_native"],
                               "shift_over_sd": stats["mean_shift_abs_over_baseline_sd"],
                               "baseline_crps": stats["baseline_crps"],
                               "thesis_crps": stats["thesis_crps"], "ratio": stats["ratio"]})
    _dump(results / "crps_summary.json", output)
    _dump(results / "signal_summary.json", signal_out)
    _dump(results / "negative_controls.json", neg)
    _dump(results / "era_summary.json", era)
    pd.DataFrame(asset_rows).to_csv(results / "asset_horizon_summary.csv", index=False)
    manifest = {"private_ledger_sha256": hashlib.sha256(private_out.read_bytes()).hexdigest(),
                "private_panel_sha256": hashlib.sha256(panel.read_bytes()).hexdigest(),
                "seed": SEED, "draws": {"FX": 500, "Rates": 500, "Factor/Equity": 1000},
                "selection": "frozen before final holdout", "asset_horizon_groups": len(asset_rows)}
    _dump(results / "artifact_manifest.json", manifest)
    return {"crps": output, "negative_controls": neg, "manifest": manifest}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--panel", type=Path, required=True)
    p.add_argument("--private-out", type=Path, required=True)
    p.add_argument("--results", type=Path, default=Path("backtesting/thesis01/results"))
    args = p.parse_args()
    result = evaluate(args.root, args.panel, args.private_out, args.results)
    print(json.dumps(result["crps"], indent=2))

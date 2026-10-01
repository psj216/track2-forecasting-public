"""## Executive summary (read this first)

Run exposed 2017–2024 research with nested prior-release expectations and
strictly earlier matured market labels. Three heads and controls remain fixed.
This is not a one-shot final or independent proof.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from qfbench2_common.scoring.crps import crps_marginal, crps_ensemble, tail_penalty

from qfbench2_track_forecasting.surprise01 import HEADS
from qfbench2_track_forecasting.surprise01.engine import update
from .diagnostics import aggregate
from .event_block_bootstrap import interval
from .final_eval import final_status
from .negative_controls import maps


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def prepared_coefficients(cases):
    index = {}
    for key, part in cases.groupby(["event_type", "asset", "horizon"], sort=True):
        part = part.sort_values("target_end")
        s = part["surprise"].to_numpy()
        index[key] = (part["target_end"].to_numpy(),
                      np.cumsum(s * part["q"].to_numpy()),
                      np.cumsum(np.abs(s) * part["log_scale_response"].to_numpy()),
                      np.cumsum(s * s))
    return index


def coefficients(index, family, asset, horizon, cutoff):
    key = (family, asset, horizon)
    if key not in index:
        return 0.0, 0.0, 0
    ends, mu, scale, squares = index[key]
    n = int(np.searchsorted(ends, cutoff, side="left"))
    if n < 24:
        return 0.0, 0.0, n
    denominator = float(squares[n-1] + .1 * n)
    return float(mu[n-1] / denominator), float(scale[n-1] / denominator), n


def score(draw, truth, norm):
    return float(crps_marginal(np.asarray(draw).reshape(-1, 1), np.asarray([truth]))) / norm


def evaluate(private_root, results, pre_final_sha):
    frozen = json.loads((results.parent / "frozen_inputs.json").read_text())
    cases_path = private_root / "training_cases.parquet"
    if hashlib.sha256(cases_path.read_bytes()).hexdigest() != frozen["case_sha256"]:
        raise ValueError("Frozen private cases mismatch")
    cases = pd.read_parquet(cases_path)
    if (cases["origin"] >= "2025-01-01").any() or (cases["target_end"] >= "2025-01-01").any():
        raise ValueError("2025 observations are prohibited in this research evaluation")
    index = prepared_coefficients(cases)
    evaluation = cases[(cases["origin"] >= "2017-01-01") & (cases["origin"] <= "2024-12-18")]
    flips, date_permuted, family_mapping = maps(evaluation)
    rows = []
    cached_path, cache = None, None
    entries = evaluation.sort_values(["cache_file", "event_type", "asset", "horizon"]).to_dict("records")
    for k, r in enumerate(entries):
        if r["cache_file"] != cached_path:
            cache = np.load(private_root / "draw_cache" / r["cache_file"])
            cached_path = r["cache_file"]
            expected = frozen["draw_cache_sha256"][cached_path]
            if hashlib.sha256((private_root / "draw_cache" / cached_path).read_bytes()).hexdigest() != expected:
                raise ValueError("Frozen baseline cache mismatch")
        draw = cache["samples"][:, r["asset_index"], r["horizon_index"]]
        beta, gamma, count = coefficients(index, r["event_type"], r["asset"], r["horizon"], r["origin"])
        scenarios = {"primary": (r["surprise"], beta, gamma)}
        scenarios["sign_shuffle"] = (r["surprise"] * flips[r["event_id"]], beta, gamma)
        scenarios["date_permutation"] = (date_permuted[(r["event_id"], r["event_type"])], beta, gamma)
        b2, g2, _ = coefficients(index, family_mapping[r["event_type"]], r["asset"], r["horizon"], r["origin"])
        scenarios["family_permutation"] = (r["surprise"], b2, g2)
        record = {k: r[k] for k in ("event_id", "event_type", "release_date", "origin", "asset",
                                   "group", "horizon", "q", "surprise", "log_scale_response")}
        record["fit_events"] = count
        record["v51"] = score(draw, r["truth"], r["normalization"])
        record["v51_tail_error"] = float(tail_penalty(draw.reshape(-1, 1), np.asarray([r["truth"]])))
        edges = frozen["bin_edges"][r["event_type"]]
        record["surprise_bin"] = ("small" if abs(r["surprise"]) <= edges[0] else
                                   "medium" if abs(r["surprise"]) <= edges[1] else "large")
        draws_to_score, score_keys = [], []
        for name, (s, b, g) in scenarios.items():
            changed, delta, factor = update(draw, s, b, g, r["sigma"], r["horizon"])
            for head in HEADS:
                key = head if name == "primary" else name + "_" + head
                draws_to_score.append(changed[head])
                score_keys.append(key)
                record[key + "_alpha"] = float(b * s) if head != "scale" else 0.0
                record[key + "_dispersion"] = float(g * abs(s)) if head != "location" else 0.0
                record[key + "_shift_sd"] = abs(delta) / r["baseline_sd"] if head != "scale" else 0.0
                record[key + "_factor"] = factor if head != "location" else 1.0
                record[key + "_active"] = bool((delta != 0 and head != "scale") or
                                               (factor != 1 and head != "location"))
        # One shared-toolkit call for the independently scored marginals.
        values = crps_ensemble(np.stack(draws_to_score, axis=1), r["truth"]) / r["normalization"]
        record.update({key: float(value) for key, value in zip(score_keys, values)})
        rows.append(record)
        if (k+1) % 5000 == 0:
            print(f"scored {k+1}/{len(entries)} exposed research cells", flush=True)
    private_out = private_root / "research_outcomes.json"
    dump(private_out, rows)
    heads = {head: aggregate(rows, head) for head in HEADS}
    uncertainty = {head: interval(rows, head) for head in HEADS}
    controls = {name: {head: aggregate(rows, name + "_" + head) for head in HEADS}
                for name in ("sign_shuffle", "date_permutation", "family_permutation")}
    paired_uncertainty = {
        name: {head: interval([{'release_date': r['release_date'],
                                'v51': r[name + '_' + head], head: r[head]} for r in rows], head)
               for head in HEADS}
        for name in ('sign_shuffle', 'date_permutation', 'family_permutation')}
    controls['primary_over_control_uncertainty'] = paired_uncertainty
    controls["mutation_tests"] = {"future_market": True, "later_revision": True}
    controls["sign_shuffle_scale"] = "Algebraically invariant under absolute surprise; not evidence of a scale failure."
    decision = {}
    for head in HEADS:
        ratio = heads[head]["ratio"]
        relevant = ("date_permutation", "family_permutation") if head == "scale" else ("sign_shuffle", "date_permutation", "family_permutation")
        separated = all(1 - controls[name][head]['ratio'] < .5 * (1 - ratio)
                        and paired_uncertainty[name][head]['ratio_ci95'][1] < 1
                        for name in relevant)
        group_values = {g: aggregate([r for r in rows if r["group"] == g], head)
                        for g in sorted({r["group"] for r in rows})}
        safe_groups = sum(v["ratio"] < 1.10 for v in group_values.values())
        concentration = pd.DataFrame(rows).groupby("event_id").apply(
            lambda x: float((x["v51"] - x[head]).sum()), include_groups=False)
        gains = concentration[concentration > 0]
        not_one = len(gains) >= 10 and (float(gains.max() / gains.sum()) < .5 if len(gains) else False)
        decision[head] = ("YES_RESEARCH_ONLY" if ratio < .98 and separated and safe_groups >= 2
                          and not_one and uncertainty[head]["ratio_ci95"][1] < 1
                          else "NO")
    ready = "YES_RESEARCH_ONLY" if "YES_RESEARCH_ONLY" in decision.values() else "NO"
    grouped = {}
    for field, filename in (("event_type", "event_family_summary.csv"), ("group", "target_group_summary.csv"),
                            ("horizon", "horizon_summary.csv")):
        output = []
        for value in sorted({r[field] for r in rows}):
            subset = [r for r in rows if r[field] == value]
            for head in HEADS:
                output.append({field: value, "head": head, **aggregate(subset, head)})
        pd.DataFrame(output).to_csv(results / filename, index=False)
        grouped[field] = output
    bins = {b: {"cells": len(part := [r for r in rows if r["surprise_bin"] == b]),
                "events": len({r["event_id"] for r in part}),
                "mean_abs_future_q": float(np.mean([abs(r["q"]) for r in part])),
                "extreme_q_frequency": float(np.mean([abs(r["q"]) > 2 for r in part])),
                "mean_v51_tail_error": float(np.mean([r["v51_tail_error"] for r in part])),
                "heads": {h: aggregate(part, h) for h in HEADS}}
            for b in ("small", "medium", "large")}
    summary = {"status": "EXPOSED_CHRONOLOGICAL_RESEARCH_ONLY", "pre_final_sha": pre_final_sha,
               "development": "2001-2016", "research_evaluation": "2017-2024",
               "fit_rule": "Only target_end strictly before each forecast origin",
               "information_type": "RELEASE_INNOVATION", "true_consensus_events": 0,
               "overall": heads, "event_uncertainty": uncertainty, "head_decisions": decision,
               "ready_for_surprise_02": ready, "ready_for_one_shot_submission": "NO",
               "surprise_bins": bins, "final": final_status()}
    dump(results / "validation_summary.json", summary)
    dump(results / "final_summary.json", final_status())
    for head in HEADS:
        dump(results / (head + "_summary.json"), {"research_only": True, **heads[head],
                                                 "uncertainty": uncertainty[head], "decision": decision[head]})
    dump(results / "negative_controls.json", controls)
    dump(results / "artifact_manifest.json", {"pre_final_sha": pre_final_sha,
         "private_outcome_sha256": hashlib.sha256(private_out.read_bytes()).hexdigest(),
         "private_outcome_rows": len(rows), "private_date_coverage": [evaluation["origin"].min(), evaluation["origin"].max()],
         "source_hash_manifest": "../frozen_inputs.json", "event_clusters": len({r["event_id"] for r in rows})})
    return summary


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--private-root", type=Path, required=True)
    p.add_argument("--results", type=Path, default=Path("backtesting/surprise01/results"))
    p.add_argument("--pre-final-sha", required=True)
    a = p.parse_args()
    a.results.mkdir(parents=True, exist_ok=True)
    print(json.dumps(evaluate(a.private_root, a.results, a.pre_final_sha), indent=2))

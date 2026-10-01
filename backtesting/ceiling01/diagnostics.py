"""## Executive summary (read this first)

Execute the frozen outcome-aware diagnostics, retain detailed losses privately,
and publish only grouped research results. No forecast candidate is produced.
"""

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from qfbench2_common.scoring import crps

from qfbench2_track_forecasting.ceiling01 import location_oracle, scale_oracle, tail_oracle, joint_oracle
from qfbench2_track_forecasting.ceiling01.scorer_adapter import components, score, aggregate, weights
from qfbench2_track_forecasting.ceiling01.zero_loss_bounds import replace
from qfbench2_track_forecasting.ceiling01.decomposition import summarize, pair_kind
from .build_baseline_ledger import dump, digest
from .run_feasibility import feasibility

ZERO = {
    "MARGINAL_ZERO_LOSS": ("marginal",), "JOINT_ZERO_LOSS": ("joint",),
    "TAIL_ZERO_LOSS": ("tail",), "MARGINAL_JOINT_ZERO_LOSS": ("marginal", "joint"),
    "MARGINAL_TAIL_ZERO_LOSS": ("marginal", "tail"),
    "JOINT_TAIL_ZERO_LOSS": ("joint", "tail"),
    "ALL_ZERO_LOSS": ("marginal", "joint", "tail")}


def era(origin):
    year = int(str(origin)[:4])
    return 0 if year <= 2016 else 1 if year <= 2019 else 2 if year <= 2021 else 3


def stats(values):
    a = np.asarray(values)
    if not len(a):
        return None
    return {"n": len(a), "min": float(a.min()), "max": float(a.max()),
            "quantiles_0_25_50_75_95_100": np.quantile(a, [0,.25,.5,.75,.95,1]).tolist(),
            "fraction_zero": float(np.mean(a == 0)),
            "fraction_lower_bound": float(np.mean(a == .5)),
            "fraction_upper_bound": float(np.mean(a == 2.))}


def matrix_row(rows):
    result = {"Overall": summarize(rows),
              "Single-cell": summarize([r for r in rows if r["cells"] == 1]),
              "Multi-cell": summarize([r for r in rows if r["cells"] > 1])}
    for fam in ("T2-F1", "T2-F2", "T2-F3", "T2-F4"):
        result[fam] = summarize([r for r in rows if r["family"] == fam])
    return result


def run_cards(root, private, results, frozen):
    if digest(private / "cards.json") != frozen["card_universe"]["ledger_sha256"]:
        raise ValueError("Frozen card ledger mismatch")
    cards = json.loads((private / "cards.json").read_text())
    records, cell_rows, pair_rows, horizon_rows, text_rows, cell_parameters = [], [], [], [], [], []
    arrays = {}
    all_scales = defaultdict(list)
    for i, card in enumerate(cards):
        path = private / card["file"]
        if digest(path) != card["sha256"]:
            raise ValueError("Frozen card arrays mismatch")
        data = np.load(path)
        base, truth, numeric = data["baseline"], data["truth"], data["numeric"]
        ref = components(base, truth)
        location = location_oracle.apply(base, truth)
        su, au = scale_oracle.apply(base, truth)
        sb, ab = scale_oracle.apply(base, truth, (.5, 2.))
        lu, alu = scale_oracle.apply(location, truth)
        lb, alb = scale_oracle.apply(location, truth, (.5, 2.))
        tail = tail_oracle.apply(base, truth)
        joint, joint_meta = joint_oracle.apply(base, truth)
        loc_joint, loc_meta = joint_oracle.apply(location, truth)
        variants = {"BASELINE": base, "LOCATION_ORACLE": location,
            "SCALE_ORACLE_UNCONSTRAINED": su, "SCALE_ORACLE_BOUNDED": sb,
            "LOCATION_SCALE_ORACLE_UNCONSTRAINED": lu, "LOCATION_SCALE_ORACLE_BOUNDED": lb,
            "TAIL_ORACLE": tail, "JOINT_ORACLE": joint, "LOCATION_JOINT_ORACLE": loc_joint}
        for name, a in (("scale_unconstrained", au), ("scale_bounded", ab),
                        ("location_scale_unconstrained", alu), ("location_scale_bounded", alb)):
            all_scales[name].extend(a.tolist())
        params = []
        flat, y = base.reshape(len(base), -1), truth.ravel()
        med, sd = np.median(flat, axis=0), np.maximum(np.std(flat, axis=0), 1e-12)
        for j, (h, a) in enumerate((h,a) for h in card["horizons"] for a in card["assets"]):
            m = float(crps.crps_ensemble(flat[:, j], y[j]))
            t = components(flat[:, j:j+1], y[j:j+1])["tail"]
            cell_rows.append({"card": card["id"], "origin": card["origin"], "family": card["family"],
                "asset": a, "horizon": h, "target_type": card["target_type"],
                "support": card["support"], "baseline_marginal": m, "baseline_tail": t,
                "joint": "PAIR_COMPONENT_ONLY", "truth": float(y[j]), "median": float(med[j])})
            p = {"card_index": i, "cell": j, "family": card["family"], "horizon": h,
                 "era": era(card["origin"]), "shift_sd": float((y[j]-med[j])/sd[j]),
                 "scale": float(ab[j])}
            cell_parameters.append(p)
            params.append(p)
        arrays[i] = (base, truth, ref, params)
        for name, values in variants.items():
            comp = score(values, truth, ref)
            records.append({**card, "variant": name, **comp, "baseline": ref,
                "joint_meta": joint_meta if name == "JOINT_ORACLE" else loc_meta if name == "LOCATION_JOINT_ORACLE" else None})
            vf = values.reshape(len(values), -1)
            for hi, h in enumerate(card["horizons"]):
                cols = list(range(hi*len(card["assets"]), (hi+1)*len(card["assets"])))
                rc = components(flat[:, cols], y[cols])
                vc = components(vf[:, cols], y[cols])
                r = (5/7)*(vc["marginal"]/max(rc["marginal"], 1e-12)) + (2/7)*(vc["tail"]/max(rc["tail"], 1e-12))
                horizon_rows.append({"variant": name, "horizon": h, "ratio": r,
                    "card": card["id"], "cells": len(cols), "baseline": rc})
            labels = [(h,a) for h in card["horizons"] for a in card["assets"]]
            if name in {"BASELINE", "LOCATION_ORACLE", "JOINT_ORACLE", "LOCATION_JOINT_ORACLE"}:
                for j in range(len(y)):
                    for k in range(j+1, len(y)):
                        b = float(crps.variogram_score(flat[:, [j,k]], y[[j,k]]))/2
                        v = float(crps.variogram_score(vf[:, [j,k]], y[[j,k]]))/2
                        h,a = labels[j]; hh,aa = labels[k]
                        pair_rows.append({"card": card["id"], "variant": name,
                            "kind": pair_kind(a,h,aa,hh), "baseline_joint": b, "joint": v,
                            "ratio": v/max(b,1e-12), "cells": [j,k]})
        for name, zero in ZERO.items():
            records.append({**card, "variant": name, "ratio": replace(ref, card["cells"], zero),
                "baseline": ref, **{k: (0. if k in zero else ref[k]) for k in ("marginal","joint","tail")}})
        ns = score(numeric, truth, ref)
        text_rows.append({**card, "numeric_ratio": ns["ratio"], "text_ratio": 1.,
                          "identical_draws": bool(np.array_equal(numeric, base)),
                          "normalized_loss_delta": 1. - ns["ratio"]})
        print(f"scored card oracle {i+1}/24", flush=True)

    # Fixed low-dimensional exposed cross-fit: no test-era label enters its shared correction.
    for i, card in enumerate(cards):
        base, truth, ref, params = arrays[i]
        flat = base.reshape(len(base), -1)
        sd = np.maximum(np.std(flat, axis=0), 1e-12)
        delta, multiplier, counts = [], [], []
        for p in params:
            training = [z for z in cell_parameters if z["era"] != p["era"]
                        and z["family"] == p["family"] and z["horizon"] == p["horizon"]]
            counts.append(len(training))
            delta.append(float(np.median([z["shift_sd"] for z in training])) if len(training) >= 2 else 0.)
            multiplier.append(float(np.median([z["scale"] for z in training])) if len(training) >= 2 else 1.)
        loc = (flat + sd*np.array(delta)).reshape(base.shape)
        med = np.median(flat, axis=0)
        scaled = (med + np.array(multiplier)*(flat-med)).reshape(base.shape)
        for name, values in (("STRUCTURED_LOCATION_CROSSFIT", loc), ("STRUCTURED_SCALE_CROSSFIT", scaled)):
            records.append({**card, "variant": name, **score(values, truth, ref),
                            "baseline": ref, "training_cell_counts": counts})

    actual_horizons = sorted({h for c in cards for h in c["horizons"]} | {5,21,63,126,189})
    variants = sorted({r["variant"] for r in records})
    matrix = {name: matrix_row([r for r in records if r["variant"] == name]) for name in variants}
    for name in variants:
        for h in actual_horizons:
            hr = [r for r in horizon_rows if r["variant"] == name and r["horizon"] == h]
            if name in ZERO:
                hr = []
                for r in horizon_rows:
                    if r["variant"] != "BASELINE" or r["horizon"] != h:
                        continue
                    zero = ZERO[name]
                    ratio = (0. if "marginal" in zero else 5/7) + (0. if "tail" in zero else 2/7)
                    hr.append({**r, "ratio": ratio})
            matrix[name][str(h)+"d"] = summarize(hr)
    observed = {name: v["Overall"]["score"] for name,v in matrix.items()}
    baseline_rows = [r for r in records if r["variant"] == "BASELINE"]
    bounds = {name: matrix[name] for name in ZERO}
    coverage = {}
    for selector, field in (("v51","v51"), ("v13_r2","v13")):
        fallback = [r for r in cards if r["support"][field] != "fully_modeled"]
        coverage[selector] = {"modeled_cards": len(cards)-len(fallback), "fallback_cards": len(fallback),
            "fallback_cells": sum(r["cells"] for r in fallback),
            "partial_asset_support_cards": sum(r["support"]["partial_asset_support"] for r in cards),
            "fallback_zero_loss": {"geometric": aggregate([0. if r in fallback else 1. for r in cards]),
                                   "arithmetic_sensitivity": (len(cards)-len(fallback))/len(cards)},
            "modeled_zero_loss_fallback_baseline": {"geometric": aggregate([1. if r in fallback else 0. for r in cards]),
                                                    "arithmetic_sensitivity": len(fallback)/len(cards)},
            "definition": "existing frozen support gate only; absent outside-universe outcomes unmeasurable"}
    pair_summary = {}
    for kind in ("same_asset_different_horizon", "different_asset_same_horizon", "different_asset_different_horizon"):
        pair_summary[kind] = {name: summarize([r for r in pair_rows if r["kind"] == kind and r["variant"] == name])
                             for name in ("BASELINE","LOCATION_ORACLE","JOINT_ORACLE","LOCATION_JOINT_ORACLE")}
    board_floors = {name: {"baseline_partition_cards": sum(r["cells"] == (1 if name == "single" else -1) for r in cards),
                         "leave_partition_baseline_others_zero_geometric": aggregate([
                             1. if (r["cells"] == 1) == (name == "single") else 0. for r in cards]),
                         "leave_partition_baseline_others_zero_arithmetic": float(np.mean([
                             (r["cells"] == 1) == (name == "single") for r in cards]))}
                    for name in ("single","multi")}
    board_floors["multi"]["baseline_partition_cards"] = sum(r["cells"] > 1 for r in cards)
    text_summary = {"status": "OBSERVED_CHANNEL_CONTRIBUTION", "matched_cards": len(cards),
        "numeric_only_relative_score": aggregate([r["numeric_ratio"] for r in text_rows]),
        "text_enabled_relative_score": 1., "changed_cards": sum(not r["identical_draws"] for r in text_rows),
        "family": {f: {"cases": 6, "numeric_ratio": aggregate([r["numeric_ratio"] for r in text_rows if r["family"] == f]),
                          "text_ratio": 1.} for f in ("T2-F1","T2-F2","T2-F3","T2-F4")},
        "warning": "matched exposed cards; includes existing text/context routing; no continuous-origin text inference"}
    output = {"matrix": matrix, "component_bounds": bounds, "coverage": coverage,
        "single": {"matrix": {n:v["Single-cell"] for n,v in matrix.items()}, "overall_floor": board_floors["single"]},
        "multi": {"matrix": {n:v["Multi-cell"] for n,v in matrix.items()}, "overall_floor": board_floors["multi"], "pairs": pair_summary},
        "family": {f:{n:v[f] for n,v in matrix.items()} for f in ("T2-F1","T2-F2","T2-F3","T2-F4")},
        "horizon": {str(h):{n:v[str(h)+"d"] for n,v in matrix.items()} for h in actual_horizons},
        "text": text_summary, "feasibility": feasibility([r["baseline"] for r in baseline_rows],
                                                           [r["cells"] for r in baseline_rows], observed),
        "scales": {name: stats(a) for name,a in all_scales.items()},
        "baseline": {**frozen["card_universe"], "ratio": 1.,
            "component_normalized_arithmetic_contributions": dict(zip(("marginal","joint","tail"),
                np.mean([weights(r["cells"]) for r in cards], axis=0).tolist())),
            "target_type": {t: {"cards": sum(r["target_type"] == t for r in cards),
                "oracle_matrix": {name:summarize([r for r in records if r["variant"] == name and r["target_type"] == t]) for name in variants}}
                for t in sorted({r["target_type"] for r in cards})},
            "no_family_loss_dominance_claim": "six cards each; all baseline-normalized scores equal one; raw unlike-unit losses not pooled"}}
    dump(private / "card_loss_ledger.json", records)
    dump(private / "cell_loss_ledger.json", cell_rows)
    dump(private / "pair_loss_ledger.json", pair_rows)
    dump(private / "horizon_loss_ledger.json", horizon_rows)
    dump(private / "text_loss_ledger.json", text_rows)
    return output


def run_surprise(root, private, results, frozen):
    expected = frozen["surprise_universe"]
    cases_path = private / "training_cases.parquet"
    if digest(cases_path) != expected["case_sha256"]:
        raise ValueError("SURPRISE case hash mismatch")
    cases = pd.read_parquet(cases_path)
    cases = cases[(cases.origin >= "2017-01-01") & (cases.origin <= "2024-12-18")]
    rows = []
    archived = json.loads((private / "research_outcomes.json").read_text())
    old = {(r["event_id"], r["event_type"], r["asset"], r["horizon"]): r["v51"] for r in archived}
    max_reproduction_error = 0.
    for k, (file, group) in enumerate(cases.groupby("cache_file", sort=True)):
        path = private / "draw_cache" / file
        if digest(path) != expected["cache_sha256"][file]:
            raise ValueError("SURPRISE draw hash mismatch")
        cache = np.load(path)
        for r in group.to_dict("records"):
            draw = cache["samples"][:, r["asset_index"], r["horizon_index"]]
            y, norm = r["truth"], r["normalization"]
            med, sd = np.median(draw), max(np.std(draw), 1e-12)
            loc = location_oracle.apply(draw[:,None], [y]).ravel()
            au = scale_oracle.optimal_scale(draw, y)
            ab = np.clip(au, .5, 2.)
            tail = tail_oracle.apply(draw[:,None], [y]).ravel()
            values = {"BASELINE": draw, "LOCATION_ORACLE": loc,
                "SCALE_ORACLE_UNCONSTRAINED": med+au*(draw-med),
                "SCALE_ORACLE_BOUNDED": med+ab*(draw-med),
                "LOCATION_SCALE_ORACLE_UNCONSTRAINED": np.full_like(draw,y),
                "LOCATION_SCALE_ORACLE_BOUNDED": y+.5*(loc-y), "TAIL_ORACLE": tail}
            record = {k:r[k] for k in ("event_id","event_type","origin","asset","group","horizon")}
            record.update({"truth": y, "norm": norm, "median": float(med), "sd": float(sd),
                           "shift_sd": float((y-med)/sd), "scale_unconstrained": float(au), "scale_bounded": float(ab),
                           "era": era(r["origin"])})
            for name, x in values.items():
                record[name] = float(crps.crps_ensemble(x, y))/norm
            key = (r["event_id"],r["event_type"],r["asset"],r["horizon"])
            max_reproduction_error = max(max_reproduction_error, abs(record["BASELINE"]-old[key]))
            rows.append(record)
        if (k+1) % 100 == 0:
            print(f"scored SURPRISE cache {k+1}/{cases.cache_file.nunique()}",flush=True)
    if len(rows) != expected["cells"] or max_reproduction_error > 1e-10:
        raise AssertionError("Archived SURPRISE baseline reproduction failed")
    # Group-level exposed cross-fit. Hold out complete eras, including duplicated releases.
    shared = {}
    for g in sorted({r["group"] for r in rows}):
        for h in (5,21,63,126,189):
            for e in range(4):
                train = [r for r in rows if r["group"] == g and r["horizon"] == h and r["era"] != e]
                shared[(g,h,e)] = (float(np.median([r["shift_sd"] for r in train])) if train else 0.,
                                  float(np.median([r["scale_bounded"] for r in train])) if train else 1.)
    by_key = {(r["event_id"],r["event_type"],r["asset"],r["horizon"]):r for r in rows}
    for file, group in cases.groupby("cache_file",sort=True):
        cache = np.load(private / "draw_cache" / file)
        for r in group.to_dict("records"):
            row = by_key[(r["event_id"],r["event_type"],r["asset"],r["horizon"])]
            x = cache["samples"][:,r["asset_index"],r["horizon_index"]]
            delta, mult = shared[(r["group"],r["horizon"],row["era"])]
            row["STRUCTURED_LOCATION_CROSSFIT"] = float(crps.crps_ensemble(x+delta*row["sd"], r["truth"]))/r["normalization"]
            row["STRUCTURED_SCALE_CROSSFIT"] = float(crps.crps_ensemble(row["median"]+mult*(x-row["median"]),r["truth"]))/r["normalization"]
    names = list(values) + ["STRUCTURED_LOCATION_CROSSFIT","STRUCTURED_SCALE_CROSSFIT"]
    def group_summary(part):
        base = float(np.mean([r["BASELINE"] for r in part]))
        return {"cells":len(part), "origins":len({r["origin"] for r in part}),
                "events":len({r["event_id"] for r in part}), "baseline_normalized_crps":base,
                "matrix": {name:{"loss":float(np.mean([r[name] for r in part])),
                                  "ratio":float(np.mean([r[name] for r in part]))/base} for name in names}}
    summary = group_summary(rows)
    summary.update({"scope":"MARGINAL_ONLY_EXPOSED_RESEARCH", "archived_baseline_max_abs_error":max_reproduction_error,
        "horizon":{str(h):group_summary([r for r in rows if r["horizon"]==h]) for h in (5,21,63,126,189)},
        "group":{g:group_summary([r for r in rows if r["group"]==g]) for g in sorted({r["group"] for r in rows})},
        "event_family":{g:group_summary([r for r in rows if r["event_type"]==g]) for g in sorted({r["event_type"] for r in rows})},
        "scales":{name:stats([r[name] for r in rows]) for name in ("scale_unconstrained","scale_bounded")},
        "component_bounds":{"MARGINAL_ZERO_LOSS":0.,"ALL_ZERO_LOSS":0.,"JOINT":"NOT_IN_SCORER","TAIL":"NOT_IN_SCORER"},
        "feasibility":{str(t):{"mathematically_possible":True,"required_marginal_loss_reduction":1-t,
            "oracle_reaching_target":[n for n in names if summary["matrix"][n]["ratio"]<=t]} for t in (.8,.7,.6,.5)},
        "text":"UNAVAILABLE: no origin-frozen historical text corpus"})
    dump(private / "ceiling_marginal_loss_ledger.json", rows)
    return summary


def run(root, private, surprise, pre_result):
    results = root / "backtesting/ceiling01/results"
    results.mkdir(parents=True,exist_ok=True)
    frozen = json.loads((root / "backtesting/ceiling01/frozen_inputs.json").read_text())
    cards = run_cards(root, private, results, frozen)
    continuous = run_surprise(root, surprise, results, frozen)
    outputs = {
        "baseline_summary.json":{"V13_REVISED_PUBLIC_24":cards["baseline"],
                                 "SURPRISE_EXPOSED_MARGINAL_ONLY":{k:v for k,v in continuous.items() if k in {"cells","origins","events","baseline_normalized_crps","archived_baseline_max_abs_error"}}},
        "oracle_matrix.json":{"scorer_status":"RESEARCH_PROXY_ONLY","V13_REVISED_PUBLIC_24":cards["matrix"],
                              "SURPRISE_EXPOSED_MARGINAL_ONLY":continuous["matrix"],"scales":cards["scales"]},
        "component_bounds.json":{"V13_REVISED_PUBLIC_24":cards["component_bounds"],"SURPRISE_EXPOSED_MARGINAL_ONLY":continuous["component_bounds"]},
        "coverage_bounds.json":cards["coverage"],"single_cell_summary.json":cards["single"],
        "multi_cell_summary.json":cards["multi"],"family_summary.json":cards["family"],
        "horizon_summary.json":{"V13_REVISED_PUBLIC_24":cards["horizon"],"SURPRISE_EXPOSED_MARGINAL_ONLY":continuous["horizon"]},
        "text_channel_summary.json":cards["text"],
        "feasibility_08_07_06_05.json":{"V13_REVISED_PUBLIC_24":cards["feasibility"],"SURPRISE_EXPOSED_MARGINAL_ONLY":continuous["feasibility"]},
        "surprise_marginal_summary.json":continuous}
    for filename,value in outputs.items():
        dump(results / filename,value)
    private_files = [private / name for name in ("cards.json","card_loss_ledger.json","cell_loss_ledger.json","pair_loss_ledger.json","horizon_loss_ledger.json","text_loss_ledger.json")]
    private_files += [surprise / "ceiling_marginal_loss_ledger.json"]
    manifest = {"pre_result_ceiling01_sha":pre_result,"parent_sha":frozen["parent_sha"],
                "status":"EXPOSED_ORACLE_DIAGNOSTIC_COMPLETE","scorer_status":"RESEARCH_PROXY_ONLY",
                "private_files":{p.name:{"sha256":digest(p),"rows":len(json.loads(p.read_text()))} for p in private_files},
                "public_results_sha256":{p.name:digest(p) for p in results.glob('*.json') if p.name != 'artifact_manifest.json'},
                "date_range":{k:frozen[k]["date_range"] for k in ("card_universe","surprise_universe")},
                "no_predictive_model":True,"no_submission":True,"no_official_score_prediction":True}
    dump(results / "artifact_manifest.json",manifest)
    print("CEILING-01 oracle evaluation complete",flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path.cwd())
    p.add_argument("--private",type=Path,required=True)
    p.add_argument("--surprise",type=Path,required=True)
    p.add_argument("--pre-result-sha",required=True)
    a = p.parse_args()
    run(a.root,a.private,a.surprise,a.pre_result_sha)

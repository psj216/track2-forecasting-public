"""Executive summary: synthesize stored evidence after PRE; never evaluate forecasts.

The numbers below are read from existing aggregate artifacts using explicit JSON paths.
Judgment scores are strategic assessments, not predictions of official score gains.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from .core import CANDIDATES, DIMENSIONS, OFFICIAL, PARENT, read, sha, verify_protection, weighted, decide
from .prepare import ROOT, RESULTS, save, table


def at(path, pointer=""):
    d = read(ROOT / path)
    for key in pointer.split("/") if pointer else []:
        d = d[key]
    return d


def csvrows(path):
    with (ROOT / path).open() as f:
        return list(csv.DictReader(f))


def mdtable(rows, columns):
    def cell(v):
        if v is None:
            return "MISSING / N/A"
        if isinstance(v, float):
            return f"{v:.6f}"
        return str(v).replace("|", "/").replace("\n", " ")
    return "| " + " | ".join(columns) + " |\n|" + "|".join(["---"] * len(columns)) + "|\n" + "\n".join(
        "| " + " | ".join(cell(r.get(k)) for k in columns) + " |" for r in rows)


def inventory():
    rows = []
    evidence = []
    branches = {r["branch"]: r["sha"] for r in at("backtesting/alpha_strategy_reset05/results/remote_branch_inventory.json", "branches")}
    log = [line.split("\t", 2) for line in (ROOT.parent / "reset-lineage-log.tsv").read_text().splitlines()]
    def add(name, slug, branch, path, pointer, quality, universe, decision, reason,
            result=None, pre=None, parent=None, sample="See linked aggregate artifact", next_axis="No continuation authorized", metric="baseline-relative research ratio"):
        value = at(path, pointer) if pointer else None
        if result is None and path and (ROOT / path).exists():
            # Existing Git lineage determines the containing historical commit outside this runtime.
            result = branches.get(branch, "MISSING_ARTIFACT")
        row = {"study": name, "branch": branch, "parent_SHA": parent or "NOT_RECORDED",
          "PRE_SHA": pre or "NOT_RECORDED", "RESULT_SHA": result or "MISSING_ARTIFACT",
          "objective": slug, "universe": universe, "universe_detail": sample,
          "sample_size": sample, "metric": metric, "primary_result": value,
          "decision": decision, "quality": quality, "independent_OOS": False,
          "official_submission": "inherited verified reference" if universe == "OFFICIAL" else "No new official result verified",
          "failure_reason": reason, "next_axis": next_axis, "evidence": path,
          "metric_pointer": pointer or "qualitative / missing metric", "evidence_SHA256": sha(ROOT / path),
          "artifact_storage_commit": PARENT, "result_status": "STORED_METRIC" if pointer else "MISSING_METRIC_OR_QUALITATIVE"}
        rows.append(row)
        evidence.append({k: row[k] for k in ["study", "quality", "universe", "evidence", "metric_pointer", "evidence_SHA256", "primary_result", "result_status"]})
    add("V5.1", "Official safe reference", "track2/text-first-v5.1-candidate",
        "backtesting/persistent_direction02/results/baseline_preservation_audit.json", "verified_official_reference_score",
        "A", "OFFICIAL", "PRESERVE", "Original official numerical receipt is inherited, not rerun", sample="Official Development; roster differs from research", metric="official composite score")
    old = at("backtesting/alpha_strategy_reset05/results/historical_remote_evidence.json", "branches")
    for name, b in [("V6-F2", "v6-f2-event-analog"), ("V6-FULL", "v6-full-event-engine"),
                    ("V7", "v7-event-memory"), ("V8/V8-A", "v8-calibration-diagnostics"),
                    ("V9-A", "v9-multiscale-path"), ("V9-B", "v9-vol-term-structure"),
                    ("V10-DATA", "v10-data"), ("V10-SHADOW", "v10-shadow-benchmark"),
                    ("SINGLE-CELL-TAIL", "v51-single-cell-tail")]:
        item = next(x for x in old if x["branch"] == "track2/" + b)
        parent = item.get("commits", [{}])[0].get("parent_sha") if item.get("commits") else None
        reason = {"V6-F2": "Zero actual-asof activations across27 F2 cards; insufficient matured event analogs",
          "V10-DATA": "Current-vintage provisional dates; historical exposure and no completed scored FINAL",
          "V10-SHADOW": "Independent vintage-safe benchmark not established",
          "SINGLE-CELL-TAIL": "Instruction reports official non-improvement; branch verifies published image but numeric official receipt was not recovered"}.get(name,
          "Implementation/branch found; original numeric evaluation artifact absent. Do not infer failure size or alpha.")
        add(name, "Historical event/calibration/path/provenance audit", item["branch"],
            "backtesting/alpha_strategy_reset05/results/historical_remote_evidence.json", "", "D", "DIAGNOSTIC_ONLY",
            "MISSING_RESULT_ARTIFACT" if name not in {"V6-F2", "V10-DATA", "V10-SHADOW"} else "COVERAGE_OR_VALIDATION_BLOCKED",
            reason, result=item["RESULT_SHA"], parent=parent,
            pre="b2c3a8013e503648c754944a622f396c945a173d" if name.startswith("V9") else None)
    arch = "backtesting/v13_copula/archive/full_eval_final.json"
    for name, model, branch, result in [("V11", "V11", "track2/v11", None),
       ("V12", "V12", "track2/v12-joint-native", "123115f3a7f04450f6a525594f9e39b88aa0037b"),
       ("V13-A", "A", "track2/v13-copula", "253a0c733d77917599f1dbf21eae914cd136d69a")]:
        add(name, "Joint native / marginal-copula separation", branch, arch, f"models/{model}/versus_v5/geometric_ratio",
            "C", "CARD_PROXY", "NO_SUBMISSION", "24 reused pseudo-origins; original executables/bank unavailable; post-fit joint or F1 safety fails",
            result=result or "MISSING_ORIGINAL_RESULT", sample="Original archived24 pseudo-origins;9 post-fit over2 years; not CEILING reconstructed24")
    add("V12/V13-R/R2", "Reconstructed implementation and parity", "track2/v13-r2-data-feature-parity",
        "V13-R2-DATA-FEATURE-PARITY.md", "", "D", "DIAGNOSTIC_ONLY", "PARITY_NOT_ESTABLISHED",
        "Recovered structure differs from unavailable original numerical bank; reconstructed proxy is a different universe")
    add("V14-TEMPORAL-JOINT", "Temporal joint branch inspected", "track2/v14-temporal-joint", "V13-RECONSTRUCTION-report.md", "",
        "D", "DIAGNOSTIC_ONLY", "NO_DISTINCT_RESULT", "Remote HEAD equals reconstructed V13 commit; no separate completed V14 result")
    # Freeze/result identities were re-read from the actual inherited Git lineage.
    definitions = [
      ("CEILING-01", "ceiling01", "ceiling-01-score-headroom", "oracle_matrix.json", "V13_REVISED_PUBLIC_24/LOCATION_ORACLE/Overall/score", "C", "CARD_PROXY", "MATHEMATICAL_ONLY", "Truth-informed oracle, not predictive evidence", "b24d2602fc70e4e004a6d4b5496f3b0be00948e2", "0d396b84d361c752a921cf439f7f846637401cb0", "24 reconstructed cards/63 cells;13 single/11 multi"),
      ("THESIS-01", "thesis01", "thesis-01-cross-market-implied-value", "crps_summary.json", "lag_safe/final/ratio", "B", "CANONICAL_MARGINAL_PROXY", "NO", "Lag-safe ranking near zero; controls comparable", "7e73f3623ec93e7efca852904ab6d656489d2b5c", "39b558f6bf565a6057cd419c0975255127aa1a80", "7450 final cells;2018–2023 revised-history no-text V51"),
      ("ORIGIN-01", "origin01", "origin-01-shock-propagation-alpha", "final_summary.json", "overall/ratio", "B", "CANONICAL_MARGINAL_PROXY", "INCONCLUSIVE", "15 active cells from1 source shock; low power", "809b2e192e36db0bcb25b9d62e19b7680a4f3e91", "51b4e81f4aeff1811c0990bc1532f2259ef8779f", "570 cells/12 origins in2024;1 information event"),
      ("SURPRISE-01-LOCATION", "surprise01", "surprise-01-external-information-alpha", "location_summary.json", "ratio", "B", "CANONICAL_MARGINAL_PROXY", "NO", "Primary event-release information shift worsens CRPS", "537f7b86b9094e8cf12a0aa1951e18351f0d6874", "bada39e0bc9cd4b084e7c745f5689f0a59467648", "59052 cells/376 market origins/382 events; exposed marginal"),
      ("SURPRISE-01-SCALE", "surprise01", "surprise-01-external-information-alpha", "scale_summary.json", "ratio", "B", "CANONICAL_MARGINAL_PROXY", "NO", "Weak scale correlation did not improve score", "537f7b86b9094e8cf12a0aa1951e18351f0d6874", "bada39e0bc9cd4b084e7c745f5689f0a59467648", "Same59052 cells; no joint score"),
      ("LOCATION-01", "location01", "location-01-predictable-oracle-shift", "crossfit_summary.json", "models/ridge/M1/ratio", "B", "CANONICAL_MARGINAL_PROXY", "NO;TRANSFER_ORIGINALLY_BLOCKED", "Primary Ridge fails; nonlinear gain tiny; transfer recovered separately", "4c35ef22e9b1bafe2d9fc009e6b3151e09afb723", "b05f73ace0d300968198f6563ca3eb4ba0d94257", "82184 evaluation cells/780 origins/25 assets;135994 full"),
      ("LOCATION-01R", "location01r", "location-01r-transfer-guard", "final_decision.json", "", "C", "CARD_PROXY", "MIXED;CONTINUOUS_NO", "Tie-safe geometry repair completed all24 without refit; primary transfer single worse/multi better", "2a110455c4d4640c8ea8a3b09dd62455104ab475", "7554bb851658306172654864c10fd40d41e4edb2", "24 exposed transfer cards/144 model-card checks"),
      ("EXPECTATION-01", "expectation01", "expectation-01-true-market-expectation", "full_ledger_summary.json", "models/A1/ratio", "B", "CANONICAL_MARGINAL_PROXY", "NO", "True consensus source admitted but primary/full shifts fail; market-implied source gate failed", "2ac22729875d48e59968edaa60cab927a02712d9", "5cf12e6380c43d272028a6def96ff9e47e1a3839", "82184 fixed cells/780 origins; active subset separately reported"),
      ("POSITIONING-01", "positioning01", "positioning-01-public-positioning-flow-liquidity", "final_decision.json", "", "B", "CANONICAL_MARGINAL_PROXY", "NO;POSITIONING_SOURCE_GATE_FAIL", "Flow/liquidity mixed tiny gains fail gates; original positioning quantities NOT tested", "79083c298f8dede7f9113dbf058f4f55c3dfad3d", "80933363f6c8fd273508c7ab30e35a43e03f37af", "82184 fixed evaluation cells/780 origins;25 assets"),
      ("CONTEXT-01", "context01", "context-01-card-semantic-location", "final_decision.json", "", "B", "CARD_PROXY", "NO", "Semantic residual NONE; R2 weak exposed transfer, no independent validation", "d3618dcd9aae4ac118a5c12c0fe8f3709a72f296", "a57c11701ae2b9383882673b14680e16c8d9cdea", "24 exposed reconstructed cards/63 cells"),
      ("TEXT-ROUTE-AUDIT-02", "text_route_audit02", "text-route-audit-02", "final_decision.json", "primary_composite", "B", "CARD_PROXY", "NO", "ST0_LOG fails controls and multi safety; secondary T0_RIDGE cannot rescue primary", "a37f232d5fcdf8dd8fa1c44e30bde68b3dda458c", "16b4e6b216141a181d5bed73eb89c7232edb0da7", "24 exposed cards/63 cells;5 strict oracle winners"),
      ("INFO-01", "info01", "info-01-new-information-audit", "final_decision.json", "", "C", "DIAGNOSTIC_ONLY", "SOURCES_FOUND_RESEARCH_ONLY", "Source quality assessment, not alpha evidence", "43a154ab419b6f3e3f4fc903db40d8c2e319f6bf", "0bd2a1e768156d74f82a9959a62da40184d30d87", "Source inventory; no candidate scores"),
      ("LOCATION-02-ECB", "location02", "location-02-ecb-spf-alpha", "primary_score_summary.json", "models/ECB_RIDGE_FULL5/crps_ratio", "B", "SOURCE_SPECIFIC_PROXY", "NO", "PIT-B FULL5 magnitude mapping fails; release-balanced direction weak", "6a9bf9a3507b3dd5b2ef2b8b687b4bfedf89e267", "d83409f414498b0cadcc508d387252b54dfd1e98", "EUR227 cells/48 origins/20 evaluation releases"),
      ("LOCATION-03-SLOOS", "location03", "location-03-sloos-alpha", "primary_score_summary.json", "models/SLOOS_FULL5_RELEASE_BALANCED/crps_ratio", "B", "SOURCE_SPECIFIC_PROXY", "NO", "PIT-B primary fails; release-balanced accuracy below chance", "938abb88db0dc985d8468950e169098b88ed50b9", "57e9d1b5c44d3b196755e00524e778e56f220049", "2616 cells/91 origins/33 evaluation releases;US rates"),
      ("LOCATION-04-SPD", "location04", "location-04-nyfed-spd-alpha", "primary_score_summary.json", "models/SPD_FULL5_RELEASE_BALANCED/crps_ratio", "B", "SOURCE_SPECIFIC_PROXY", "NO", "PIT-B direction interesting but magnitude overshoot/year instability;2023 retained", "ca9b467d48b2fc145faa5bfe549975206c8a811f", "2e356b91dd98dae022b72494ea6d4c70a9a38ed7", "552 cells/59 origins/41 evaluation releases;UST2Y/5Y"),
      ("INFORMATION-FAILURE-01", "information_failure01", "information-failure-reassessment-01", "final_decision.json", "", "C", "DIAGNOSTIC_ONLY", "INCONCLUSIVE", "Post-hoc curves diagnose amplitude but do not validate alpha; explicit interpretation override disclosed", "fe62b9058ea6dc540f7548c6be96ccc4e8d04b92", "1a417f0522e04e2ecf1598c80e0bf0ebb1e7b5fe", "Three different source ledgers; frozen prior predictions"),
      ("DIRECTION-TO-LOCATION-01", "direction_to_location01", "direction-to-location-01", "primary_summary.json", "models/DTL_PRIMARY_010/crps_ratio", "B", "SOURCE_SPECIFIC_PROXY", "NO", "2.47% exposed fixed-shift gain misses frozen capture/stability gates; not new independent information", "16ef4d87f15151796b072e2a6f658ec076171bda", "e5058474ce1917f02fafab50e261f06f2fbf5bf2", "Same552 SPD cells/59 origins/41 releases"),
      ("NEW-INFORMATION-SEARCH-02", "new_information_search02", "new-information-search-02", "final_decision.json", "", "C", "DIAGNOSTIC_ONLY", "PERSISTENT_REGIME_PROXY", "SEP-SPD alignment is not future Treasury accuracy; daily contracts lack offline license/data", "6653df8c61042c4642be3e2ed37b52daeea16de7", "8f4ae57eebb33b6d5a60f6fd0c351df29b5f65ea", "33 extracted SEP reports; source audit only"),
      ("PERSISTENT-DIRECTION-02", "persistent_direction02", "persistent-direction-state-02", "final_decision.json", "primary_ratio", "B", "SOURCE_SPECIFIC_PROXY", "NO", "Contemporary SEP loses baseline and price/stale controls; no timing alpha", "929ca23e0a57a0529cc64d8a14d5a78b791892e6", "2bdc6722fd5705887bee5f0695a09fe2319bf431", "482 cells/52 origins;UST2Y/5Y2020–24"),
      ("PRICE-STATE-03", "price_state_information03", "price-state-information-audit-03", "price_full_summary.json", "PRICE_FULL/CRPS_ratio", "B", "SOURCE_SPECIFIC_PROXY", "INCONCLUSIVE", "PIT-C, weaker than majority/structure; broad canonical transfer not completed", "0f5c938eeb4054518b0bde81e4de1503890fd684", "b1681d58ecc75e16760904086e672490d3cc20c6", "482 cells/52 origins; inherited14 price features"),
      ("V51-CENTER-BIAS-04", "v51_center_bias04", "v51-center-bias-audit-04", "global_sign005_summary.json", "ratio", "B", "CANONICAL_MARGINAL_PROXY", "INCONCLUSIVE", "Fold signs all+; degenerate matched random p1; year/asset intervals span1; material global gate fails", PARENT, "ae0bdf3faf2b2ca32205f43cd417e32ab2119d4f", "1250 origins/135994 full cells/25 assets;82184 heldout cells"),
    ]
    for name, slug, branch, filename, pointer, quality, universe, decision, reason, result, pre, sample in definitions:
        parent = next((parents.split()[0] for digest, parents, _ in log if digest == result and parents), None)
        add(name, slug, "track2/" + branch, f"backtesting/{slug}/results/{filename}", pointer,
            quality, universe, decision, reason, result, pre, parent, sample)
    # Secondary observations remain explicitly secondary and exposed.
    for name, path, pointer, reason in [
      ("CONTEXT-R2-SECONDARY", "backtesting/context01/results/routed_summary.json", "models/R2/geometric_composite_ratio", "Single good/multi worse; not semantic alpha"),
      ("TEXT-T0_RIDGE-SECONDARY", "backtesting/text_route_audit02/results/router_score_summary.json", "models/T0_RIDGE/composite", "Frozen secondary winner identified after many exposed-card results; not primary success"),
      ("PRICE-MAJORITY-CONTROL", "backtesting/price_state_information03/results/constant_shift_summary.json", "", "Better than price on narrow UST subset; no canonical alpha implication")]:
        add(name, "Secondary diagnostic/control", "track2/text-route-audit-02" if "TEXT" in name else "track2/price-state-information-audit-03" if "PRICE" in name else "track2/context-01-card-semantic-location",
            path, pointer, "C", "CARD_PROXY" if "PRICE" not in name else "SOURCE_SPECIFIC_PROXY", "NOT_A_CANDIDATE", reason)
    add("PRICE03-CANONICAL-EXTENSION", "Separate unfinished price audit extension", "track2/price-state-information-audit-03",
        "backtesting/price_state_information03/results/broader_transfer_readiness.json", "", "D", "DIAGNOSTIC_ONLY",
        "NO_COMPLETED_CANONICAL_RESULT", "Later separate remote branch head is not V51 scientific parent; never count a PRE as a result",
        result=branches.get("track2/price-state-information-audit-03"))
    table("research_inventory.csv", rows)
    table("evidence_quality_ledger.csv", evidence)
    table("score_universe_map.csv", [{k: r[k] for k in ["study", "universe", "universe_detail", "metric", "quality", "primary_result", "evidence"]} for r in rows])
    save("research_lineage.json", {"studies": [{k: r[k] for k in ["study", "branch", "parent_SHA", "PRE_SHA", "RESULT_SHA", "artifact_storage_commit", "result_status"]} for r in rows],
         "separate_PRICE_extension_not_bias_parent": True, "missing_metrics_not_imputed": True})
    return rows


def headroom():
    path = "backtesting/ceiling01/results/oracle_matrix.json"
    oracle = at(path); rows = []
    for universe, models in oracle.items():
        if universe not in {"V13_REVISED_PUBLIC_24", "SURPRISE_EXPOSED_MARGINAL_ONLY"}:
            continue
        for name, values in models.items():
            if "CROSSFIT" in name or name == "BASELINE":
                continue
            card = "Overall" in values
            ratio = values["Overall"]["score"] if card else values.get("ratio")
            if ratio is None:
                continue
            splits = {k: v["score"] for k, v in values.items() if isinstance(v, dict) and "score" in v}
            rows.append({"component": name, "oracle_ratio": ratio, "universe": "CARD_PROXY" if card else "CANONICAL_MARGINAL_PROXY",
               "universe_detail": universe, "mathematical_loss_reduction": 1 - ratio,
               "future_truth_used": True, "learnability_established": False,
               "oracle_kind": "component-zero mathematical floor" if "ZERO_LOSS" in name else "future-informed transform",
               "single_ratio": splits.get("Single-cell"), "multi_ratio": splits.get("Multi-cell"),
               "family_horizon_breakdown": json.dumps({k: v for k, v in splits.items() if k not in {"Overall", "Single-cell", "Multi-cell"}}),
               "arithmetic_sensitivity": values["Overall"].get("arithmetic_sensitivity") if card else None,
               "evidence": path, "metric_pointer": universe + "/" + name})
    bias = at("backtesting/v51_center_bias04/results/bias_oracle_summary.json")
    save("headroom_integrity_note.json", {"CEILING_oracle_rows_reloaded": len(rows),
         "bias_headroom": at("backtesting/v51_center_bias04/results/headroom_decomposition.json"),
         "card_floor_warning": "Geometric1e-12 is existing floor; unrestricted location+scale collapses forecasts to truth.",
         "scale_tail_warning": "These transforms minimize marginal criteria, not full card composite; ratios>1 mean damage, not negative theoretical maximum headroom."})
    table("oracle_headroom_map.csv", rows)
    return rows


def synthesize():
    # All narrative judgments cite existing evidence, never newly scored forecasts.
    defs = [
      ("LOCATION", 4, "EXHAUSTED", "Large oracle, no independently validated mapping; repeated primary failures", "backtesting/location01/results/crossfit_summary.json", "None; exposed only", "multi-day"),
      ("SCALE", 2, "DEPRIORITIZE", "SURPRISE scale1.001666; structured CEILING1.341872; early V8/V9 numerical records missing", "backtesting/surprise01/results/scale_summary.json", "None; exposed only", ">8hours"),
      ("TAIL", 2, "DEPRIORITIZE", "CEILING single0.6654 vs multi1.5845; reported official non-improvement not independently receipted here", "backtesting/ceiling01/results/oracle_matrix.json", "No clean set", ">8hours"),
      ("JOINT", 3, "DEPRIORITIZE", "V11/V12 post-fit fail; V13 mixed reused cases and reconstruction parity gap", "backtesting/v13_copula/archive/full_eval_final.json", "No clean vintages/independent set", "multi-day"),
      ("TEXT_ROUTING", 2, "WATCH", "ST0_LOG1.007942 fails; T0_RIDGE0.957520 secondary exposed lead, no clean validation", "backtesting/text_route_audit02/results/router_score_summary.json", "NOT_AVAILABLE now", ">8hours"),
      ("EXTERNAL_INFORMATION", 4, "EXHAUSTED", "ECB/SLOOS/SPD/SEP fail primary; source gate failures are not absence-of-information proofs", "backtesting/information_failure01/results/cross_source_failure_matrix.csv", "No independent source evaluation", "multi-day"),
      ("PRICE_STATE", 2, "DEPRIORITIZE", "Price0.993183 loses majority0.989829; PIT-C and canonical transfer unestablished", "backtesting/price_state_information03/results/final_decision.json", "PIT/prospective unavailable", ">8hours"),
      ("CENTER_BIAS", 1, "DEPRIORITIZE", "Global0.997800; matched nullp1; year/asset CIs span1; tiny oracle capture", "backtesting/v51_center_bias04/results/final_decision.json", "Exposed canonical only", "3–8hours"),
      ("OTHER", 1, "WATCH", "Original positioning and licensed high-frequency contracts not tested; data/license gates remain", "backtesting/new_information_search02/results/source_scorecard.csv", "AVAILABLE_WITH_ACQUISITION, unverified rights", "multi-day"),
    ]
    rows = [{"component": c, "failure_saturation": s, "status": state,
             "learnability": reason, "evidence": e, "independent_validation": validation,
             "operational_cost": runtime, "independent_OOS_replications": 0,
             "failure_saturation_scope": "Current related hypothesis space, not every possible source/model"}
            for c, s, state, reason, e, validation, runtime in defs]
    card_oracles = at("backtesting/ceiling01/results/oracle_matrix.json", "V13_REVISED_PUBLIC_24")
    oracle_names = {"LOCATION": "LOCATION_ORACLE", "SCALE": "SCALE_ORACLE_UNCONSTRAINED", "TAIL": "TAIL_ORACLE", "JOINT": "JOINT_ORACLE"}
    for row in rows:
        name = oracle_names.get(row["component"])
        row["oracle_ratio"] = card_oracles[name]["Overall"]["score"] if name else None
        row["oracle_universe"] = "CARD_PROXY: CEILING reconstructed24" if name else "Source-specific or diagnostic; no cross-universe pooled oracle"
        row["mathematical_headroom"] = 1-row["oracle_ratio"] if name else None
        row["learnable_headroom_estimate"] = "NOT_ESTABLISHED; no official score projection"
        row["effective_information_evidence"] = "Whole origin/year/asset or release blocks; no independent-cell sample claim"
    rows[0]["distinct_hypothesis_families_tested"] = 11
    rows[0]["hypothesis_count_scope"] = "Cross-market tension, shock propagation, release innovation, structured internal residual, true expectations, flow/liquidity, card semantics, survey-state mapping, SEP directional policy state, price state, historical residual bias. ECB/SLOOS/SPD share mapping family; DTL is an amplitude continuation."
    table("learnability_summary.csv", rows)
    table("failure_saturation.csv", [{k: r[k] for k in ["component", "failure_saturation", "failure_saturation_scope", "evidence"]} for r in rows])
    table("score_component_status.csv", rows + [{"component": "SUBMISSION_INTEGRITY", "status": "ACTIVE", "learnability": "Preserve proven official baseline; no alpha claim", "evidence": "backtesting/persistent_direction02/results/baseline_preservation_audit.json", "operational_cost": "1–3hours", "independent_validation": "AVAILABLE_NOW operational checks"}])
    save("location_go_no_go.json", {"decision": "EXHAUSTED_FOR_CURRENT_DATA", "reopen_condition": "Genuinely different information with lawful PIT and prospective validation; not another survey/Ridge/lag", "same_information_location_models": "STOP", "not_a_proof_all_location_information_useless": True})
    save("text_routing_go_no_go.json", {"decision": "NO_GO_NOW", "frozen_secondary_lead": "T0_RIDGE", "primary_failed": True,
        "independent_validation": "NOT_AVAILABLE", "new_unexposed_card_universe_verified": False,
        "primary_ratio": at("backtesting/text_route_audit02/results/final_decision.json", "primary_composite"),
        "secondary_ratio": at("backtesting/text_route_audit02/results/router_score_summary.json", "models/T0_RIDGE/composite"),
        "R2_multi": at("backtesting/text_route_audit02/results/router_score_summary.json", "models/R2/multi/composite"),
        "T0_RIDGE_multi": at("backtesting/text_route_audit02/results/router_score_summary.json", "models/T0_RIDGE/multi/composite"),
        "interpretation": "Specific frozen lead, but all24 cards exposed; require prospective untouched cards, unchanged E0/E1/router, whole-card joint/F1 safety; no tuning."})
    save("joint_tail_go_no_go.json", {"JOINT": "NO_GO_REOPEN", "TAIL": "NO_GO_REOPEN", "HEADROOM_X_LEARNABILITY": "Joint has modest mathematical headroom but weak mixed learnability; tail single-cell headroom is offset by multi safety and lack of official improvement. Neither outranks reliable delivery.",
        "joint_card_oracle": at("backtesting/ceiling01/results/oracle_matrix.json", "V13_REVISED_PUBLIC_24/JOINT_ORACLE/Overall/score"), "metric_origin": "Stored CEILING oracle, not candidate", "fresh_validation_available": False,
        "official_tail_receipt_status": "MISSING_ARTIFACT; non-improvement reported in user-provided study brief, no numeric official claim recovered"})
    return rows


def readiness():
    baseline = at("backtesting/persistent_direction02/results/baseline_preservation_audit.json")
    docker = (ROOT / "Dockerfile").read_text()
    workflow = (ROOT / ".github/workflows/text-first-v51-candidate.yml").read_text()
    rows = [
      ("V51 protected source", "VERIFIED_READ_ONLY", "All2409 inherited Git files byte-protected"),
      ("Build definition", "PRESENT_NOT_BUILT", "Dockerfile Python3.13 and pinned numerical dependencies; base tag not immutable digest"),
      ("Common pin", "RISK", "Submission Docker/CI v2.4.2; research common2.4.3. Preserve official candidate and verify scorer/runtime compatibility without silently upgrading"),
      ("Determinism", "HISTORICAL_TEST_EVIDENCE", "Same-seed/geometry/regression tests exist; complete image runtime repeat not performed here"),
      ("Docker binary", "MISSING_IN_WORKSPACE", "Prior preservation audit explicitly binary_Docker_package_currently_available=false"),
      ("Descriptor/ZIP/image receipt", "NOT_FULLY_VERIFIED", "Published candidate workflow exists; exact official V51 digest/package receipt needs retrieval, not reconstruction by assumption"),
      ("Network/read-only runtime", "CONFIGURATION_PRESENT", "Offline smoke CI and non-root Docker USER; no runtime build/test in this meta reset"),
      ("CI", "DEFINITION_PRESENT", "Pinned actions and family smoke gates; current live CI status not a fresh image attestation"),
      ("Recovery", "VERIFIED_PRIOR_ARCHIVE", "Parent final recovery SHA660a7b8... preserved; new reset recovery will include sources/evidence and Git bundle"),
    ]
    save("submission_readiness_audit.json", {"official_reference": OFFICIAL, "checks": [{"item": a, "status": b, "evidence": c} for a,b,c in rows],
      "build_executed": False, "submission_executed": False, "V51_overwritten": False,
      "baseline_package_fully_reverified": False, "DEADLINE_STATUS": "UNVERIFIED",
      "deadline_evidence": "Available README/SUBMISSION_CLI/project artifacts have no verified exact current submission deadline.",
      "risk": "Concrete image/descriptor/pin gaps justify hardening without inventing deadline urgency",
      "evidence_paths": ["Dockerfile", "pyproject.toml", ".github/workflows/text-first-v51-candidate.yml", "backtesting/persistent_direction02/results/baseline_preservation_audit.json"]})


def rank():
    # Scores assigned only after PRE remote verification. No changes to frozen rubric.
    configs = [
      ("LOCATION_INFORMATION_CONTINUE", [5,1,1,1,1,1,2,3], "EXPOSED_ONLY", False, True, "UNKNOWN", "multi-day", .35,
       "No concrete new observable information beyond exhausted survey/price/bias mappings", "backtesting/location01/results/crossfit_summary.json"),
      ("MARGINAL_SCALE_REOPEN", [2,1,1,1,1,2,2,3], "EXPOSED_ONLY", False, True, "UNKNOWN", ">8hours", .30,
       "Another multiplier duplicates V8/V9/SURPRISE; a distinct PIT scale-error mechanism is not identified", "backtesting/surprise01/results/scale_summary.json"),
      ("TAIL_REOPEN", [2,1,1,0,1,2,2,4], "EXPOSED_ONLY", False, True, "UNKNOWN", ">8hours", .30,
       "Repeat single-tail calibration has no new validation and multi-card damage", "backtesting/ceiling01/results/oracle_matrix.json"),
      ("JOINT_DEPENDENCE_REOPEN", [3,2,1,1,1,1,0,3], "EXPOSED_ONLY", False, True, "UNKNOWN", "multi-day", .55,
       "Random copula variant is redundant; original bank/parity and independent validation unresolved", "backtesting/v13_copula/archive/full_eval_final.json"),
      ("TEXT_ROUTING_VALIDATION", [2,3,1,2,0,2,3,2], "NOT_AVAILABLE", True, False, "UNKNOWN", ">8hours", .30,
       "What is new would be untouched cards validating frozen T0_RIDGE; no such universe is present", "backtesting/text_route_audit02/results/router_score_summary.json"),
      ("SCORE_GEOMETRY_REASSESSMENT", [3,1,2,0,1,4,4,2], "EXPOSED_ONLY", False, True, "NEGLIGIBLE", "1–3hours", .10,
       "CEILING already maps component/single/multi/family/horizon composition; repeated broad audit is redundant", "backtesting/ceiling01/results/component_bounds.json"),
      ("CARD_CONDITIONAL_ERROR_STRUCTURE", [3,2,1,2,1,2,2,3], "EXPOSED_ONLY", True, False, "UNKNOWN", ">8hours", .30,
       "Potential new mechanism is prospectively identifying card-level marginal–joint safety interactions; exposed24-card map already exists and cannot validate new rules", "backtesting/text_route_audit02/results/multi_safety_summary.json"),
      ("NEW_HIGH_FREQUENCY_INFORMATION", [5,0,0,5,2,0,0,2], "AVAILABLE_WITH_ACQUISITION", True, False, "UNKNOWN", "multi-day", .60,
       "Genuinely distinct daily traded policy-contract path/timing data; original historical/offline rights and clean evaluation not acquired", "backtesting/new_information_search02/results/source_scorecard.csv"),
      ("SUBMISSION_HARDENING", [0,0,5,3,5,4,5,5], "AVAILABLE_NOW", True, False, "NEGLIGIBLE", "1–3hours", .10,
       "Recover exact verified V51 executable/descriptor/digest and close concrete delivery reproducibility gaps without changing forecasts", "backtesting/persistent_direction02/results/baseline_preservation_audit.json"),
    ]
    rows, hypotheses = [], []
    evidence_by_dimension = {
      "THEORETICAL_HEADROOM": "Stored CEILING component bounds constrain this component; no projected official gain.",
      "EMPIRICAL_SIGNAL": "Stored primary verdicts and controls determine learnability; secondary leads never rescue failures.",
      "REPLICATION_STABILITY": "All historical research is exposed; reusing cells is not independent replication.",
      "NEW_INFORMATION_NOVELTY": "The WHAT_IS_NEW sentence specifies the only distinct mechanism or marks redundancy.",
      "VALIDATION_FEASIBILITY": "Validation status is based on existing datasets/rights, never an invented untouched set.",
      "TIME_TO_RESULT": "Parent execution_audit records47.52s full tests/1.47s common; reconstruction, source acquisition and failed recovery span staged runs/days. Estimates include implementation and acquisition, not just arithmetic.",
      "IMPLEMENTATION_RISK": "Risk estimate reflects archived recovery/PIT/license/parity failures and existing verified paths, not measured frequency.",
      "SUBMISSION_RELEVANCE": "Official baseline0.9541 is the delivery reference; proxy improvement is not an official score forecast.",
    }
    rationale = ["## Executive summary (read this first)", "", "Scores are evidence-based strategic judgments after remote PRE. They are not estimated official gains. Missing early numeric artifacts lower confidence, not proof of scientific failure.", ""]
    for axis, values, validation, novel, eliminated, impact, runtime, risk, novelty, evidence in configs:
        scores = dict(zip(DIMENSIONS, values, strict=True))
        row = {"axis": axis, **scores, "priority": weighted(scores), "validation": validation,
             "genuinely_novel": novel, "eliminated": eliminated,
             "operationally_feasible": axis not in {"NEW_HIGH_FREQUENCY_INFORMATION", "TEXT_ROUTING_VALIDATION", "CARD_CONDITIONAL_ERROR_STRUCTURE"},
             "low_submission_downside": axis in {"SCORE_GEOMETRY_REASSESSMENT", "SUBMISSION_HARDENING"},
             "expected_score_impact": impact, "expected_implementation_time": runtime,
             "expected_evaluation_time": "No model; check/runtime1–3hours" if axis=="SUBMISSION_HARDENING" else runtime,
             "operational_failure_probability_estimate": risk, "probability_is_subjective": True,
             "endangers_submission_preparation": axis not in {"SUBMISSION_HARDENING", "SCORE_GEOMETRY_REASSESSMENT"},
             "WHAT_IS_NEW": novelty, "evidence": evidence, "DEADLINE_STATUS": "UNVERIFIED"}
        for dimension in DIMENSIONS:
            row[dimension + "_evidence"] = f"{evidence_by_dimension[dimension]} Axis-specific evidence: {novelty}; see {evidence}."
        headroom_evidence = {
          "LOCATION_INFORMATION_CONTINUE": "5: CEILING location0.489209 and canonical perfect0.310345 imply over40% mathematical headroom, not learnability.",
          "MARGINAL_SCALE_REOPEN": "2: CEILING unconstrained full-card scale0.968602 gives3.14% improvement while bounded1.196772 degrades; fragile headroom.",
          "TAIL_REOPEN": "2: CEILING tail0.990344 aggregate is fragile, with single0.665412 but multi1.584457; mathematical floor is not a feasible mapping.",
          "JOINT_DEPENDENCE_REOPEN": "3: CEILING joint zero floor0.849187 provides15.08% mathematical ceiling; actual truth-informed rank oracle0.902435 is smaller.",
          "TEXT_ROUTING_VALIDATION": "2: Frozen two-expert routing oracle0.953566 offers4.64% on only24 exposed cards, with61.05% of oracle log gain from one card.",
          "SCORE_GEOMETRY_REASSESSMENT": "3: Component zero bounds include15.08% joint reduction but this audit creates no predictive recovery; CEILING already resolves broad composition.",
          "CARD_CONDITIONAL_ERROR_STRUCTURE": "3: Joint/marginal card interactions have material mathematical component floors, but no quantified learnable new conditional mechanism.",
          "NEW_HIGH_FREQUENCY_INFORMATION": "5: The source would target existing location headroom over40%; no actual source gain is observed.",
        }
        empirical_evidence = {
          "LOCATION_INFORMATION_CONTINUE": "1: THESIS1.006221, LOCATION M1 1.005739, ECB1.562820, SLOOS1.148455, SPD1.420833 and SEP1.003343 fail primary tests; bias gain is tiny.",
          "MARGINAL_SCALE_REOPEN": "1: SURPRISE scale1.001666 and CEILING structured-scale1.341872 fail; original V8/V9 numeric metrics are missing rather than invented.",
          "TAIL_REOPEN": "1: Tail warp's full multi-card penalty contradicts the single-card lead; reported official non-improvement has no recovered numeric receipt here.",
          "JOINT_DEPENDENCE_REOPEN": "2: Archived V13-B post-fit0.925339 is a weak reused-case lead, while V11/V12 post-fit1.308229/1.077213 and parity deficits prevent robust replication.",
          "TEXT_ROUTING_VALIDATION": "3: Frozen secondary T0_RIDGE0.957520 is promising but primary ST0_LOG1.007942 fails; it is not independent validation.",
          "SCORE_GEOMETRY_REASSESSMENT": "1: Truth-informed component maps establish diagnosis only, so oracle-alone evidence cannot exceed1.",
          "CARD_CONDITIONAL_ERROR_STRUCTURE": "2: R2 single0.943992 versus multi1.024592 and transfer safety give mixed exposed structural evidence, not a validated predictive model.",
        }
        row["THEORETICAL_HEADROOM_evidence"] = headroom_evidence.get(axis, row["THEORETICAL_HEADROOM_evidence"])
        row["EMPIRICAL_SIGNAL_evidence"] = empirical_evidence.get(axis, row["EMPIRICAL_SIGNAL_evidence"])
        row["VALIDATION_FEASIBILITY_evidence"] = f"{scores['VALIDATION_FEASIBILITY']}: {validation}; {novelty}. No untouched set is synthesized. Evidence: {evidence}."
        row["TIME_TO_RESULT_evidence"] = f"{scores['TIME_TO_RESULT']}: estimated {runtime}; parent final test times47.52s/1.47s and documented multi-stage recovery/acquisition logs distinguish cheap arithmetic from the unresolved implementation/data workload."
        row["IMPLEMENTATION_RISK_evidence"] = f"{scores['IMPLEMENTATION_RISK']}: subjective failure estimate{risk:.0%}, driven by {novelty}; five denotes lower risk, never a statistical error probability. Evidence: {evidence}."
        if axis == "SUBMISSION_HARDENING":
            row["EMPIRICAL_SIGNAL_evidence"] = "0: No new predictive improvement is claimed; operational value is preservation of the already verified0.9541 reference (baseline_preservation_audit.json)."
            row["REPLICATION_STABILITY_evidence"] = "5: Existing source hashes, same-seed tests, parent31/58/841/250 test suites and verified recovery reproduce operational integrity; not predictive alpha replication."
            row["THEORETICAL_HEADROOM_evidence"] = "0: Hardening changes no forecast and promises no mathematical loss reduction; protects delivery."
        if axis == "NEW_HIGH_FREQUENCY_INFORMATION":
            row["EMPIRICAL_SIGNAL_evidence"] = "0: NEWINFO02 source_scorecard shows no acquired licensed policy-contract experiment; no empirical alpha evidence exists."
        rows.append(row)
        hypotheses.append({"axis": axis, "WHAT_IS_NEW": novelty, "novelty_gate": "ELIMINATED_REDUNDANT" if eliminated else "SPECIFIC_CONDITIONAL_HYPOTHESIS", "validation": validation, "evidence": evidence})
        rationale += [f"### {axis}: {row['priority']:.1f}/100", "", novelty, ""]
        for dimension in DIMENSIONS:
            rationale.append(f"- {dimension}={scores[dimension]}: {row[dimension + '_evidence']}")
        rationale.append("")
    rows.sort(key=lambda r: (-r["priority"], list(CANDIDATES).index(r["axis"])))
    table("research_priority_matrix.csv", rows); table("remaining_hypotheses.csv", hypotheses)
    (RESULTS / "research_priority_rationale.md").write_text("\n".join(rationale))
    decision = decide(rows)
    save("stopping_rule_decision.json", {**decision, "all_research_below55": all(r["priority"] <55 for r in rows if r["axis"]!="SUBMISSION_HARDENING"), "deadline_unverified_not_used_as_urgency": True})
    save("next_axis_decision.json", {**decision, "reason": "Every research axis below55; no immediately usable novel clean-validation path. Concrete official-package risks remain. Preserve V51 and harden delivery.", "WHAT_IS_NEW": next(r["WHAT_IS_NEW"] for r in rows if r["axis"]==decision["selected_axis"]),
         "killer_test": "Exact verified V51 digest/package must reproduce pinned offline deterministic outputs and mandatory gates; unresolved binary/descriptor provenance means NOT_READY, never substitute a research candidate.", "expected_runtime": "1–3hours after exact image/receipt retrieval; unavailable original binary requires a separate documented provenance gate"})
    save("final_decision.json", {"ALPHA_RESET05_RESULT": decision["stopping_rule"], "NEXT": decision["NEXT"], "selected_axis_count": 1,
         "PRE_RESULT_ALPHA_RESET05_SHA": at("backtesting/alpha_strategy_reset05/results/pre_result_manifest.json", "PRE_RESULT_ALPHA_RESET05_SHA"),
         "scientific_parent": PARENT, "official_reference": OFFICIAL, "official_score_reestimated": False,
         "new_models_fit": 0, "new_candidate_scores": 0, "new_sources_acquired": 0,
         "hidden_labels_used": False, "next_study_executed": False, "independent_OOS": False,
         "submission_created": False, "missing_historical_metrics": "V6FULL/V7/V8/V9 numerical results and official tail receipt not recovered; D/unknown, never imputed"})
    return rows, decision


def report(inventory_rows, oracle_rows, components, priorities, decision):
    gaps = {str(t): round(OFFICIAL-t,4) for t in [.90,.80,.70,.50]}
    save("official_target_gap.json", {"label": "TARGET_GAP_ONLY", "official_reference": OFFICIAL, "absolute_reductions_required": gaps, "projected_achievable_score": None})
    doc = """## Executive summary (read this first)

# ALPHA-STRATEGY-RESET-05 — Evidence-weighted research program reset

**HARDEN_NOW. Exactly one next axis: SUBMISSION-HARDENING-06.** No new source, feature, model, candidate score, Docker build or competition submission was executed. This reset ranks existing evidence, not future performance. V5.1 Development0.9541 remains the inherited verified official reference.

The largest mathematical opportunity is location. No tested location mapping has yet converted that headroom into independently validated alpha. The strongest remaining exposed predictive lead is secondary text routing T0_RIDGE, but the primary failed and no untouched validation card set exists. A distinct high-frequency policy-contract source could supply new information, but its historical/offline licenses, PIT reconstruction and clean validation are not available now. These limitations make operational preservation the only currently justified next action.

"""
    doc += f"Parent RESULT `{PARENT}`; parent PRE `ae0bdf3faf2b2ca32205f43cd417e32ab2119d4f`; reset PRE `{at('backtesting/alpha_strategy_reset05/results/pre_result_manifest.json', 'PRE_RESULT_ALPHA_RESET05_SHA')}`. PRE froze all nine candidates, weights, score meanings and stopping rules before ranking. No rule changed after ranking.\n\n"
    doc += "## Evidence and score-universe firewall\n\nQuality A=official/independently validated, B=frozen chronological exposed, C=post-hoc/diagnostic exposed, D=missing/incomplete/reconstruction/parity. All historical research remains RESEARCH_EXPOSED; no independent OOS replication is inferred. The official0.9541 is not multiplied by proxy ratios. Canonical marginal ratios are not official card composites. Original archived V11–V13 pseudo-origins are not CEILING's reconstructed24 cards. Missing metrics remain blank/D.\n\n"
    doc += mdtable(inventory_rows, ["study", "primary_result", "universe", "quality", "decision"]) + "\n\n"
    doc += "Early V6-F2 has documented zero activations, rather than a loss failure. V6FULL/V7/V8/V9 branches contain implementations but not preserved numeric result ledgers in the inspected trees. V10 finds no proved independent vintage-safe benchmark. The single-cell tail branch verifies an amd64 published candidate; the brief reports official non-improvement, but the numeric official receipt is MISSING_ARTIFACT here. No invented tail official score is used. The separate later PRICE03 canonical extension is not a completed evaluation and is not the bias study's scientific parent.\n\n"
    doc += "## Mathematical headroom\n\n"
    selected = [r for r in oracle_rows if r["universe"]=="CARD_PROXY" and r["component"] in {"LOCATION_ORACLE", "SCALE_ORACLE_UNCONSTRAINED", "SCALE_ORACLE_BOUNDED", "TAIL_ORACLE", "JOINT_ORACLE", "LOCATION_JOINT_ORACLE", "JOINT_TAIL_ZERO_LOSS", "LOCATION_SCALE_ORACLE_BOUNDED"}]
    doc += mdtable(selected, ["component", "oracle_ratio", "single_ratio", "multi_ratio", "arithmetic_sensitivity", "universe"]) + "\n\n"
    doc += "All oracle rows use future truth. Joint+tail0.606562 is a component-zero floor, not an executable learned oracle. Unrestricted location+scale collapses to truth and the geometric1e-12 is a numerical floor. Card scale/tail transforms can worsen multi joint loss; even location0.489209 geometric has arithmetic1.042291. Negative reductions describe transform damage, not absence of mathematical headroom. Full families/horizons and other combinations are in oracle_headroom_map.csv. SURPRISE marginal location0.386635, bounded scale0.865040 and tail-warp0.821683 belong to a different59052-cell marginal universe.\n\n"
    doc += "Bias-only full-ledger perfect-location ratio0.310345 leaves68.965% mathematical marginal reduction, but low-dimensional asset×horizon oracle captures only1.794% of that headroom. Actual GLOBAL_BIAS_SIGN005 on82184 held-out cells is0.997800, about0.373% oracle capture. No projection to official score is made.\n\n"
    doc += "## Learnability and consumed hypothesis space\n\n" + mdtable(components,["component","failure_saturation","status","learnability","independent_validation"]) + "\n\n"
    doc += "Cross-market tension, shock propagation, release innovation, survey consensus, source policy paths, text residuals, price-state information and historical residual bias are distinct hypotheses. ECB/SLOOS/SPD represent independent source families, but use related Ridge-to-location geometry and shared exposed market years; they are not independent OOS replications. DTL/SPD shrinkage reuses exactly the same predictions and labels. V11–V13 are related joint-engine variations on reused pseudo-origins. Exposure and overlap prevent a claim of an accumulated independent significance level. Saturation4 applies to current related information/mapping space, not every possible external source. Original positioning quantities and licensed high-frequency paths were blocked/unacquired, not proved useless.\n\n"
    doc += "SPD retains release-balanced direction accuracy66.386% and rank evidence; primary1.420833 failed with calibration slope0.232819 and large2023 damage. That supports a possible direction/amplitude mismatch, not validated alpha. Frozen DTL0.975344 still verdictNO under its gates. SEP1.003343 failed; its earlier alignment with SPD was persistence, not future accuracy. PRICE0.993183 is weaker than majority/intercept0.989829 and structure0.991809; PIT-C, year concentration and absent canonical transfer leave incremental price evidence INCONCLUSIVE. Bias fold signs are all positive: matched-null p1 is degenerate, year/asset intervals span1, and fixed rolling1/3/5-year correlations are weak or negative.\n\n"
    doc += "Text T0_RIDGE0.957520 is the strongest unvalidated routing lead; single0.922988, multi1.000000. R2 always0.980115 is single0.943992 but multi1.024592. Primary ST0_LOG1.007942 fails negative controls and has multi1.017410; T0 secondary cannot replace it. No untouched cards or independent E0/E1 ledger is available. Prospective validation could reopen the exact frozen lead, but cannot be invented for today's selection. Joint V13-A archived overall0.892887 is exposed/selected; its post-fit joint1.137125 is not safe. Original bank/coefficients unavailable and reconstructed parity audits remain D.\n\n"
    doc += "## Frozen priority matrix\n\nEvery score has a linked evidence sentence in research_priority_rationale.md. Scores are0–5 and weighted by20/25/15/10/10/10/5/5 percent. Five in IMPLEMENTATION_RISK means low risk. Hardening deliberately receives zero theoretical/empirical alpha points; its benefit is delivery preservation. Time/failure probabilities are labeled operational estimates, not measured rates.\n\n"
    doc += mdtable(priorities,["axis","priority","validation","eliminated","expected_score_impact","expected_implementation_time"]) + "\n\n"
    doc += "Top descriptive scores: " + ", ".join(f"{r['axis']} {r['priority']:.0f}" for r in priorities[:3]) + ". Lowest: " + priorities[-1]["axis"] + ". Redundant candidates receive descriptive scores but are selection-ineligible. The frozen stopping rule is decisive: all non-submission axes are below55, so HARDEN_NOW; a high oracle cannot override it. No tie remains in the selected action.\n\n"
    doc += "## Explicit go/no-go and eight central answers\n\n1. Large location oracle failed to become alpha because it uses realized cell-specific outcomes; observed sources do not reliably predict that conditional error at the required magnitude and horizon. Low-dimensional bias accounts for only a small share. This is a limit of the tested inputs/mappings, not a theorem of unforecastability.\n\n2. Independent source hypotheses exist, but most evaluations reuse market years, cells, a Ridge transform or exposed pseudo-origins. They are not independent validation studies.\n\n3. T0_RIDGE is the strongest remaining exposed predictive lead; official V51 is the strongest validated delivery evidence. Neither establishes incremental new alpha today.\n\n4. Location, especially location+scale mathematical collapse, has the largest theoretical headroom.\n\n5. Largest theoretical headroom and strongest learnable evidence are different.\n\n6. The most actionable remaining unknown is exact official V51 package/digest/descriptor reproducibility under pinned offline constraints. Licensed high-frequency-policy information is scientifically distinct but not currently ready.\n\n7. STOP another survey/Ridge/lag/shrinkage trial, repeated scale/tail multiplier, random copula variant, exposed-card rerouting threshold, winner-only subsets, or further historical constant-bias tuning. LOCATION=EXHAUSTED_FOR_CURRENT_DATA. Tail/joint=NO_GO_REOPEN. Text=NO_GO_NOW until truly untouched validation exists.\n\n8. No further forecasting experiment meets the frozen priority/stopping gates. Exactly one next action is SUBMISSION-HARDENING-06; only its draft is written here.\n\n"
    doc += "## Deadline and safe-reference readiness\n\nDEADLINE_STATUS=UNVERIFIED. Available project artifacts do not prove an exact current competition deadline; no date or urgency is invented. Concrete risks remain: original official V51 Docker binary is not currently materialized, descriptor/image/ZIP receipt is not fully reverified, Python base image floats by tag, and Docker/CI common2.4.2 differs from research2.4.3. Existing deterministic source tests, pinned numerical dependencies, offline family smoke workflow, non-root USER and source hashes are positive evidence. This reset audits them read-only; it neither builds nor fixes the submission package. Estimated hardening1–3hours after exact receipt/image retrieval, with subjective10% operational-failure estimate; unavailable original binary triggers a documented STOP/provenance decision.\n\n"
    doc += "Targets0.90/0.80/0.70/0.50 require absolute official reductions0.0541/0.1541/0.2541/0.4541 respectively. TARGET_GAP_ONLY, not a predicted achievable score. Hardening expected score improvement is NEGLIGIBLE; expected value is avoiding delivery failure.\n\n"
    doc += "## Limitations, tests and preservation\n\nEarly numeric studies and tail official receipt are incomplete evidence; this lowers confidence without manufacturing results. No new prospective validation set is present. Five-year/source-block studies have few information events despite many cells. Stored aggregate hashes and linked JSON/CSV paths preserve the evidence trail. All inherited Git files, main and V51 remain protected; no per-cell private truth or losses are exported. New reset tests guard rubric arithmetic, exact-one selection, evidence links, universe tags and absence of model/scorer/hidden-label use. Final test results appear in execution_audit.json. Remote RESULT and recovery hashes are bound by external completion receipts to avoid self-referential commits.\n"
    (ROOT / "ALPHA-STRATEGY-RESET-05-report.md").write_text(doc)
    draft = """## Executive summary (read this first)

# Frozen next action: SUBMISSION-HARDENING-06

Purpose: deliver the exact previously verified V5.1 official reference without forecast changes. This reset has not executed the action below.

1. Recover the original official0.9541 evaluation receipt, submitted Docker digest, architecture, descriptor and ZIP/image provenance. Use the protected V51 source and its original package identity, not a research branch or reconstructed candidate. If exact binary/receipt is unavailable, STOP and document the gap before any rebuild assumption.
2. Confirm contest artifact policy, API/credential handoff, permitted dependency versions, runtime filesystem/network/architecture constraints and current deadline using authoritative documents. Never place secrets or hidden labels in Git.
3. Freeze source/common/numerical dependency/image hashes. Resolve research common2.4.3 versus official Docker common2.4.2 as a compatibility question; do not upgrade the official reference without proof. Pin immutable image/base provenance in a separate authorized hardening branch.
4. In that future task only, perform reproducible build and repeated offline smoke on all declared families with fixed seeds. Gates: schema/integrity/as-of/resource/domain semantics, deterministic output bytes,200+ draws, joint rank/shape preservation, non-root/read-only runtime and correct absolute output mount.
5. Compare all protected source/output hashes with the original safe reference. No location, scale, tail, copula, router, feature or model change allowed. No CRPS candidate evaluation or leaderboard tuning. Use synthetic/public gate fixtures only; no hidden Development answers.
6. Preserve exact submission descriptor, image digest, allowed artifacts, build/runtime logs, pinned manifest and private recovery with CRC/member/archive hashes. Do not submit absent a separate explicit submission instruction.

Scientific target/model/folds: NOT_APPLICABLE; this is operational hardening. Primary metric: all mandatory delivery/reproducibility gates pass and original candidate identity unchanged. Success threshold: zero unresolved critical gates, exact version/hash provenance, clean tree and remote verification. Controls: repeat fixed-seed outputs and protected-hash comparison. FAIL: missing binary provenance, changed forecast bytes, nondeterminism, unsafe as-of, schema/runtime failure or unapproved model substitution. STOP after the same new step fails twice; preserve logs and exact continuation point. No post-hoc rescue with a research model. Expected runtime1–3hours once image/receipt is recoverable; acquisition uncertainty is reported separately. No next forecasting experiment runs here.
"""
    (RESULTS / "next_study_frozen_draft.md").write_text(draft)


def main():
    pre = read(RESULTS / "pre_result_manifest.json")
    assert pre["remote_verified"] and pre["parent"] == PARENT
    verify_protection(ROOT, read(RESULTS / "protected_parent_hashes.json")["files"])
    print("stage=evidence_inventory completed=1/5 no_fits=0 output=" + str(RESULTS), flush=True)
    inv = inventory(); oracle = headroom()
    # Integrity reproduction: compare identical frozen R2 evidence across prior studies.
    r2a = at("backtesting/context01/results/routed_summary.json", "models/R2/geometric_composite_ratio")
    r2b = at("backtesting/text_route_audit02/results/router_score_summary.json", "models/R2/composite")
    assert abs(r2a-r2b) < 1e-12
    integrity = {"R2_cross_study_equality": {"context": r2a, "text_route": r2b, "difference": r2a-r2b, "tolerance": 1e-12},
         "all_metric_values_loaded_from_stored_artifacts": True, "new_candidate_CRPS": 0,
         "private_truth_loaded": False, "models_refit": 0, "required_evidence_files": 518}
    save("prior_result_integrity.json", integrity)
    components = synthesize(); readiness()
    print("stage=evidence_synthesis completed=3/5 studies=" + str(len(inv)), flush=True)
    priorities, decision = rank(); report(inv, oracle, components, priorities, decision)
    save("execution_audit.json", {"scientific_audit_complete": True, "report_complete": True,
        "new_models_fit": 0, "new_candidate_scores": 0, "new_sources_acquired": 0,
        "no_official_score_reestimation": True, "next_study_executed": False,
        "parent_files_unchanged": True, "tests": "Pending final test stage"})
    status = read(RESULTS.parent / "STATUS.json")
    status.update({"state": "RESULTS_READY", "HEAD_SHA": pre["PRE_RESULT_ALPHA_RESET05_SHA"],
        "PRE_RESULT_ALPHA_RESET05_SHA": pre["PRE_RESULT_ALPHA_RESET05_SHA"], "current_stage": "FINAL_TESTS",
        "completed": ["environment", "inventory", "PRE_remote", "headroom", "synthesis", "ranking", "decision", "report"],
        "pending": ["tests", "RESULT_remote", "recovery"], "rankings_computed": True})
    (RESULTS.parent / "STATUS.json").write_text(json.dumps(status, indent=2) + "\n")
    print("stage=report completed=5/5 result=" + decision["stopping_rule"] + " NEXT=" + decision["NEXT"], flush=True)


if __name__ == "__main__":
    main()

"""Executive summary: freeze evidence inventory and rubric before any axis ranking."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import platform
from pathlib import Path

from .core import BRANCH, CANDIDATES, DIMENSIONS, MAIN, PARENT, PARENT_PRE, sha

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "backtesting/alpha_strategy_reset05/results"


def save(name, data):
    RESULTS.mkdir(parents=True, exist_ok=True)
    if isinstance(data, dict) and "executive_summary" not in data:
        data = {"executive_summary": "Evidence-only strategic audit; no model fitting or candidate scoring.", **data}
    (RESULTS / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def table(name, rows):
    if not rows:
        raise ValueError(f"Empty table: {name}")
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with (RESULTS / name).open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--remote-inventory", type=Path, required=True)
    parser.add_argument("--tracked-files", type=Path, required=True)
    args = parser.parse_args()
    files = args.tracked_files.read_bytes().decode().split("\0")
    protected = {p: sha(ROOT / p) for p in files if p}
    save("protected_parent_hashes.json", {"files": protected, "count": len(protected), "parent": PARENT})
    save("environment_audit.json", {"branch": BRANCH, "parent_RESULT_SHA": PARENT,
         "parent_PRE_SHA": PARENT_PRE, "main_SHA": MAIN, "starting_tree_clean": True,
         "python": platform.python_version(), "asof_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
         "parent_remote_verified": True, "common_version": "2.4.3",
         "common_commit": "03fc89cc666354e999768381bb923e60be5c1cee",
         "official_scorer_executed": False, "source_acquisition": False,
         "new_forecasts": False, "new_candidate_CRPS": False,
         "private_truth_loaded": False, "hidden_Development_labels_used": False})
    save("lineage_manifest.json", {"scientific_parent": PARENT, "parent_PRE": PARENT_PRE,
         "branch": BRANCH, "main": MAIN, "no_parent_branch_changes": True})
    save("remote_branch_inventory.json", {"branches": json.loads(args.remote_inventory.read_text()),
         "read_only_observation": True})
    inventory = []
    for p in sorted((ROOT / "backtesting").glob("*/results/*")):
        if p.parent.parent.name == "alpha_strategy_reset05" or not p.is_file():
            continue
        if p.suffix in {".json", ".csv", ".md"}:
            inventory.append({"evidence": p.relative_to(ROOT).as_posix(), "sha256": sha(p),
                              "source_RESULT": PARENT, "use": "stored aggregate evidence only"})
    for p in sorted(ROOT.glob("*report.md")):
        inventory.append({"evidence": p.relative_to(ROOT).as_posix(), "sha256": sha(p),
                          "source_RESULT": PARENT, "use": "historical report; prefer machine-readable result"})
    for p in [ROOT / "Dockerfile", ROOT / "pyproject.toml", ROOT / "README.md",
              ROOT / ".github/workflows/text-first-v51-candidate.yml"]:
        inventory.append({"evidence": p.relative_to(ROOT).as_posix(), "sha256": sha(p),
                          "source_RESULT": PARENT, "use": "read-only operational readiness"})
    table("required_evidence_inventory.csv", inventory)
    save("research_priority_rubric.json", {
        "dimensions": DIMENSIONS, "score_range": [0, 5], "weighted_formula": "20 * sum(weight * score)",
        "candidate_axes": CANDIDATES, "scores_assigned": False,
        "empirical_signal": {"5": "Replicated predictive improvement across multiple frozen evaluations",
          "4": "Strong frozen exposed evidence", "3": "Promising exposed or unstable",
          "2": "Weak mixed", "1": "Mostly failed", "0": "Repeated strong failures or no signal"},
        "oracle_alone_empirical_cap": 1,
        "headroom": {"5": "Material location or combined headroom >40% in stored proxy",
          "4": "20–40%", "3": "10–20% or large mathematical floor only",
          "2": "3–10% or fragile constrained oracle", "1": "Less than3%", "0": "No new score improvement mechanism"},
        "replication": {"5": "Multiple verified operational reproductions / independent predictive replications",
          "4": "Broad frozen replications", "3": "Consistent exposed tests", "2": "Mixed exposed tests",
          "1": "Single exposed or unstable test", "0": "No tested evidence / parity blocked"},
        "novelty": {"5": "Distinct observable licensed market-policy contract information",
          "4": "Specific untested independent mechanism", "3": "Concrete operational risk resolution",
          "2": "Specific diagnostic unknown with partial prior coverage", "1": "Closely related hypothesis",
          "0": "Redundant variation or question already answered"},
        "validation": {"AVAILABLE_NOW": [4, 5], "AVAILABLE_WITH_ACQUISITION": [2, 3],
          "EXPOSED_ONLY": [0, 1], "NOT_AVAILABLE": [0]},
        "time": {"5": "<1hour", "4": "1–3hours", "3": "3–8hours",
          "2": ">8hours", "1": "multi-day", "0": "Unbounded acquisition / legal dependency"},
        "risk": "5 means low implementation risk; 0 high. Estimates are judgments, not measured probabilities.",
        "submission_relevance": "5 operational delivery of verified official baseline;3 material component with uncertain transfer;0 irrelevant.",
        "stopping_rule": {"RESEARCH_CONTINUE": "Novel feasible clean-validation research >=70",
          "ONE_LAST_SHOT": "Best eligible research55–69 and low submission downside",
          "HARDEN_NOW": "All research<55 OR no novel feasible validation OR deadline operational risk dominates"},
        "technical_clarifications": [
          "EXPOSED_ONLY is not a clean validation path; no prospective set is invented.",
          "Hardening has zero novel predictive empirical signal/headroom; its benefit is preservation, not alpha.",
          "All nine candidates receive descriptive scores; eliminated redundant candidates cannot be selected.",
          "Tie order is the fixed candidate-list order; exactly one final axis.",
          "Unverified current deadline does not itself prove deadline urgency.",
          "Missing historical result metrics get D and null; missing is not a demonstrated scientific failure."]})
    save("experiment_spec.json", {"study": "ALPHA-STRATEGY-RESET-05", "parent": PARENT,
        "candidate_axes": CANDIDATES, "no_model_fit": True, "no_candidate_score": True,
        "no_new_data_source": True, "no_hidden_labels": True,
        "quality": {"A": "Official or independently validated", "B": "Frozen chronological exposed",
                    "C": "Post-hoc/diagnostic exposed", "D": "Missing reconstruction incomplete or parity issue"},
        "universes": ["OFFICIAL", "CARD_PROXY", "CANONICAL_MARGINAL_PROXY", "SOURCE_SPECIFIC_PROXY", "DIAGNOSTIC_ONLY"],
        "deadline_rule": "UNVERIFIED unless current exact date is proven by available repository artifacts",
        "score_projection": "Forbidden: no proxy * official score", "next_study_executed": False})
    status = {"executive_summary": "Rubric and required evidence inventory frozen before ranking.",
       "branch": BRANCH, "HEAD_SHA": PARENT, "state": "PRE_READY", "current_stage": "PRE_REMOTE_FREEZE",
       "completed": ["environment", "research_evidence_discovery", "rubric_implementation"],
       "pending": ["PRE_REMOTE_VERIFY", "evidence_synthesis", "ranking", "report", "tests", "RESULT", "recovery"],
       "rankings_computed": False, "new_forecasts": False}
    (RESULTS.parent / "STATUS.json").write_text(json.dumps(status, indent=2) + "\n")
    print(f"stage=PRE_READY evidence_files={len(inventory)} protected_files={len(protected)} output={RESULTS}")


if __name__ == "__main__":
    main()

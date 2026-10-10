"""Executive summary: test the evidence firewall, frozen rubric and single-axis decision."""
import ast
import csv
import json
from pathlib import Path

import pytest

from backtesting.alpha_strategy_reset05.core import (
    BRANCH, CANDIDATES, DIMENSIONS, MAIN, PARENT, PARENT_PRE, QUALITIES,
    UNIVERSES, decide, read, sha, verify_protection, weighted,
)

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "backtesting/alpha_strategy_reset05/results"


def test_exact_lineage():
    assert PARENT == "3c2bbfe7ff54ff9f95debf58f5bafa92d5d2ad70"
    assert PARENT_PRE == "ae0bdf3faf2b2ca32205f43cd417e32ab2119d4f"
    assert MAIN == "e1b5cf3b3a87966e902332ef3cc5c0ed2dbffee8"
    assert BRANCH == "track2/alpha-strategy-reset-05"


def test_weight_sum():
    assert sum(DIMENSIONS.values()) == pytest.approx(1)


@pytest.mark.parametrize("score,expected", [(0, 0), (1, 20), (3, 60), (5, 100)])
def test_weighted_endpoints(score, expected):
    assert weighted(dict.fromkeys(DIMENSIONS, score)) == expected


def test_weighted_asymmetric_arithmetic():
    s = dict.fromkeys(DIMENSIONS, 0); s["EMPIRICAL_SIGNAL"] = 5
    assert weighted(s) == 25


@pytest.mark.parametrize("bad", [-1, 6, 2.1, "3"])
def test_invalid_scores_rejected(bad):
    with pytest.raises(ValueError):
        weighted(dict.fromkeys(DIMENSIONS, bad))


def test_no_omitted_dimension():
    with pytest.raises(ValueError):
        weighted({"EMPIRICAL_SIGNAL": 5})


def rows(priority=30, novel=True, validation="AVAILABLE_WITH_ACQUISITION"):
    return [{"axis": a, "priority": priority, "genuinely_novel": novel,
             "validation": validation, "operationally_feasible": True,
             "eliminated": False, "low_submission_downside": True} for a in CANDIDATES]


@pytest.mark.parametrize("priority,decision", [(54, "HARDEN_NOW"), (55, "ONE_LAST_SHOT"),
                                               (69, "ONE_LAST_SHOT"), (70, "RESEARCH_CONTINUE")])
def test_frozen_stop_boundaries(priority, decision):
    d = decide(rows(priority)); assert d["stopping_rule"] == decision
    assert d["NEXT"] in CANDIDATES.values(); assert not d["next_study_executed"]


@pytest.mark.parametrize("validation", ["NOT_AVAILABLE", "EXPOSED_ONLY"])
def test_exposure_is_not_clean_validation(validation):
    assert decide(rows(95, validation=validation))["stopping_rule"] == "HARDEN_NOW"


def test_no_novelty_cannot_continue():
    assert decide(rows(95, novel=False))["NEXT"] == "SUBMISSION-HARDENING-06"


def test_no_fitting_scoring_or_truth_reader():
    for p in (RESULTS.parent).glob("*.py"):
        tree = ast.parse(p.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "attr", getattr(node.func, "id", ""))
                assert name not in {"fit", "fit_transform", "predict", "score_roster", "crps",
                                    "read_parquet", "load", "loadtxt", "train"}
            if isinstance(node, ast.Import):
                assert all(not x.name.startswith(("sklearn", "torch")) for x in node.names)


def test_parent_bytes_preserved():
    m = read(RESULTS / "protected_parent_hashes.json")
    verify_protection(ROOT, m["files"])


def test_evidence_inventory_hashes():
    with (RESULTS / "required_evidence_inventory.csv").open() as f:
        rows_ = list(csv.DictReader(f))
    assert len(rows_) > 300
    for row in rows_:
        assert sha(ROOT / row["evidence"]) == row["sha256"]


def test_frozen_rubric_identity():
    r = read(RESULTS / "research_priority_rubric.json")
    assert r["dimensions"] == DIMENSIONS
    assert r["candidate_axes"] == CANDIDATES
    assert not r["scores_assigned"]


def test_result_evidence_and_schemas():
    if not (RESULTS / "final_decision.json").exists():
        pytest.skip("Result-only schema check after remotely verified PRE")
    with (RESULTS / "evidence_quality_ledger.csv").open() as f:
        evidence = list(csv.DictReader(f))
    assert evidence and all(r["quality"] in QUALITIES for r in evidence)
    assert all(r["universe"] in UNIVERSES and r["evidence"] for r in evidence)
    with (RESULTS / "research_priority_matrix.csv").open() as f:
        matrix = list(csv.DictReader(f))
    assert {r["axis"] for r in matrix} == set(CANDIDATES)
    for row in matrix:
        assert weighted({k: int(row[k]) for k in DIMENSIONS}) == float(row["priority"])
        assert all(row[k + "_evidence"] for k in DIMENSIONS)
    final = read(RESULTS / "final_decision.json")
    assert final["NEXT"] in CANDIDATES.values()
    assert final["selected_axis_count"] == 1
    assert final["new_models_fit"] == final["new_candidate_scores"] == 0
    assert final["next_study_executed"] is False
    assert final["official_score_reestimated"] is False


def test_pre_binding():
    if not (RESULTS / "pre_result_manifest.json").exists():
        pytest.skip("Remote PRE receipt cannot exist inside its own commit")
    p = read(RESULTS / "pre_result_manifest.json")
    assert p["parent"] == PARENT and p["remote_verified"]
    assert len(p["PRE_RESULT_ALPHA_RESET05_SHA"]) == 40

"""Executive summary: test fail-closed provenance and unmeasured runtime evidence rejection."""
import ast
import json
from pathlib import Path

import pytest

from backtesting.submission_hardening06.core import (
    BRANCH, COMMON, GATES, MAIN, PARENT, PARENT_PRE, digest, package_names_safe,
    readiness, rebuild_allowed, repeated_output_equivalent, runtime_gates_verified,
    verify_protection,
)

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "backtesting/submission_hardening06/results"


def test_lineage_constants():
    assert PARENT == "8d06fcff48b9cc838d502f4c7b08fa2618015112"
    assert PARENT_PRE == "a80d1b431e4b9ff53d9abfd653b681b64fa006fa"
    assert MAIN == "e1b5cf3b3a87966e902332ef3cc5c0ed2dbffee8"
    assert BRANCH == "track2/submission-hardening-06"
    assert COMMON == "2.4.2"


@pytest.mark.parametrize("missing", GATES)
def test_each_ready_gate_mandatory(missing):
    e = dict.fromkeys(GATES, True); e[missing] = False
    assert not readiness(e).startswith("READY")


def test_unexecuted_cannot_be_ready():
    assert readiness({}) == "NOT_READY_MISSING_PROVENANCE"
    assert not rebuild_allowed({})
    assert not repeated_output_equivalent([])
    assert not runtime_gates_verified({})


def test_ready_exact_requires_all_gates():
    e = dict.fromkeys(GATES, True); e["original_image"] = True
    assert readiness(e) == "READY_EXACT_REFERENCE"
    e["original_image"] = False
    assert readiness(e) == "READY_REBUILT_EQUIVALENT"


def test_partial_provenance_blocks_rebuild():
    e = dict.fromkeys(("unique_historical_identity", "source_lineage", "runtime_dependencies_frozen",
                      "entrypoint_config_known", "runtime_contract_known", "source_unchanged"), True)
    assert rebuild_allowed(e)
    e["unique_historical_identity"] = False
    assert not rebuild_allowed(e)


def test_protected_parent_bytes():
    verify_protection(ROOT, json.loads((RESULTS / "protected_source_manifest.json").read_text())["all_parent_files"])


def test_protection_detects_mutation(tmp_path):
    p = tmp_path / "source.py"; p.write_bytes(b"original")
    verify_protection(tmp_path, {p.name: digest(b"original")})
    p.write_bytes(b"changed")
    with pytest.raises(ValueError):
        verify_protection(tmp_path, {p.name: digest(b"original")})


def runs():
    return [{"execution_id": i, "measured": True, "exit_code": 0,
             "files": {"forecast.parquet": "abc", "forecast_meta.json": "def"}} for i in range(3)]


def test_repeated_outputs_require_three_measured_independent_runs():
    r = runs(); assert repeated_output_equivalent(r)
    assert not repeated_output_equivalent(r[:2])
    r[2]["measured"] = False; assert not repeated_output_equivalent(r)


def test_changed_output_and_duplicate_run_rejected():
    r = runs(); r[2]["files"] = {"forecast.parquet": "changed"}
    assert not repeated_output_equivalent(r)
    r = runs(); r[2]["execution_id"] = 0
    assert not repeated_output_equivalent(r)


def gate_record():
    return dict.fromkeys(("measured", "finite", "schema", "shape", "domain", "joint_geometry",
                          "absolute_output_mount", "offline", "non_root", "read_only", "as_of"), True) | {"draws": 200}


@pytest.mark.parametrize("field", ["measured", "finite", "schema", "shape", "domain", "joint_geometry",
                                    "absolute_output_mount", "offline", "non_root", "read_only", "as_of"])
def test_runtime_contract_failure_not_green(field):
    r = gate_record(); assert runtime_gates_verified(r)
    r[field] = False; assert not runtime_gates_verified(r)


def test_minimum_and_card_draw_floor():
    r = gate_record(); r["draws"] = 199; assert not runtime_gates_verified(r)
    r["draws"] = 500; r["card_min_draws"] = 1000; assert not runtime_gates_verified(r)


@pytest.mark.parametrize("bad", ["../credentials", "/submission.json", ".env", "answer_key/a", "realized.parquet"])
def test_package_forbidden_paths(bad):
    assert not package_names_safe([bad])
    assert package_names_safe(["submission.json", "team-claim.json"])


def test_no_forecasting_hidden_labels_or_submit_calls():
    forbidden = {"fit", "predict", "crps", "read_parquet", "load", "score_roster", "submit"}
    for p in RESULTS.parent.glob("*.py"):
        for n in ast.walk(ast.parse(p.read_text())):
            if isinstance(n, ast.Call):
                assert getattr(n.func, "attr", getattr(n.func, "id", "")) not in forbidden


def test_candidate_preparation_is_not_official_receipt():
    r = json.loads((RESULTS / "official_receipt_audit.json").read_text())
    assert r["official_score"] == 0.9541 and not r["receipt_found"]
    assert r["preparation_archive_submission_status"] == "NOT_YET"


def test_fixed_historical_common_and_candidate_log_versions():
    d = json.loads((RESULTS / "dependency_identity.json").read_text())
    assert d["candidate_runtime_versions"]["qfbench2-common"] == "2.4.2"
    assert d["candidate_runtime_versions"]["numpy"] == "2.1.3"
    assert d["candidate_runtime_versions"]["pandas"] == "2.2.3"
    assert d["candidate_runtime_versions"]["pyarrow"] == "18.1.0"


def test_frozen_seed_and_draw_source_not_redefined():
    s = json.loads((RESULTS / "v51_source_identity.json").read_text())
    assert s["historical_workflow_seed"] == 0
    assert s["source_default_draws"] == 500 and s["F4_draw_floor"] == 1000
    assert s["official_invocation_seed"] is None and s["official_invocation_draws"] is None


def test_final_readiness_honest_if_present():
    p = RESULTS / "final_decision.json"
    if not p.exists(): pytest.skip("Final decision after remote PRE")
    d = json.loads(p.read_text())
    assert d["SUBMISSION_HARDENING06_RESULT"] == "NOT_READY_MISSING_PROVENANCE"
    assert not d["submission_performed"] and not d["rebuild_performed"]
    assert json.loads((RESULTS / "determinism_audit.json").read_text())["runs"] == []

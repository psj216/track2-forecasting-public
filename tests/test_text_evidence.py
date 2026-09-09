"""## Executive summary (read this first)

These tests pin the Phase-4 firewall: post-as-of and path-traversal documents are never opened,
model output cannot invent citations or assets, probabilities remain Python-owned, and an absent
model endpoint degrades explicitly to unchanged Numeric v3 behavior.
"""

from __future__ import annotations

import json
import pathlib

import pytest

import qfbench2_track_forecasting.text_evidence as text_evidence
from qfbench2_track_forecasting.text_evidence import (
    SCENARIOS,
    interpret_text_evidence,
    read_frozen_corpus,
    scenario_probability_ledger,
    validate_evidence_response,
)


def _valid_response() -> dict[str, object]:
    evidence = [
        {
            "id": "E1",
            "doc_ids": ["doc-1"],
            "claim": "Inflation language became firmer.",
            "shock": "INFLATION",
            "stance": "support",
            "strength": 0.8,
            "confidence": 0.9,
            "relevance": 0.8,
            "asset_impacts": [{"asset": "UST_2Y", "direction": "up", "intensity": 0.8}],
            "volatility_impact": "up",
            "tail_impact": "upside",
        },
        {
            "id": "E2",
            "doc_ids": ["doc-2"],
            "claim": "Growth risks create a competing downside case.",
            "shock": "GROWTH",
            "stance": "support",
            "strength": 0.5,
            "confidence": 0.7,
            "relevance": 0.6,
            "asset_impacts": [{"asset": "UST_2Y", "direction": "down", "intensity": 0.5}],
            "volatility_impact": "up",
            "tail_impact": "downside",
        },
    ]
    return {
        "market_state": {
            "label": "POLICY_REPRICING",
            "confidence": 0.8,
            "doc_ids": ["doc-1", "doc-2"],
        },
        "evidence": evidence,
        "views": {
            "long": {
                "thesis": "Rates can fall on growth weakness.",
                "evidence_ids": ["E2"],
                "confidence": 0.5,
            },
            "short": {
                "thesis": "Inflation can lift rates.",
                "evidence_ids": ["E1"],
                "confidence": 0.8,
            },
            "outlier": {
                "thesis": "Policy credibility can break.",
                "evidence_ids": ["E1", "E2"],
                "confidence": 0.4,
            },
        },
        "skeptic": {
            "common_assumption": "Policy remains effective.",
            "challenge": "Persistent inflation could constrain the response.",
            "evidence_ids": ["E1"],
        },
        "scenarios": [
            {
                "name": "SOFT_LANDING",
                "support": 0.2,
                "contradiction": 0.5,
                "confidence": 0.7,
                "relevance": 0.8,
                "evidence_ids": ["E1", "E2"],
            },
            {
                "name": "INFLATION_SHOCK",
                "support": 0.9,
                "contradiction": 0.1,
                "confidence": 0.9,
                "relevance": 0.9,
                "evidence_ids": ["E1"],
            },
            {
                "name": "GROWTH_SHOCK",
                "support": 0.6,
                "contradiction": 0.2,
                "confidence": 0.7,
                "relevance": 0.6,
                "evidence_ids": ["E2"],
            },
        ],
    }


def _write_index(root: pathlib.Path, documents: list[dict[str, str]]) -> None:
    root.mkdir(parents=True)
    (root / "corpus_index.json").write_text(json.dumps({"documents": documents}), encoding="utf-8")


def test_corpus_enforces_cutoff_and_refuses_path_traversal(tmp_path: pathlib.Path) -> None:
    text = tmp_path / "text"
    outside = tmp_path / "outside.txt"
    outside.write_text("must never be read", encoding="utf-8")
    _write_index(
        text,
        [
            {
                "doc_id": "old",
                "timestamp": "2020-01-01",
                "source": "x",
                "doc_type": "landmark",
                "file": "old.txt",
            },
            {
                "doc_id": "future",
                "timestamp": "2020-01-03",
                "source": "x",
                "doc_type": "landmark",
                "file": "future.txt",
            },
            {
                "doc_id": "escape",
                "timestamp": "2020-01-01",
                "source": "x",
                "doc_type": "landmark",
                "file": "../outside.txt",
            },
        ],
    )
    (text / "old.txt").write_text("known at the cutoff", encoding="utf-8")
    (text / "future.txt").write_text("future information", encoding="utf-8")

    result = read_frozen_corpus(text, "2020-01-02")

    assert [doc.doc_id for doc in result.documents] == ["old"]
    assert result.excluded_after_asof == 1
    assert result.excluded_invalid == 1


def test_response_rejects_an_invented_citation() -> None:
    response = _valid_response()
    response["evidence"][0]["doc_ids"] = ["not-supplied"]  # type: ignore[index]

    with pytest.raises(ValueError, match="unknown references"):
        validate_evidence_response(response, assets=["UST_2Y"], document_ids={"doc-1", "doc-2"})


def test_response_rejects_non_finite_scores() -> None:
    response = _valid_response()
    response["scenarios"][0]["support"] = float("nan")  # type: ignore[index]

    with pytest.raises(ValueError, match="finite"):
        validate_evidence_response(response, assets=["UST_2Y"], document_ids={"doc-1", "doc-2"})


def test_python_owns_probabilities_and_family_routing_strength() -> None:
    validated = validate_evidence_response(
        _valid_response(), assets=["UST_2Y"], document_ids={"doc-1", "doc-2"}
    )
    f1 = scenario_probability_ledger(validated, "T2-F1")
    f4 = scenario_probability_ledger(validated, "T2-F4")

    assert set(f1) == set(SCENARIOS)
    assert sum(f1.values()) == pytest.approx(1.0)
    assert sum(f4.values()) == pytest.approx(1.0)
    assert f4["INFLATION_SHOCK"] > f1["INFLATION_SHOCK"]
    assert min(f4.values()) >= 0.01


def test_response_rejects_numeric_strings() -> None:
    response = _valid_response()
    response["market_state"]["confidence"] = "0.8"  # type: ignore[index]

    with pytest.raises(ValueError, match="must be a number"):
        validate_evidence_response(response, assets=["UST_2Y"], document_ids={"doc-1", "doc-2"})


def test_absent_endpoint_is_an_explicit_shadow_fallback(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = tmp_path / "text"
    _write_index(
        text,
        [
            {
                "doc_id": "doc-1",
                "timestamp": "2020-01-01",
                "source": "x",
                "doc_type": "macro_release",
                "file": "doc.txt",
            }
        ],
    )
    (text / "doc.txt").write_text("Inflation risks increased.", encoding="utf-8")
    monkeypatch.delenv("MODEL_ENDPOINT", raising=False)

    result = interpret_text_evidence(
        text_dir=text,
        unit_id="t2-test",
        family="T2-F4",
        asof="2020-01-02",
        assets=["UST_2Y"],
        horizons=[21],
        target_type="level",
        target_frequency="daily",
        panel_context={},
        numeric_context={},
    )

    assert not result.applied
    assert result.skipped_reason == "MODEL_ENDPOINT is unset"
    assert result.evidence is None
    assert result.scenario_probabilities == scenario_probability_ledger(None, "T2-F4")


def test_valid_model_evidence_is_accepted_but_remains_shadow_only(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = tmp_path / "text"
    _write_index(
        text,
        [
            {
                "doc_id": "doc-1",
                "timestamp": "2020-01-01",
                "source": "x",
                "doc_type": "macro_release",
                "file": "one.txt",
            },
            {
                "doc_id": "doc-2",
                "timestamp": "2020-01-02",
                "source": "x",
                "doc_type": "fomc_statement",
                "file": "two.txt",
            },
        ],
    )
    (text / "one.txt").write_text("Inflation risks increased.", encoding="utf-8")
    (text / "two.txt").write_text("Growth risks also increased.", encoding="utf-8")
    monkeypatch.setattr(
        text_evidence,
        "call_evidence_model",
        lambda prompt: (_valid_response(), "", "test-model"),
    )

    result = interpret_text_evidence(
        text_dir=text,
        unit_id="t2-test",
        family="T2-F4",
        asof="2020-01-02",
        assets=["UST_2Y"],
        horizons=[21],
        target_type="level",
        target_frequency="daily",
        panel_context={},
        numeric_context={},
    )

    assert result.applied
    assert result.evidence is not None
    assert result.evidence["views"]["outlier"]["thesis"] == "Policy credibility can break."
    assert result.metadata()["forecast_adjustment_applied"] is False
    assert result.model_name == "test-model"

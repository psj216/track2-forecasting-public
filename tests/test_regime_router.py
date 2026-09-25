"""## Executive summary (read this first)

Exercise the House transport and cutoff-aware routing with synthetic documents.
Mocks verify the actual request contract; no live House access is implied.
"""

from __future__ import annotations

import io
import json
import urllib.error

import pytest

from qfbench2_track_forecasting.regime_router import (
    ModelReply,
    call_regime_model,
    interpret_regime,
    parse_regime_content,
    validate_regime,
)


def decision(**changes):
    return dict(
        regime="policy_shift",
        direction=1,
        confidence=0.8,
        tail_side="upper",
        horizon="medium",
        evidence=["past"],
        **changes,
    )


@pytest.fixture
def corpus(tmp_path):
    (tmp_path / "past.txt").write_text("Policy direction has changed.")
    (tmp_path / "future.txt").write_text("FUTURE_SECRET")
    (tmp_path / "corpus_index.json").write_text(
        json.dumps(
            {
                "documents": [
                    {"doc_id": "past", "timestamp": "2020-01-01", "file": "past.txt"},
                    {"doc_id": "future", "timestamp": "2020-03-01", "file": "future.txt"},
                ]
            }
        )
    )
    return tmp_path


def run(corpus, caller, family="T2-F2"):
    return interpret_regime(
        text_dir=corpus,
        family=family,
        asof="2020-02-01",
        assets=["EURUSD"],
        horizons=[21],
        target_type="level",
        model_caller=caller,
    )


def test_cutoff_grounding_and_application_are_separate(corpus):
    def caller(prompt):
        assert "FUTURE_SECRET" not in prompt
        assert '"doc_id": "future"' not in prompt
        return ModelReply(decision(), True, True, True, True)

    result = run(corpus, caller)
    assert result.gate_passed
    assert result.corpus.excluded_after_asof == 1
    assert result.metadata()["samples_changed"] is False
    assert result.metadata(samples_changed=True)["samples_changed"] is True


def test_future_or_hallucinated_citation_rejected(corpus):
    raw = decision()
    raw["evidence"] = ["future"]
    result = run(corpus, lambda _: ModelReply(raw, True, True, True, True))
    assert result.reason == "validation:evidence"
    assert not result.metadata(samples_changed=True)["samples_changed"]


def test_frozen_f3_never_calls_model(corpus):
    def caller(_):
        pytest.fail("F3 must never call House")

    assert run(corpus, caller, "T2-F3").reason == "gate:family_frozen"


@pytest.mark.parametrize(
    "field,value",
    [
        ("confidence", float("nan")),
        ("direction", True),
        ("direction", "up"),
        ("confidence", True),
        ("evidence", ["past", "past"]),
    ],
)
def test_strict_schema(field, value):
    raw = decision()
    raw[field] = value
    with pytest.raises(ValueError):
        validate_regime(raw, {"past"})


def test_parser_rejects_ambiguous_and_duplicate_json():
    raw = json.dumps(decision())
    assert parse_regime_content("```json\n" + raw + "\n```") == decision()
    assert (
        parse_regime_content("<think>classification only</think>\n```JSON\n" + raw + "\n```")
        == decision()
    )
    for content in (raw + raw, '{"regime":"continuation","regime":"policy_shift"}', "x" * 17000):
        with pytest.raises(ValueError):
            parse_regime_content(content)
    with pytest.raises(ValueError):
        parse_regime_content("<think>unfinished " + raw)


def test_minimal_json_normalizes_documented_values_and_requires_multiasset_target():
    raw = {"regime": " POLICY_SHIFT ", "direction": "+1", "confidence": "0.95", "evidence": "past"}
    decision = validate_regime(raw, {"past"}, ["EURUSD"])
    assert (decision.direction, decision.horizon, decision.tail_side) == (1, "short", "upper")
    with pytest.raises(ValueError, match="direction_asset_required"):
        validate_regime(raw, {"past"}, ["UST_2Y", "UST_10Y"])
    raw["direction_asset"] = "UST_2Y"
    assert validate_regime(raw, {"past"}, ["UST_2Y", "UST_10Y"]).direction_asset == "UST_2Y"
    raw["direction_asset"] = "NOT_A_TARGET"
    with pytest.raises(ValueError, match="direction_asset"):
        validate_regime(raw, {"past"}, ["UST_2Y", "UST_10Y"])


def setup_house(monkeypatch):
    monkeypatch.setenv("MODEL_ENDPOINT", "https://house.test")
    monkeypatch.setenv("MODEL_NAME", "house")
    monkeypatch.setenv("MODEL_TOKEN", "synthetic-private-token")


def test_official_transport_contract(monkeypatch):
    setup_house(monkeypatch)

    def open_mock(request, timeout):
        assert request.full_url == "https://house.test/v1/chat/completions"
        assert request.get_header("Authorization") == "Bearer synthetic-private-token"
        body = json.loads(request.data)
        assert body["model"] == "house"
        assert body["max_tokens"] <= 4000
        assert body["chat_template_kwargs"]["enable_thinking"] is False
        assert timeout == 60
        return io.BytesIO(
            json.dumps(
                {
                    "choices": [
                        {"finish_reason": "stop", "message": {"content": json.dumps(decision())}}
                    ]
                }
            ).encode()
        )

    monkeypatch.setattr("urllib.request.urlopen", open_mock)
    result = call_regime_model("synthetic prompt")
    assert result.call_attempted and result.call_succeeded and result.parse_succeeded


@pytest.mark.parametrize("status", [401, 403, 429])
def test_http_failure_is_auditable_without_secret(monkeypatch, status):
    setup_house(monkeypatch)

    def fail(request, timeout):
        raise urllib.error.HTTPError(request.full_url, status, "synthetic-private-token", {}, None)

    monkeypatch.setattr("urllib.request.urlopen", fail)
    reply = call_regime_model("prompt")
    assert reply.http_status == status and reply.call_attempted
    assert not reply.call_succeeded
    assert "synthetic-private-token" not in repr(reply)


def test_truncation_distinguished_from_transport_failure(monkeypatch):
    setup_house(monkeypatch)
    payload = {
        "choices": [{"finish_reason": "length", "message": {"content": json.dumps(decision())}}]
    }
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *a, **kw: io.BytesIO(json.dumps(payload).encode())
    )
    reply = call_regime_model("prompt")
    assert reply.call_succeeded and not reply.parse_succeeded


def test_missing_endpoint_never_calls(monkeypatch):
    monkeypatch.delenv("MODEL_ENDPOINT", raising=False)
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: pytest.fail("must not call"))
    assert not call_regime_model("prompt").call_attempted


def test_low_confidence_is_valid_but_not_applied(corpus):
    raw = decision()
    raw["confidence"] = 0.2
    result = run(corpus, lambda _: ModelReply(raw, True, True, True, True))
    assert result.validation_succeeded and not result.gate_passed
    assert result.reason == "gate:low_confidence"

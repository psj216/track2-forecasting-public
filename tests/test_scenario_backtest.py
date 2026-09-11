"""## Executive summary (read this first)

These tests pin Phase 6's anti-leakage and anti-overfitting contracts.  Replayed evidence must cite
documents available at its historical cutoff.  Candidate selection must use older cases, approval
must use newer holdout cases, and weak or undersized evidence sets must leave a family rejected.
"""

from __future__ import annotations

import json
import pathlib

import numpy as np
import pandas as pd
import pytest

import backtesting.build_evidence_replay as replay_builder
import backtesting.scenario_backtest as scenario_backtest
from backtesting.build_evidence_replay import _selected_cutoffs, build_evidence_replay
from backtesting.calibration_model import CalibrationModelClient
from backtesting.scenario_backtest import (
    _split_case_keys,
    calibrate,
    candidate_configs,
    load_replay,
    run_scenario_backtest,
)
from backtesting.universe_backtest import UniverseCase, load_universe
from qfbench2_track_forecasting.numeric_v1 import NumericForecast
from qfbench2_track_forecasting.scenario_integration import (
    IntegrationConfig,
)
from qfbench2_track_forecasting.scenario_integration import (
    integrate_scenario_worlds as real_integrator,
)
from qfbench2_track_forecasting.text_evidence import CorpusResult, ReasoningResult, TextDocument


def _case(family: str = "T2-F4") -> UniverseCase:
    dates = pd.date_range("2020-01-01", periods=220, freq="B").astype(str)
    values = pd.Series(range(220), index=dates, dtype=float)
    return UniverseCase(
        unit_id="public-test-unit",
        family=family,
        target_type="level",
        target_frequency="daily",
        assets=["A"],
        horizons=[1],
        histories={"A": values},
    )


def _evidence(doc_id: str = "D1") -> dict[str, object]:
    evidence = [
        {
            "id": "E1",
            "doc_ids": [doc_id],
            "claim": "Policy support may lift the target.",
            "shock": "POLICY",
            "stance": "support",
            "strength": 0.8,
            "confidence": 0.8,
            "relevance": 0.8,
            "asset_impacts": [{"asset": "A", "direction": "up", "intensity": 0.8}],
            "volatility_impact": "none",
            "tail_impact": "upside",
        },
        {
            "id": "E2",
            "doc_ids": [doc_id],
            "claim": "Growth risk contradicts the upside case.",
            "shock": "GROWTH",
            "stance": "contradiction",
            "strength": 0.5,
            "confidence": 0.7,
            "relevance": 0.7,
            "asset_impacts": [{"asset": "A", "direction": "down", "intensity": 0.5}],
            "volatility_impact": "up",
            "tail_impact": "downside",
        },
    ]
    return {
        "market_state": {"label": "MIXED_OR_UNCLEAR", "confidence": 0.6, "doc_ids": [doc_id]},
        "evidence": evidence,
        "views": {
            "long": {"thesis": "Policy helps.", "evidence_ids": ["E1"], "confidence": 0.7},
            "short": {"thesis": "Growth weakens.", "evidence_ids": ["E2"], "confidence": 0.6},
            "outlier": {
                "thesis": "Both effects fade.",
                "evidence_ids": ["E1", "E2"],
                "confidence": 0.4,
            },
        },
        "skeptic": {
            "common_assumption": "Policy transmits normally.",
            "challenge": "Transmission may be impaired.",
            "evidence_ids": ["E1"],
        },
        "scenarios": [
            {
                "name": "SOFT_LANDING",
                "support": 0.8,
                "contradiction": 0.2,
                "confidence": 0.8,
                "relevance": 0.8,
                "evidence_ids": ["E1"],
            },
            {
                "name": "GROWTH_SHOCK",
                "support": 0.5,
                "contradiction": 0.2,
                "confidence": 0.7,
                "relevance": 0.7,
                "evidence_ids": ["E2"],
            },
            {
                "name": "UNKNOWN_DOWNSIDE",
                "support": 0.3,
                "contradiction": 0.2,
                "confidence": 0.4,
                "relevance": 0.5,
                "evidence_ids": ["E2"],
            },
        ],
    }


def _write_replay(root: pathlib.Path, cutoff: str, doc_timestamp: str) -> pathlib.Path:
    text_dir = root / "units/public-test-unit/text"
    text_dir.mkdir(parents=True)
    (text_dir / "doc.txt").write_text("Policy and growth evidence.", encoding="utf-8")
    (text_dir / "corpus_index.json").write_text(
        json.dumps(
            {
                "documents": [
                    {
                        "doc_id": "D1",
                        "timestamp": doc_timestamp,
                        "file": "doc.txt",
                        "source": "test",
                        "doc_type": "macro_release",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    replay = root / "replay.jsonl"
    replay.write_text(
        json.dumps(
            {
                "calibration_kind": "public_nemotron_proxy",
                "unit_id": "public-test-unit",
                "cutoff": cutoff,
                "model_name": "test-model",
                "interpreter_prompt_version": "1.0.3",
                "interpreter_schema_version": "1.0.0",
                "replay_format_version": "2.0.0",
                "evidence": _evidence(),
            }
        ),
        encoding="utf-8",
    )
    return replay


def test_replay_revalidates_document_cutoff(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _case()
    cutoff = str(pd.Timestamp(case.histories["A"].index[180]).date())
    replay = _write_replay(tmp_path, cutoff, "2021-01-01")
    monkeypatch.setattr(scenario_backtest, "load_universe", lambda root: [case])

    with pytest.raises(ValueError, match="no cutoff-safe documents"):
        load_replay(replay, tmp_path)


def test_replay_accepts_only_grounded_historical_evidence(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _case()
    cutoff = str(pd.Timestamp(case.histories["A"].index[180]).date())
    replay = _write_replay(tmp_path, cutoff, "2020-01-02")
    monkeypatch.setattr(scenario_backtest, "load_universe", lambda root: [case])

    records = load_replay(replay, tmp_path)

    assert len(records) == 1
    assert records[0].reasoning.applied is True
    assert records[0].reasoning.corpus.documents[0].doc_id == "D1"


def test_scenario_backtest_compares_candidate_with_identical_numeric_draws(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _case()
    cutoff = str(pd.Timestamp(case.histories["A"].index[180]).date())
    replay = _write_replay(tmp_path, cutoff, "2020-01-02")
    monkeypatch.setattr(scenario_backtest, "load_universe", lambda root: [case])
    records = load_replay(replay, tmp_path)
    samples = np.linspace(178.0, 182.0, 500).reshape(500, 1, 1)
    monkeypatch.setattr(
        scenario_backtest,
        "forecast_numeric_v3",
        lambda *args, **kwargs: NumericForecast(samples=samples, metadata={}),
    )

    def checked_integrator(samples: np.ndarray, *args: object, **kwargs: object) -> object:
        np.testing.assert_array_equal(samples, expected_samples)
        return real_integrator(samples, *args, **kwargs)  # type: ignore[arg-type]

    expected_samples = samples.copy()
    monkeypatch.setattr(scenario_backtest, "integrate_scenario_worlds", checked_integrator)
    config = IntegrationConfig("test candidate", 0.05, 0.0, 0.0, 0.0, 0.0, 0.15)

    detail = run_scenario_backtest(
        tmp_path,
        records,
        500,
        configs_by_family={"T2-F4": (config,)},
    )

    assert detail["candidate"].tolist() == ["Numeric v3", "test candidate"]
    assert detail["model_name"].nunique() == 1
    assert detail[["marginal", "tail"]].notna().all().all()


def _detail(candidate_train: float, candidate_holdout: float) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    cutoffs = pd.date_range("2020-01-01", periods=8, freq="MS").astype(str)
    for index, cutoff in enumerate(cutoffs):
        candidate_value = candidate_train if index < 4 else candidate_holdout
        common = {
            "unit_id": f"u{index}",
            "family": "T2-F4",
            "cutoff": cutoff,
            "model_name": "fixed-test-model",
        }
        rows.append(
            {
                **common,
                "candidate": "Numeric v3",
                "marginal": 1.0,
                "joint": 1.0,
                "tail": 1.0,
            }
        )
        rows.append(
            {
                **common,
                "candidate": "candidate-a",
                "marginal": candidate_value,
                "joint": candidate_value,
                "tail": candidate_value,
            }
        )
    return pd.DataFrame(rows)


def test_calibration_approves_only_when_newer_holdout_clears_every_guard() -> None:
    _, decisions = calibrate(_detail(candidate_train=0.8, candidate_holdout=0.9))

    assert decisions[0].candidate == "candidate-a"
    assert decisions[0].approved is True
    assert decisions[0].train_cases == 4
    assert decisions[0].holdout_cases == 4


def test_calibration_rejects_a_train_winner_that_fails_on_holdout() -> None:
    _, decisions = calibrate(_detail(candidate_train=0.7, candidate_holdout=1.2))

    assert decisions[0].candidate == "candidate-a"
    assert decisions[0].approved is False
    assert "holdout geometric mean did not beat Numeric v3" in decisions[0].reasons


@pytest.mark.parametrize(
    ("component", "value", "reason"),
    [
        ("marginal", 1.04, "marginal component worsened by more than 3%"),
        ("tail", 1.06, "tail component worsened by more than 5%"),
    ],
)
def test_calibration_rejects_component_guard_failure(
    component: str, value: float, reason: str
) -> None:
    detail = _detail(candidate_train=0.8, candidate_holdout=0.8)
    holdout_candidate = (detail["candidate"] == "candidate-a") & detail["unit_id"].isin(
        ["u4", "u5", "u6", "u7"]
    )
    detail.loc[holdout_candidate, component] = value

    _, decisions = calibrate(detail)

    assert decisions[0].approved is False
    assert reason in decisions[0].reasons


def test_calibration_rejects_worst_decile_guard_failure() -> None:
    detail = _detail(candidate_train=0.8, candidate_holdout=0.8)
    bad_case = (detail["candidate"] == "candidate-a") & (detail["unit_id"] == "u7")
    detail.loc[bad_case, ["marginal", "joint", "tail"]] = 1.5

    _, decisions = calibrate(detail)

    assert decisions[0].approved is False
    assert "holdout worst decile exceeded the 1.10 guard" in decisions[0].reasons


def test_calibration_rejects_too_few_cases() -> None:
    detail = _detail(candidate_train=0.8, candidate_holdout=0.9)
    detail = detail[detail["unit_id"].isin([f"u{index}" for index in range(7)])]

    summary, decisions = calibrate(detail)

    assert summary.empty
    assert decisions[0].approved is False
    assert "at least four training and four holdout cases are required" in decisions[0].reasons


def test_calibration_rejects_mixed_model_versions() -> None:
    detail = _detail(candidate_train=0.8, candidate_holdout=0.9)
    detail.loc[detail["unit_id"] == "u7", "model_name"] = "changed-model"

    summary, decisions = calibrate(detail)

    assert summary.empty
    assert decisions[0].approved is False
    assert decisions[0].reasons == ["a family replay must use exactly one model version"]


def test_replay_loader_rejects_mixed_model_names(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _case()
    cutoff = str(pd.Timestamp(case.histories["A"].index[180]).date())
    replay = _write_replay(tmp_path, cutoff, "2020-01-02")
    second = json.loads(replay.read_text(encoding="utf-8"))
    second["unit_id"] = "second-test-unit"
    second["model_name"] = "changed-model"
    replay.write_text(
        replay.read_text(encoding="utf-8").rstrip() + "\n" + json.dumps(second) + "\n",
        encoding="utf-8",
    )
    second_case = UniverseCase(
        unit_id="second-test-unit",
        family=case.family,
        target_type=case.target_type,
        target_frequency=case.target_frequency,
        assets=case.assets,
        horizons=case.horizons,
        histories=case.histories,
    )
    second_text = tmp_path / "units/second-test-unit/text"
    second_text.mkdir(parents=True)
    (second_text / "doc.txt").write_text("Evidence.", encoding="utf-8")
    (second_text / "corpus_index.json").write_text(
        json.dumps(
            {
                "documents": [
                    {
                        "doc_id": "D1",
                        "timestamp": "2020-01-02",
                        "file": "doc.txt",
                        "source": "test",
                        "doc_type": "macro_release",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(scenario_backtest, "load_universe", lambda root: [case, second_case])

    with pytest.raises(ValueError, match="exactly one model name"):
        load_replay(replay, tmp_path)


def test_replay_loader_rejects_wrong_expected_model(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _case()
    cutoff = str(pd.Timestamp(case.histories["A"].index[180]).date())
    replay = _write_replay(tmp_path, cutoff, "2020-01-02")
    monkeypatch.setattr(scenario_backtest, "load_universe", lambda root: [case])

    with pytest.raises(ValueError, match="does not match expected model"):
        load_replay(replay, tmp_path, "nvidia/different-model")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("interpreter_prompt_version", "changed", "interpreter prompt"),
        ("interpreter_schema_version", "changed", "interpreter schema"),
        ("replay_format_version", "changed", "replay format"),
    ],
)
def test_replay_loader_rejects_stale_versions(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: str,
    message: str,
) -> None:
    case = _case()
    cutoff = str(pd.Timestamp(case.histories["A"].index[180]).date())
    replay = _write_replay(tmp_path, cutoff, "2020-01-02")
    raw = json.loads(replay.read_text(encoding="utf-8"))
    raw[field] = value
    replay.write_text(json.dumps(raw) + "\n", encoding="utf-8")
    monkeypatch.setattr(scenario_backtest, "load_universe", lambda root: [case])

    with pytest.raises(ValueError, match=message):
        load_replay(replay, tmp_path)


def test_chronological_split_never_divides_one_event_date() -> None:
    detail = _detail(candidate_train=0.8, candidate_holdout=0.9)
    duplicate = detail[detail["unit_id"] == "u1"].copy()
    duplicate["unit_id"] = "u1-second-card"
    detail = pd.concat([detail, duplicate], ignore_index=True)

    train, holdout = _split_case_keys(detail)

    train_dates = {cutoff for _, cutoff in train}
    holdout_dates = {cutoff for _, cutoff in holdout}
    assert train_dates.isdisjoint(holdout_dates)


def test_candidate_grid_is_predeclared_and_bounded() -> None:
    assert len(candidate_configs("T2-F1")) == 2
    assert len(candidate_configs("T2-F3")) == 4
    assert len(candidate_configs("T2-F4")) == 3
    assert max(config.tail_fraction for config in candidate_configs("T2-F4")) == pytest.approx(0.07)


@pytest.mark.parametrize("family", ["T2-F1", "T2-F2", "T2-F3"])
def test_non_f4_family_cannot_be_approved(family: str) -> None:
    detail = _detail(candidate_train=0.8, candidate_holdout=0.9)
    detail["family"] = family

    _, decisions = calibrate(detail)

    assert decisions[0].approved is False
    assert "only F4 has enough independent public proxy cases" in decisions[0].reasons[0]


def test_public_f4_opportunities_and_grouped_split_are_frozen() -> None:
    root = pathlib.Path(__file__).resolve().parents[1]
    cases: list[tuple[str, str]] = []
    for case in load_universe(root):
        if case.family != "T2-F4":
            continue
        cutoffs = _selected_cutoffs(case, root, 5, True)
        if cutoffs:
            cases.append((case.unit_id, cutoffs[0]))
    assert len(cases) == 24
    detail = pd.DataFrame(
        [
            {
                "unit_id": unit_id,
                "family": "T2-F4",
                "cutoff": cutoff,
                "candidate": candidate,
            }
            for unit_id, cutoff in cases
            for candidate in ("Numeric v3", "candidate")
        ]
    )

    train, holdout = _split_case_keys(detail)

    assert (len(train), len(holdout)) == (14, 10)
    assert {cutoff for _, cutoff in train}.isdisjoint({cutoff for _, cutoff in holdout})


def test_replay_builder_fails_instead_of_inventing_evidence(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _case()
    unit = tmp_path / "units/public-test-unit"
    unit.mkdir(parents=True)
    (unit / "card.toml").write_text(
        """## Executive summary (read this first)
[targets]
value_unit = "index"
[panels.primary]
series = ["A"]
asset_ids = ["A"]
frequency = "daily"
""",
        encoding="utf-8",
    )
    cutoff = str(pd.Timestamp(case.histories["A"].index[180]).date())
    corpus = CorpusResult(
        (TextDocument("D1", "2020-01-02", "test", "macro_release", "text"),),
        1,
        0,
        0,
        0,
        4,
    )
    numeric = NumericForecast(
        samples=np.empty((0,), dtype=float),
        metadata={
            "regime": {"fragility": 0.1, "recent_weight": 0.5, "uncertainty_scale": 1.0},
            "daily_drift": {"A": 0.0},
            "daily_sd": {"A": 1.0},
            "anchor": {"A": 180.0},
        },
    )
    skipped = ReasoningResult(False, "proxy endpoint failed", None, {}, corpus, "test-model")
    client = CalibrationModelClient("https://proxy.invalid/v1", "test-model")
    monkeypatch.setattr(replay_builder, "load_universe", lambda root: [case])
    monkeypatch.setattr(replay_builder, "cutoff_dates", lambda case, count: [cutoff])
    monkeypatch.setattr(replay_builder, "read_frozen_corpus", lambda path, asof: corpus)
    monkeypatch.setattr(replay_builder, "future_observations", lambda case, cutoff: None)
    monkeypatch.setattr(replay_builder, "forecast_numeric_v3", lambda *args, **kwargs: numeric)
    monkeypatch.setattr(replay_builder, "interpret_text_evidence", lambda **kwargs: skipped)

    with pytest.raises(RuntimeError, match="no evidence replay cases"):
        build_evidence_replay(
            tmp_path,
            tmp_path / "replay.jsonl",
            1,
            200,
            model_client=client,
        )


def test_replay_builder_serializes_only_deterministic_public_provenance(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _case()
    unit = tmp_path / "units/public-test-unit"
    unit.mkdir(parents=True)
    (unit / "card.toml").write_text(
        """## Executive summary (read this first)
[targets]
value_unit = "index"
[panels.primary]
series = ["A"]
asset_ids = ["A"]
frequency = "daily"
""",
        encoding="utf-8",
    )
    cutoff = str(pd.Timestamp(case.histories["A"].index[180]).date())
    corpus = CorpusResult(
        (TextDocument("D1", "2020-01-02", "test", "macro_release", "text"),),
        1,
        0,
        0,
        0,
        4,
    )
    numeric = NumericForecast(
        samples=np.empty((0,), dtype=float),
        metadata={
            "regime": {"fragility": 0.1, "recent_weight": 0.5, "uncertainty_scale": 1.0},
            "daily_drift": {"A": 0.0},
            "daily_sd": {"A": 1.0},
            "anchor": {"A": 180.0},
        },
    )
    reasoning = ReasoningResult(True, "", _evidence(), {}, corpus, "test-model")
    secret = "must-not-leak"
    client = CalibrationModelClient("https://proxy.invalid/v1", "test-model", api_key=secret)
    monkeypatch.setattr(replay_builder, "load_universe", lambda root: [case])
    monkeypatch.setattr(replay_builder, "cutoff_dates", lambda case, count: [cutoff])
    monkeypatch.setattr(replay_builder, "read_frozen_corpus", lambda path, asof: corpus)
    monkeypatch.setattr(replay_builder, "future_observations", lambda case, cutoff: None)
    monkeypatch.setattr(replay_builder, "forecast_numeric_v3", lambda *args, **kwargs: numeric)
    monkeypatch.setattr(replay_builder, "interpret_text_evidence", lambda **kwargs: reasoning)
    output = tmp_path / "replay.jsonl"

    written, skipped = build_evidence_replay(
        tmp_path,
        output,
        1,
        200,
        model_client=client,
        strict_model_failures=True,
    )

    payload = output.read_text(encoding="utf-8")
    record = json.loads(payload)
    assert (written, skipped) == (1, 0)
    assert secret not in payload
    assert "proxy.invalid" not in payload
    assert record["calibration_kind"] == "public_nemotron_proxy"
    assert record["model_name"] == "test-model"
    assert record["interpreter_prompt_version"] == "1.0.3"
    assert record["interpreter_schema_version"] == "1.0.0"
    assert record["replay_format_version"] == "2.0.0"

"""## Executive summary (read this first)

Prove cutoff filtering precedes record reads, response windows are causal, event
retrieval is independent, selection cannot rescue failed holdout, and F3 marginals
are preserved exactly. Synthetic data exercises the active family transformations.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from qfbench2_track_forecasting.v6.catalog import EventRecord, load_catalog
from qfbench2_track_forecasting.v6.fingerprint import Fingerprint, interpret, with_delta
from qfbench2_track_forecasting.v6.heads import Candidate, apply_head
from qfbench2_track_forecasting.v6.responses import extract
from qfbench2_track_forecasting.v6.retrieval import retrieve, similarity
from qfbench2_track_forecasting.v6.selector import choose


def fp(sign=1.0) -> Fingerprint:
    return Fingerprint(
        "policy", "FED", "US", "CURRENT", 0.9, {"policy": sign}, delta={"policy": sign}
    )


def record(date: str, episode: str = "meeting") -> EventRecord:
    return EventRecord(
        date,
        episode,
        fp(),
        "https://www.federalreserve.gov/test",
        "a" * 64,
        "The committee has raised the policy interest rate.",
        "fomc_statement",
    )


def test_catalog_checks_cutoff_before_opening_future_record(tmp_path: Path) -> None:
    (tmp_path / "index.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "records": [
                    {
                        "published_at": "2030-01-01",
                        "file": "does-not-exist.json",
                        "sha256": "a" * 64,
                    }
                ],
            }
        )
    )
    assert load_catalog(tmp_path, "2020-01-01") == []


def test_corrupt_catalog_fails_loudly(tmp_path: Path) -> None:
    (tmp_path / "record.json").write_text("{}")
    (tmp_path / "index.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "records": [
                    {"published_at": "2010-01-01", "file": "record.json", "sha256": "a" * 64}
                ],
            }
        )
    )
    with pytest.raises(ValueError, match="checksum"):
        load_catalog(tmp_path, "2020-01-01")


def test_response_must_mature_and_future_panel_cannot_change_it() -> None:
    dates = pd.bdate_range("2000-01-03", periods=500)
    frame = pd.DataFrame({"X": np.arange(500, dtype=float)}, index=dates)
    event = record(str(dates[200].date()))
    assert extract(frame, event, [21, 63], "level", "daily", str(dates[250].date())) is None
    response = extract(frame, event, [21, 63], "level", "daily", str(dates[263].date()))
    assert response is not None
    np.testing.assert_array_equal(response.path, [[21, 63]])
    modified = frame.copy()
    modified.iloc[264:] = 1e9
    after = extract(modified, event, [21, 63], "level", "daily", str(dates[263].date()))
    np.testing.assert_array_equal(response.path, after.path)
    np.testing.assert_array_equal(response.volatility, after.volatility)


def test_opposite_policy_events_and_duplicate_episodes_are_not_analogs() -> None:
    assert similarity(fp(), fp(-1), "T2-F2") == 0
    dates = pd.bdate_range("2000-01-03", periods=500)
    frame = pd.DataFrame({"X": np.arange(500, dtype=float)}, index=dates)
    rows = [
        extract(frame, record(str(dates[i].date())), [21], "level", "daily", str(dates[-1].date()))
        for i in (100, 200)
    ]
    selected, weights, ess = retrieve(fp(), rows, "T2-F2")
    assert len(selected) == 1 and ess == 1 and weights.sum() == 1


def test_failed_holdout_does_not_switch_to_another_candidate() -> None:
    train = {"a": [0.8] * 6, "b": [0.9] * 6}
    valid = {"a": [1.2] * 6, "b": [0.7] * 6}
    name, meta = choose(train, valid)
    assert name is None and meta["selected"] == "a"
    name, meta = choose(train, {"a": [0.9] * 6, "b": [0.7] * 6})
    assert name == "a" and meta["validation"]["n"] == 6


@pytest.mark.parametrize("family", ["T2-F1", "T2-F2", "T2-F3", "T2-F4"])
def test_active_heads_and_exact_zero_trust(family: str) -> None:
    rng = np.random.default_rng(12)
    base = rng.normal(size=(1000, 2, 3))
    paths = rng.normal(1, 0.3, size=(12, 2, 3))
    weights = np.ones(12) / 12
    config = Candidate("test", 0.2, False, 0.05)
    result = apply_head(base, paths, weights, np.zeros(2), family, "level", config, 0.9, 17)
    assert np.isfinite(result).all() and not np.array_equal(result, base)
    assert apply_head(base, paths, weights, np.zeros(2), family, "level", config, 0.0, 17) is base
    if family == "T2-F3":
        np.testing.assert_array_equal(np.sort(result, axis=0), np.sort(base, axis=0))


def test_semantics_reject_historical_and_detect_same_issuer_delta() -> None:
    old = interpret(
        "The Committee has lowered the policy interest rate.", "2000-01-01", "Federal Reserve"
    )
    new = interpret(
        "The Committee has raised the policy interest rate.", "2000-06-01", "Federal Reserve"
    )
    assert old is not None and new is not None
    assert with_delta(new, old).delta["policy"] > 0
    assert (
        interpret(
            "During the 2008 crisis, funding markets were under severe stress.",
            "2024-01-01",
            "Federal Reserve",
        )
        is None
    )

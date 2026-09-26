"""## Executive summary (read this first)

Prove same-event F2 responses use only completed paths in the unit's panel.
Sparse episodes and frozen families preserve the exact input draw bytes.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from qfbench2_track_forecasting.event_analog_v6 import apply_event_analog_f2


def _inputs(tmp_path: Path, *, past: int = 3) -> tuple[pd.Series, np.ndarray, str]:
    dates = pd.bdate_range("2010-01-04", periods=1400)
    values = 1.0 + np.cumsum(np.random.default_rng(6).normal(0, 0.002, len(dates)))
    series = pd.Series(values, index=dates)
    asof = str(dates[-1].date())
    entries = []
    for i in range(past):
        date = str(dates[200 + i * 240].date())
        filename = f"episode-{i}.txt"
        (tmp_path / filename).write_text("Funding market strain is severe now.")
        entries.append(
            {
                "doc_id": f"episode-{i}",
                "timestamp": date,
                "source": "test",
                "doc_type": "cb_speech",
                "file": filename,
            }
        )
    (tmp_path / "current.txt").write_text("Funding market strain is severe now.")
    entries.append(
        {
            "doc_id": "current",
            "timestamp": asof,
            "source": "test",
            "doc_type": "cb_speech",
            "file": "current.txt",
        }
    )
    (tmp_path / "corpus_index.json").write_text(json.dumps({"documents": entries}))
    draws = np.random.default_rng(17).normal(series.iloc[-1], 0.02, size=(500, 1, 2))
    return series, draws, asof


def test_f2_uses_completed_same_event_paths(tmp_path: Path) -> None:
    series, draws, asof = _inputs(tmp_path)
    result, meta = apply_event_analog_f2(
        draws,
        {"EUR": series},
        ["EUR"],
        [21, 63],
        "level",
        "daily",
        "T2-F2",
        asof,
        42,
        tmp_path,
    )
    assert meta["applied"]
    assert meta["eligible_episodes"] == 3
    assert meta["max_response_date"] < asof
    assert meta["sleeve_draws"] == 75
    changed = np.any(result != draws, axis=(1, 2))
    assert changed.sum() == 75
    assert np.array_equal(result[~changed], draws[~changed])


def test_sparse_or_future_episodes_keep_exact_numeric_draws(tmp_path: Path) -> None:
    series, draws, asof = _inputs(tmp_path, past=2)
    output, meta = apply_event_analog_f2(
        draws,
        {"EUR": series},
        ["EUR"],
        [21, 63],
        "level",
        "daily",
        "T2-F2",
        asof,
        42,
        tmp_path,
    )
    assert output is draws
    assert meta["reason"] == "too_few_independent_event_episodes"
    # A third event with a 63-day response outside the panel is not historical evidence.
    index = tmp_path / "corpus_index.json"
    entry = json.loads(index.read_text())
    (tmp_path / "late.txt").write_text("Funding market strain is severe now.")
    entry["documents"].append(
        {
            "doc_id": "late",
            "timestamp": str(series.index[-20].date()),
            "source": "test",
            "doc_type": "cb_speech",
            "file": "late.txt",
        }
    )
    index.write_text(json.dumps(entry))
    output, meta = apply_event_analog_f2(
        draws,
        {"EUR": series},
        ["EUR"],
        [21, 63],
        "level",
        "daily",
        "T2-F2",
        asof,
        42,
        tmp_path,
    )
    assert output is draws
    assert meta["eligible_episodes"] == 2


def test_other_families_and_late_documents_are_ignored(tmp_path: Path) -> None:
    series, draws, asof = _inputs(tmp_path)
    for family in ("T2-F1", "T2-F3", "T2-F4"):
        output, meta = apply_event_analog_f2(
            draws,
            {},
            ["EUR"],
            [21, 63],
            "level",
            "daily",
            family,
            asof,
            42,
            tmp_path,
        )
        assert output is draws and meta["reason"] == "family_frozen"
    index = tmp_path / "corpus_index.json"
    entry = json.loads(index.read_text())
    entry["documents"] = [e for e in entry["documents"] if e["doc_id"] != "current"]
    (tmp_path / "future.txt").write_text("Funding market strain is severe now.")
    entry["documents"].append(
        {
            "doc_id": "future",
            "timestamp": "2030-01-01",
            "source": "test",
            "doc_type": "cb_speech",
            "file": "future.txt",
        }
    )
    index.write_text(json.dumps(entry))
    output, meta = apply_event_analog_f2(
        draws,
        {"EUR": series},
        ["EUR"],
        [21, 63],
        "level",
        "daily",
        "T2-F2",
        asof,
        42,
        tmp_path,
    )
    assert output is draws and meta["reason"] == "no_current_event"

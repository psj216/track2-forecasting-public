"""## Executive summary (read this first)

Check F1 release changes and F4 temporal states with invented, dated prose.
This test contains no market outcome or validation-card answer.
"""

from __future__ import annotations

import json
from pathlib import Path

from qfbench2_track_forecasting.text_interpreter_v51 import (
    classify_currentness,
    f1_document_delta,
    f4_current_event,
)


def _write_corpus(root: Path, old: str, new: str) -> None:
    (root / "old.txt").write_text(old)
    (root / "new.txt").write_text(new)
    (root / "corpus_index.json").write_text(
        json.dumps(
            {
                "documents": [
                    {
                        "doc_id": "statement-old",
                        "timestamp": "2020-01-10",
                        "file": "old.txt",
                        "doc_type": "fomc_statement",
                    },
                    {
                        "doc_id": "statement-new",
                        "timestamp": "2020-02-10",
                        "file": "new.txt",
                        "doc_type": "fomc_statement",
                    },
                ]
            }
        )
    )


def test_f1_requires_change_in_same_series(tmp_path: Path) -> None:
    old = (
        "The Committee decided to maintain the target range for the rate. "
        "The Committee judges that it can be patient in beginning to normalize "
        "the stance of monetary policy."
    )
    new = (
        "The Committee decided to maintain the target range for the rate. "
        "The Committee will assess incoming information before it raises rates."
    )
    _write_corpus(tmp_path, old, new)
    event, meta = f1_document_delta(tmp_path, "2020-02-10", ["UST_2Y"])
    assert event is not None and event.currentness == "DOCUMENT_DELTA"
    assert event.event.kind == "policy_tightening"
    assert "patient" in event.prior_excerpt
    assert meta["document_pair"] == ["statement-old", "statement-new"]
    _write_corpus(tmp_path, old, old)
    event, meta = f1_document_delta(tmp_path, "2020-02-10", ["UST_2Y"])
    assert event is None and meta["reason"] == "no_meaningful_delta"


def test_f4_temporal_states() -> None:
    cases = (
        (
            "Funding markets are under severe strain.",
            "funding markets are under severe strain",
            "CURRENT",
        ),
        ("Funding pressures may intensify over coming weeks.", "funding pressures", "FORWARD"),
        (
            "During the 2008 crisis, funding markets were under severe strain.",
            "funding markets",
            "RETROSPECTIVE",
        ),
        (
            "If funding markets were to deteriorate, banks would respond.",
            "funding markets",
            "HYPOTHETICAL",
        ),
        ("Funding pressures have eased materially.", "funding pressures", "RESOLVED"),
    )
    for sentence, trigger, expected in cases:
        assert classify_currentness(sentence, trigger, "2024-05-01") == expected


def test_post_cutoff_or_retrospective_cannot_activate(tmp_path: Path) -> None:
    _write_corpus(
        tmp_path,
        "During the 2008 crisis, bank failures were widespread.",
        "In 2008, bank failures were widespread during the global financial crisis.",
    )
    event, _ = f4_current_event(tmp_path, "2020-02-10", ["UST_2Y"])
    assert event is None
    event, _ = f4_current_event(tmp_path, "2020-01-31", ["UST_2Y"])
    assert event is None

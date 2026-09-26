"""## Executive summary (read this first)

Match a current F2 text event to earlier events in this unit's own dated corpus.
Use only their fully observed, pre-asof panel responses. If independent matches
are too sparse, return the exact V3 draws; other families never enter this head.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from .numeric_v1 import _observation_period_business_days
from .text_evidence import TextDocument, read_frozen_corpus
from .text_first_v5 import _EVENTS
from .text_interpreter_v51 import _sentences, classify_currentness


@dataclass(frozen=True)
class AnalogEvent:
    kind: str
    date: str
    doc_id: str
    excerpt: str


def _doc_event(doc: TextDocument) -> AnalogEvent | None:
    """Take one temporally grounded event per document; never use card titles."""
    hits: list[tuple[int, int, str, str]] = []
    for sentence in _sentences(doc.text):
        if not 24 <= len(sentence) <= 550 or sentence.endswith("?"):
            continue
        for kind, pattern, specificity in _EVENTS:
            match = re.search(pattern, sentence, re.I)
            if match is None:
                continue
            if classify_currentness(sentence, match.group(0), doc.timestamp) not in {
                "CURRENT",
                "FORWARD",
            }:
                continue
            hits.append((specificity, -len(hits), kind, sentence[:220]))
    if not hits:
        return None
    _, _, kind, excerpt = max(hits)
    return AnalogEvent(kind, doc.timestamp, doc.doc_id, excerpt)


def event_episodes(
    text_dir: Path, asof: str, kind: str, *, maturity_days: int, min_gap_days: int = 20
) -> tuple[list[AnalogEvent], AnalogEvent | None, dict[str, Any]]:
    """Filter each document by its publication date and deduplicate one event cycle."""
    try:
        corpus = read_frozen_corpus(text_dir, asof)
    except (OSError, ValueError, TypeError):
        return [], None, {"reason": "corpus_unavailable"}
    detected = [event for doc in corpus.documents if (event := _doc_event(doc))]
    recent = [e for e in detected if (pd.Timestamp(asof) - pd.Timestamp(e.date)).days <= 50]
    current = max(recent, key=lambda e: (e.date, e.doc_id), default=None)
    if current is None:
        return [], None, {"reason": "no_current_event", "documents": len(corpus.documents)}
    if current.kind != kind:
        return [], current, {"reason": "different_current_event"}
    cutoff = pd.Timestamp(asof)
    older = sorted(
        (
            e
            for e in detected
            if e.kind == kind
            and e.doc_id != current.doc_id
            and pd.Timestamp(e.date) + pd.offsets.BDay(maturity_days) <= cutoff
        ),
        key=lambda e: (e.date, e.doc_id),
    )
    independent: list[AnalogEvent] = []
    for event in older:
        if (
            independent
            and (pd.Timestamp(event.date) - pd.Timestamp(independent[-1].date)).days < min_gap_days
        ):
            continue
        independent.append(event)
    return independent, current, {"reason": "episodes_checked", "documents": len(corpus.documents)}


def apply_event_analog_f2(
    samples: NDArray[np.float64],
    histories: dict[str, pd.Series],
    assets: list[str],
    horizons: list[int],
    target_type: str,
    target_frequency: str,
    family: str,
    asof: str,
    seed: int,
    text_dir: Path,
    *,
    min_episodes: int = 3,
    sleeve: float = 0.15,
) -> tuple[NDArray[np.float64], dict[str, Any]]:
    """Replace a small draw sleeve with actual responses to the same past event.

    Dates and prices come exclusively from the current unit's mounted inputs.
    An episode's entire response window must end before the current as-of.
    """
    meta: dict[str, Any] = {
        "config": "v6-f2-event-analog",
        "applied": False,
        "numeric_fallback_exact": True,
        "reason": "family_frozen",
    }
    if family != "T2-F2":
        return samples, meta
    if target_type not in {"level", "log_return"} or samples.shape[1:] != (
        len(assets),
        len(horizons),
    ):
        meta["reason"] = "unsupported_grid"
        return samples, meta
    if not assets or any(asset not in histories for asset in assets):
        meta["reason"] = "target_history_unavailable"
        return samples, meta
    # Derive steps without applying the V5 2520-observation truncation: early
    # dated documents may be much older than ten years.
    frame = pd.DataFrame({a: histories[a] for a in assets}).sort_index()
    frame = frame.loc[pd.to_datetime(frame.index) <= pd.Timestamp(asof)]
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna()
    if len(frame) < 180:
        meta["reason"] = "insufficient_history"
        return samples, meta
    period = 1 if target_frequency == "daily" else _observation_period_business_days(frame)
    observed = np.maximum(1, np.ceil(np.asarray(horizons) / period).astype(int))
    maximum = int(observed.max())
    try:
        corpus = read_frozen_corpus(text_dir, asof)
    except (OSError, ValueError, TypeError):
        meta["reason"] = "corpus_unavailable"
        return samples, meta
    events = [e for doc in corpus.documents if (e := _doc_event(doc))]
    recent = [e for e in events if (pd.Timestamp(asof) - pd.Timestamp(e.date)).days <= 50]
    if not recent:
        meta["reason"] = "no_current_event"
        return samples, meta
    current = max(recent, key=lambda e: (e.date, e.doc_id))
    meta.update(event=current.kind, evidence_ids=[current.doc_id], evidence_excerpt=current.excerpt)
    episodes, _, _ = event_episodes(text_dir, asof, current.kind, maturity_days=max(horizons))
    dates = pd.DatetimeIndex(pd.to_datetime(frame.index))
    starts: list[int] = []
    used: list[AnalogEvent] = []
    last_position = -maximum
    for episode in episodes:
        # An event published after market close starts at the next observation.
        origin = int(dates.searchsorted(pd.Timestamp(episode.date), side="right"))
        if origin <= 0 or origin + maximum >= len(frame):
            continue
        if dates[origin + maximum] > pd.Timestamp(asof):
            continue
        if origin - last_position < maximum:
            continue
        window = dates[origin : origin + maximum + 1].to_numpy(dtype="datetime64[D]")
        if np.any(np.busday_count(window[:-1], window[1:]) > max(5, 2 * period)):
            continue
        starts.append(origin)
        used.append(episode)
        last_position = origin
    meta.update(eligible_episodes=len(starts), episode_dates=[e.date for e in used])
    if len(starts) < min_episodes:
        meta["reason"] = "too_few_independent_event_episodes"
        return samples, meta
    count = int(len(samples) * sleeve)
    if count < 10:
        meta["reason"] = "too_few_draws"
        return samples, meta
    values = frame.to_numpy(dtype=float)
    responses = []
    for origin in starts:
        if target_type == "log_return":
            path = np.stack(
                [values[origin + 1 : origin + offset + 1].sum(axis=0) for offset in observed],
                axis=1,
            )
        else:
            path = np.stack(
                [values[origin + offset] - values[origin] for offset in observed], axis=1
            )
        responses.append(path)
    paths = np.stack(responses)
    if target_type == "level":
        paths += values[-1][None, :, None]
    if not np.isfinite(paths).all():
        meta["reason"] = "nonfinite_paths"
        return samples, meta
    rng = np.random.default_rng(seed ^ 0x6F2A)
    positions = rng.choice(len(samples), count, replace=False)
    choices = rng.choice(len(paths), count, replace=True)
    output = samples.copy()
    output[positions] = paths[choices]
    meta.update(
        applied=True,
        numeric_fallback_exact=False,
        reason="same_event_empirical_mixture",
        sleeve_draws=count,
        sleeve_fraction=count / len(samples),
        max_response_date=str(dates[max(starts) + maximum].date()),
    )
    return output, meta

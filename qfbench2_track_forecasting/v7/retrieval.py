"""## Executive summary (read this first)

Retrieve compatible, non-overlapping historical episodes with mature response paths.
No later panel observations or same-day response can enter the result.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from ..v6.responses import Response, extract
from .catalog import Event
from .encoder import Query


def similarity(query: Query, event: Event) -> float:
    a, b = query.fingerprint, event.fingerprint
    # An unlabeled speech is not the same historical event as a CPI release.
    # Add speech episodes to the catalog before allowing that event class.
    if query.event_type != event.event_type:
        return 0.0
    if a.region != event.region:
        return 0.0
    keys = set(a.axes) | set(b.axes)
    x = np.array([a.axes.get(k, 0.0) for k in sorted(keys)])
    y = np.array([b.axes.get(k, 0.0) for k in sorted(keys)])
    cosine = float(x @ y / max(1e-12, np.linalg.norm(x) * np.linalg.norm(y)))
    if cosine <= 0:
        return 0.0
    return float(
        np.clip(
            0.55 * cosine + 0.25 * (a.major == b.major) + 0.2 * (a.issuer == b.issuer),
            0,
            1,
        )
    )


def _market_state(frame: pd.DataFrame, end: pd.Timestamp, target: str) -> np.ndarray | None:
    prefix = frame.loc[frame.index <= end].tail(121)
    if len(prefix) < 70:
        return None
    steps = prefix if target == "log_return" else prefix.diff().dropna()
    if len(steps) < 60:
        return None
    recent = steps.tail(20).to_numpy(dtype=float)
    long = steps.tail(60).to_numpy(dtype=float)
    slow_sd = np.maximum(np.std(long, axis=0), 1e-8)
    ratio = np.clip(np.std(recent, axis=0) / slow_sd, 0, 5)
    trend = np.clip(np.mean(recent, axis=0) / slow_sd, -3, 3)
    return np.r_[ratio, trend]


def retrieve(
    query: Query,
    events: list[Event],
    frame: pd.DataFrame,
    horizons: list[int],
    target: str,
    frequency: str,
    cutoff: str,
    max_items: int = 30,
) -> tuple[list[Response], NDArray[np.float64], float]:
    ranked = sorted(
        ((similarity(query, e), e) for e in events if e.published_at < query.published_at),
        key=lambda pair: (pair[0], pair[1].published_at),
        reverse=True,
    )
    selected: list[Response] = []
    scores = []
    current_state = _market_state(frame, frame.index[-1], target)
    for score, event in ranked:
        if score < 0.52:
            break
        response = extract(frame, event, horizons, target, frequency, cutoff)
        if response is None or any(
            not (response.end < old.start or response.start > old.end) for old in selected
        ):
            continue
        selected.append(response)
        historical_state = _market_state(frame, response.start, target)
        if current_state is not None and historical_state is not None:
            distance = float(np.mean(np.abs(current_state - historical_state)))
            state_weight = 0.75 + 0.25 * np.exp(-distance)
        else:
            state_weight = 1.0
        scores.append(score * state_weight)
        if len(selected) >= max_items:
            break
    weights = np.asarray(scores, dtype=np.float64) ** 3
    if len(weights):
        weights /= weights.sum()
    ess = float(1 / np.sum(weights**2)) if len(weights) else 0.0
    return selected, weights, ess

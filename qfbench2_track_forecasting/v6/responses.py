"""## Executive summary (read this first)

Extract complete response paths and pre-event volatility from the current panel only.
Every returned outcome and volatility estimate is bounded by the caller's cutoff.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from .catalog import EventRecord


@dataclass(frozen=True)
class Response:
    event: EventRecord
    start: pd.Timestamp
    end: pd.Timestamp
    path: NDArray[np.float64]
    volatility: NDArray[np.float64]


def frame_at(histories: dict[str, pd.Series], assets: list[str], cutoff: str) -> pd.DataFrame:
    frame = pd.DataFrame({a: histories[a] for a in assets}).sort_index()
    frame.index = pd.to_datetime(frame.index)
    return (
        frame.loc[frame.index <= pd.Timestamp(cutoff)].replace([np.inf, -np.inf], np.nan).dropna()
    )


def positions(
    frame: pd.DataFrame, date: str, horizons: list[int], frequency: str
) -> tuple[int, list[int]] | None:
    dates = frame.index
    origin = int(dates.searchsorted(pd.Timestamp(date), side="right")) - 1
    if origin < 60 or (pd.Timestamp(date) - dates[origin]).days > 5:
        return None
    ends = [
        origin + h
        if frequency == "daily"
        else int(dates.searchsorted(dates[origin] + pd.offsets.BDay(h)))
        for h in horizons
    ]
    if max(ends) >= len(frame):
        return None
    window = dates[origin : max(ends) + 1].to_numpy(dtype="datetime64[D]")
    max_gap = 5 if frequency == "daily" else 40
    if np.any(np.busday_count(window[:-1], window[1:]) > max_gap):
        return None
    return origin, ends


def volatility(frame: pd.DataFrame, target: str, origin: int | None = None) -> NDArray[np.float64]:
    prefix = frame if origin is None else frame.iloc[: origin + 1]
    steps = prefix if target == "log_return" else prefix.diff()
    return np.asarray(
        np.maximum(steps.tail(60).std().to_numpy(dtype=float), 1e-8), dtype=np.float64
    )


def extract(
    frame: pd.DataFrame,
    event: EventRecord,
    horizons: list[int],
    target: str,
    frequency: str,
    cutoff: str,
) -> Response | None:
    if event.published_at > cutoff:
        return None
    loc = positions(frame, event.published_at, horizons, frequency)
    if loc is None:
        return None
    origin, ends = loc
    if frame.index[max(ends)] > pd.Timestamp(cutoff):
        return None
    values = frame.to_numpy(dtype=float)
    paths = np.stack(
        [
            values[origin + 1 : end + 1].sum(axis=0)
            if target == "log_return"
            else values[end] - values[origin]
            for end in ends
        ],
        axis=1,
    )
    return Response(
        event, frame.index[origin], frame.index[max(ends)], paths, volatility(frame, target, origin)
    )

"""## Executive summary (read this first)

This module is the first competitive numeric forecaster for the submission. It separates level
targets from return targets, measures the current regime, and samples one joint path across every
asset and horizon. It never reads text and never uses data after the requested as-of date.

The model deliberately stays small and auditable. It uses a five-day block bootstrap, blending
recent history with the full sample. Blocks preserve observed volatility clustering and
cross-asset co-movement. A regime-fragility score lowers the weight on recent history and widens
the distribution when recent behaviour is unusually different from the longer record.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

_RETURN_TARGETS = frozenset({"log_return", "return", "simple_return", "pct_change"})
_VOL_FLOOR = 1e-8


@dataclass(frozen=True)
class NumericForecast:
    """Joint Monte Carlo paths and the diagnostics that produced them."""

    samples: NDArray[np.float64]
    metadata: dict[str, Any]


def _diff_without_gaps(series: pd.Series) -> pd.Series:
    """Difference a dated series without treating a long missing interval as one day."""
    diff = series.diff()
    when = pd.to_datetime(pd.Series(series.index, index=series.index), errors="coerce")
    spacing = when.diff().dt.days
    if spacing.notna().sum() == 0:
        return diff
    limit = max(float(spacing.median()) * 10.0, 5.0)
    return diff.where(spacing <= limit)


def _safe_std(frame: pd.DataFrame) -> pd.Series:
    """Finite positive column standard deviations for stable scaling."""
    scale = frame.std(ddof=1).replace([np.inf, -np.inf], np.nan)
    fallback = frame.abs().median() * 0.01
    return scale.fillna(fallback).clip(lower=_VOL_FLOOR)


def _regime_diagnostics(steps: pd.DataFrame) -> dict[str, Any]:
    """Measure volatility, momentum and correlation instability without choosing direction."""
    long = steps.tail(min(252, len(steps)))
    recent20 = steps.tail(min(20, len(steps)))
    recent60 = steps.tail(min(60, len(steps)))
    recent120 = steps.tail(min(120, len(steps)))

    vol_long = _safe_std(long)
    vol20 = _safe_std(recent20)
    vol60 = _safe_std(recent60)
    vol120 = _safe_std(recent120)
    vol_ratio = (vol20 / vol_long).clip(lower=0.05, upper=20.0)

    momentum20 = recent20.sum() / (vol_long * np.sqrt(max(len(recent20), 1)))
    vol_shift = float(np.median(np.abs(np.log(vol_ratio.to_numpy(dtype=float)))))
    vol_fragility = float(np.clip(vol_shift / np.log(3.0), 0.0, 1.0))
    momentum_fragility = float(
        np.clip(
            np.median(np.maximum(np.abs(momentum20.to_numpy(dtype=float)) - 1.0, 0.0)) / 3.0,
            0.0,
            1.0,
        )
    )

    correlation_shift = 0.0
    if steps.shape[1] > 1 and len(recent60) >= 10:
        corr_recent = recent60.corr().fillna(0.0).to_numpy(dtype=float)
        corr_long = long.corr().fillna(0.0).to_numpy(dtype=float)
        denominator = np.sqrt(steps.shape[1] * max(steps.shape[1] - 1, 1))
        correlation_shift = float(
            np.clip(np.linalg.norm(corr_recent - corr_long, ord="fro") / denominator, 0.0, 1.0)
        )

    fragility_raw = 0.55 * vol_fragility + 0.25 * momentum_fragility + 0.20 * correlation_shift
    fragility = float(np.clip(fragility_raw, 0.0, 1.0))
    recent_weight = float(np.clip(0.70 - 0.25 * fragility, 0.45, 0.70))
    uncertainty_scale = float(1.0 + 0.25 * fragility)

    return {
        "vol_20": {k: float(v) for k, v in vol20.items()},
        "vol_60": {k: float(v) for k, v in vol60.items()},
        "vol_120": {k: float(v) for k, v in vol120.items()},
        "vol_long": {k: float(v) for k, v in vol_long.items()},
        "vol_ratio_20_long": {k: float(v) for k, v in vol_ratio.items()},
        "momentum_20_z": {k: float(v) for k, v in momentum20.items()},
        "correlation_shift": correlation_shift,
        "fragility": fragility,
        "recent_weight": recent_weight,
        "uncertainty_scale": uncertainty_scale,
    }


def _drift(steps: pd.DataFrame, max_horizon: int) -> NDArray[np.float64]:
    """A strongly shrunk multi-window drift with a horizon-scale safety cap."""
    means = [steps.tail(min(window, len(steps))).mean() for window in (20, 60, 120)]
    full_mean = steps.tail(min(1260, len(steps))).mean()
    raw = 0.45 * means[0] + 0.30 * means[1] + 0.15 * means[2] + 0.10 * full_mean
    daily = 0.20 * raw.to_numpy(dtype=float)

    scale = _safe_std(steps.tail(min(252, len(steps)))).to_numpy(dtype=float)
    max_daily = 0.75 * scale / np.sqrt(max(max_horizon, 1))
    return np.asarray(np.clip(daily, -max_daily, max_daily), dtype=np.float64)


def _sample_blocks(
    steps: pd.DataFrame,
    n_draws: int,
    max_horizon: int,
    recent_weight: float,
    uncertainty_scale: float,
    drift: NDArray[np.float64],
    seed: int,
) -> NDArray[np.float64]:
    """Sample shared historical blocks so every draw represents one coherent world."""
    rng = np.random.default_rng(seed)
    values = steps.to_numpy(dtype=float)
    n_rows, n_assets = values.shape
    block_size = min(5, max_horizon, n_rows)
    recent_start = max(0, n_rows - 120)

    full_mean = values.mean(axis=0)
    recent_mean = values[recent_start:].mean(axis=0)
    full_last_start = max(0, n_rows - block_size)
    recent_last_start = max(recent_start, n_rows - block_size)

    paths = np.empty((n_draws, max_horizon, n_assets), dtype=float)
    for draw in range(n_draws):
        cursor = 0
        while cursor < max_horizon:
            use_recent = bool(rng.random() < recent_weight)
            low = recent_start if use_recent else 0
            high = recent_last_start if use_recent else full_last_start
            start = int(rng.integers(low, high + 1)) if high > low else low
            take = min(block_size, max_horizon - cursor)
            centre = recent_mean if use_recent else full_mean
            block = values[start : start + take] - centre
            paths[draw, cursor : cursor + take, :] = block * uncertainty_scale + drift
            cursor += take
    return paths


def forecast_numeric_v1(
    histories: dict[str, pd.Series],
    assets: list[str],
    horizons: list[int],
    target_type: str,
    n_draws: int,
    seed: int,
) -> NumericForecast:
    """Generate target-aware, regime-aware, joint samples from dated asset histories."""
    if not assets or not horizons:
        raise ValueError("assets and horizons must be non-empty")
    if min(horizons) < 1:
        raise ValueError("horizons must be positive business-day offsets")
    if n_draws < 1:
        raise ValueError("n_draws must be positive")

    is_return = target_type in _RETURN_TARGETS
    prepared: dict[str, pd.Series] = {}
    anchors: dict[str, float] = {}
    observed_last: dict[str, float] = {}
    for asset in assets:
        series = histories[asset].sort_index().astype(float)
        if series.empty:
            raise ValueError(f"history for {asset!r} is empty")
        observed_last[asset] = float(series.iloc[-1])
        anchors[asset] = 0.0 if is_return else float(series.iloc[-1])
        prepared[asset] = series if is_return else _diff_without_gaps(series)

    steps = pd.DataFrame(prepared).dropna()
    if len(steps) < 10:
        raise ValueError(f"not enough overlapping history to forecast ({len(steps)} rows)")

    max_horizon = max(horizons)
    regime = _regime_diagnostics(steps)
    daily_drift = _drift(steps, max_horizon)
    path_steps = _sample_blocks(
        steps.tail(min(2520, len(steps))),
        n_draws,
        max_horizon,
        regime["recent_weight"],
        regime["uncertainty_scale"],
        daily_drift,
        seed,
    )
    cumulative = np.cumsum(path_steps, axis=1)
    anchor_vector = np.array([anchors[a] for a in assets], dtype=float)

    samples = np.empty((n_draws, len(assets), len(horizons)), dtype=float)
    for horizon_index, horizon in enumerate(horizons):
        samples[:, :, horizon_index] = anchor_vector + cumulative[:, horizon - 1, :]

    if not np.isfinite(samples).all():
        raise ValueError("numeric forecast produced non-finite samples")

    longest_index = horizons.index(max_horizon)
    effective_daily_sd = samples[:, :, longest_index].std(axis=0, ddof=1) / np.sqrt(max_horizon)
    metadata: dict[str, Any] = {
        "model": "regime-aware joint block bootstrap v1",
        "target_type": target_type,
        "anchor": anchors,
        # Kept for the existing reasoning adapter, which sizes its optional adjustment from these.
        "last": observed_last,
        "daily_sd": {a: float(effective_daily_sd[i]) for i, a in enumerate(assets)},
        "daily_drift": {a: float(daily_drift[i]) for i, a in enumerate(assets)},
        "n_history_rows": int(len(steps)),
        "block_size": int(min(5, max_horizon, len(steps))),
        "regime": regime,
    }
    return NumericForecast(samples=samples, metadata=metadata)

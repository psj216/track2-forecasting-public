"""## Executive summary (read this first)

Experimental V4 keeps the V2.1 anchor and F3 transmission unchanged. A changes only
analogue routing; B rescales lag-volatility-normalized historical shocks. Both retain
shared block starts across assets and coherent horizons. C is a separately fitted,
monotone single-cell tail transform. Nothing here changes the default submission.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from .numeric_v1 import (
    _RETURN_TARGETS,
    _VOL_FLOOR,
    NumericForecast,
    _diff_without_gaps,
    _state_matched_starts,
)
from .numeric_v3 import forecast_numeric_v3
from .numeric_v21 import V21_CONFIG


@dataclass(frozen=True)
class V4Config:
    """One-factor ablations, fixed before validation outcomes are examined."""

    name: str
    routing: bool = False
    normalize_volatility: bool = False


V4_A = V4Config("v4-a-routing", routing=True)
V4_B = V4Config("v4-b-volatility", normalize_volatility=True)
V4_AB = V4Config("v4-ab", routing=True, normalize_volatility=True)


def state_features(steps: pd.DataFrame) -> pd.DataFrame:
    """Every row depends only on observations up to that row, never its next block."""
    vol = steps.rolling(120, min_periods=120).std().clip(lower=_VOL_FLOOR)
    short = steps.rolling(20, min_periods=20)
    cumulative = steps.cumsum()
    features = [
        np.log(short.std().clip(lower=_VOL_FLOOR) / vol).add_prefix("vol:"),
        (short.sum() / (vol * np.sqrt(20))).add_prefix("momentum:"),
        ((cumulative - cumulative.rolling(60).max()) / (vol * np.sqrt(60))).add_prefix("drawdown:"),
        (np.sqrt(steps.clip(upper=0).pow(2).rolling(20).mean()) / vol).add_prefix("downside:"),
        short.skew().fillna(0).clip(-5, 5).add_prefix("skew:"),
        (steps.abs() > 3 * vol.shift(1)).astype(float).rolling(60).mean().add_prefix("jump:"),
    ]
    return pd.concat(features, axis=1).replace([np.inf, -np.inf], np.nan)


def persistence(steps: pd.DataFrame) -> float:
    """Agreement of two non-overlapping short windows in volatility and direction."""
    if len(steps) < 60:
        return 0.0
    current, previous = steps.iloc[-20:], steps.iloc[-40:-20]
    long_vol = steps.tail(252).std().clip(lower=_VOL_FLOOR)
    a = np.log(current.std().clip(lower=_VOL_FLOOR) / long_vol)
    b = np.log(previous.std().clip(lower=_VOL_FLOOR) / long_vol)
    vol_agreement = np.where(a * b > 0, np.minimum(np.abs(a), np.abs(b)) / np.log(2), 0)
    ma = current.sum() / (long_vol * np.sqrt(20))
    mb = previous.sum() / (long_vol * np.sqrt(20))
    trend_agreement = np.where(ma * mb > 0, np.minimum(np.abs(ma), np.abs(mb)) / 2, 0)
    return float(np.clip(np.median(0.6 * vol_agreement + 0.4 * trend_agreement), 0, 1))


def weighted_analogues(
    steps: pd.DataFrame, block_size: int, recent_start: int
) -> tuple[NDArray[np.int64], NDArray[np.float64], float]:
    """Match the state BEFORE each historical block; estimate scale on past candidates."""
    features = state_features(steps)
    starts = np.arange(120, recent_start - block_size + 1, dtype=np.int64)
    if not starts.size or features.iloc[-1].isna().any():
        return np.array([], dtype=np.int64), np.array([], dtype=float), 0.0
    matrix = features.iloc[starts - 1].to_numpy(dtype=float)
    valid = np.isfinite(matrix).all(axis=1)
    starts, matrix = starts[valid], matrix[valid]
    if not starts.size:
        return starts, np.array([], dtype=float), 0.0
    med = np.median(matrix, axis=0)
    scale = np.maximum(1.4826 * np.median(np.abs(matrix - med), axis=0), 0.1)
    distance = np.mean(((matrix - features.iloc[-1].to_numpy(dtype=float)) / scale) ** 2, axis=1)
    selected = np.argsort(distance, kind="stable")[: max(20, int(np.ceil(0.2 * len(starts))))]
    nearest = distance[selected]
    bandwidth = max(float(np.median(nearest)), 0.25)
    weights = np.exp(-0.5 * (nearest - nearest.min()) / bandwidth)
    weights /= weights.sum()
    effective_n = 1.0 / float(np.square(weights).sum())
    quality = float(np.exp(-0.5 * np.median(nearest)) * min(1.0, effective_n / 30))
    return starts[selected], weights, quality


def routing_weights(fragility: float, persistent: float, quality: float) -> NDArray[np.float64]:
    """Absolute recent/matched/full probabilities; poor analogues never gain stress weight."""
    if not all(np.isfinite(x) and 0 <= x <= 1 for x in (fragility, persistent, quality)):
        raise ValueError("routing diagnostics must be finite and in [0, 1]")
    recent = float(np.clip(0.70 - 0.25 * fragility + 0.10 * fragility * persistent, 0.30, 0.80))
    share = float(np.clip(quality * (0.50 + 0.45 * fragility * persistent), 0, 0.95))
    matched = (1 - recent) * share
    return np.array([recent, matched, 1 - recent - matched], dtype=float)


def lagged_volatility(steps: pd.DataFrame) -> pd.DataFrame:
    """Causal EWM scale: a shock cannot inflate its own standardization denominator."""
    variance = steps.pow(2).ewm(span=60, adjust=False, min_periods=20).mean().shift(1)
    return np.sqrt(variance).clip(lower=_VOL_FLOOR)


def _sample(
    steps: pd.DataFrame, baseline: NumericForecast, config: V4Config, n_draws: int, seed: int
) -> tuple[NDArray[np.float64], dict[str, Any]]:
    meta = baseline.metadata
    maximum = max(meta["observation_horizons"])
    values = steps.to_numpy(dtype=float)
    size = min(V21_CONFIG.block_size, maximum, len(values))
    recent_start = max(0, len(values) - V21_CONFIG.recent_window)
    recent = float(meta["regime"]["recent_weight"])
    share = float(meta["sampling"]["effective_state_match_share"])
    starts = np.asarray(
        _state_matched_starts(steps, size, recent_start, V21_CONFIG), dtype=np.int64
    )
    probabilities: NDArray[np.float64] | None = None
    persistent, quality = persistence(steps), 0.0
    if config.routing:
        starts, probabilities, quality = weighted_analogues(steps, size, recent_start)
        weights = routing_weights(float(meta["regime"]["fragility"]), persistent, quality)
        recent = float(weights[0])
        share = float(weights[1] / (1 - recent))
    forecast_vol = np.ones(values.shape[1])
    if config.normalize_volatility:
        sigma = lagged_volatility(steps).to_numpy(dtype=float)
        # Early rows without enough preceding observations are excluded from EVERY pool.
        valid_start = int(np.flatnonzero(np.isfinite(sigma).all(axis=1))[0])
        values = values[valid_start:] / sigma[valid_start:]
        starts = starts[starts >= valid_start] - valid_start
        recent_start = max(0, recent_start - valid_start)
        vol20 = steps.tail(20).std().clip(lower=_VOL_FLOOR).to_numpy(dtype=float)
        vol120 = steps.tail(120).std().clip(lower=_VOL_FLOOR).to_numpy(dtype=float)
        forecast_vol = np.sqrt(0.5 * vol20**2 + 0.5 * vol120**2)
    full_mean = values.mean(axis=0)
    recent_mean = values[recent_start:].mean(axis=0)
    if starts.size:
        block_means = np.array([values[s : s + size].mean(axis=0) for s in starts])
        matched_mean = np.average(block_means, axis=0, weights=probabilities)
    else:
        matched_mean = full_mean
    drift = np.array([meta["daily_drift"][a] for a in steps.columns])
    rng = np.random.default_rng(seed)
    paths = np.empty((n_draws, maximum, values.shape[1]), dtype=float)
    # Same random draw order as the legacy sampler for the no-change control.
    for draw in range(n_draws):
        for cursor in range(0, maximum, size):
            pool = float(rng.random())
            if pool < recent:
                low, high = recent_start, max(recent_start, len(values) - size)
                start = int(rng.integers(low, high + 1)) if high > low else low
                centre = recent_mean
            elif starts.size and (pool - recent) / max(1 - recent, 1e-12) < share:
                position = (
                    int(rng.choice(len(starts), p=probabilities))
                    if probabilities is not None
                    else int(rng.integers(len(starts)))
                )
                start, centre = int(starts[position]), matched_mean
            else:
                high = max(0, len(values) - size)
                start = int(rng.integers(0, high + 1)) if high > 0 else 0
                centre = full_mean
            take = min(size, maximum - cursor)
            paths[draw, cursor : cursor + take] = (
                values[start : start + take] - centre
            ) * forecast_vol * float(meta["regime"]["uncertainty_scale"]) + drift
    return paths, {
        "persistence": persistent,
        "analog_quality": quality,
        "recent_weight": recent,
        "matched_weight": (1 - recent) * share if starts.size else 0.0,
        "state_matched_block_count": len(starts),
        "normalized_volatility": config.normalize_volatility,
    }


def forecast_numeric_v4(
    histories: dict[str, pd.Series],
    assets: list[str],
    horizons: list[int],
    target_type: str,
    target_frequency: str,
    n_draws: int,
    seed: int,
    family: str,
    config: V4Config = V4_A,
    baseline: NumericForecast | None = None,
) -> NumericForecast:
    """Experimental forecast; F3 and insufficient-history cases retain exact V3 draws."""
    base = baseline or forecast_numeric_v3(
        histories, assets, horizons, target_type, target_frequency, n_draws, seed, family
    )
    if family == "T2-F3" or (not config.routing and not config.normalize_volatility):
        return NumericForecast(base.samples.copy(), copy.deepcopy(base.metadata))
    prepared = {
        a: (
            histories[a].sort_index().astype(float)
            if target_type in _RETURN_TARGETS
            else _diff_without_gaps(histories[a].sort_index().astype(float))
        )
        for a in assets
    }
    steps = pd.DataFrame(prepared).dropna().tail(V21_CONFIG.full_window)
    if len(steps) < 140:
        return NumericForecast(base.samples.copy(), copy.deepcopy(base.metadata))
    paths, diagnostics = _sample(steps, base, config, n_draws, seed)
    cumulative = np.cumsum(paths, axis=1)
    anchor = np.array([base.metadata["anchor"][a] for a in assets])
    samples = np.stack(
        [anchor + cumulative[:, h - 1] for h in base.metadata["observation_horizons"]], axis=2
    )
    if not np.isfinite(samples).all():
        raise ValueError("V4 generated non-finite samples")
    meta = copy.deepcopy(base.metadata)
    meta["model"] = config.name
    meta["v4"] = diagnostics
    meta["regime"]["recent_weight"] = diagnostics["recent_weight"]
    meta["sampling"]["state_matched_block_count"] = diagnostics["state_matched_block_count"]
    scale = samples[:, :, int(np.argmax(horizons))].std(axis=0, ddof=1) / np.sqrt(max(horizons))
    meta["daily_sd"] = {a: float(scale[i]) for i, a in enumerate(assets)}
    return NumericForecast(np.asarray(samples, dtype=np.float64), meta)


def calibrate_single_cell_tails(
    samples: NDArray[np.float64], lower: float = 1.0, upper: float = 1.0
) -> NDArray[np.float64]:
    """Stretch outside Q10/Q90 monotonically, keeping central 80% exactly unchanged.

    Q05/Q95 cannot be calibrated by a continuous transform that fixes the central 90%.
    Factors must come from a pre-validation fit split, not Development outcomes.
    """
    if not all(np.isfinite(x) and 0.75 <= x <= 1.25 for x in (lower, upper)):
        raise ValueError("tail factors must be finite and in [0.75, 1.25]")
    if samples.shape[1:] != (1, 1) or (lower == 1 and upper == 1):
        return samples.copy()
    lo, hi = np.quantile(samples, [0.1, 0.9], axis=0)
    result = np.where(samples < lo, lo + lower * (samples - lo), samples)
    return np.asarray(np.where(result > hi, hi + upper * (result - hi), result), dtype=np.float64)


def mixture_draws(
    anchor: NDArray[np.float64], candidate: NDArray[np.float64], weight: float, seed: int
) -> NDArray[np.float64]:
    """Fixed draw allocation, sampling WHOLE worlds rather than averaging predictions."""
    if anchor.shape != candidate.shape or not np.isfinite(weight) or not 0 <= weight <= 1:
        raise ValueError("mixture requires matching tensors and a weight in [0, 1]")
    result = anchor.copy()
    rng = np.random.default_rng(seed)
    chosen = rng.permutation(len(anchor))[: int(round(weight * len(anchor)))]
    result[chosen] = candidate[chosen]
    return result

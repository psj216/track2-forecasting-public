"""## Executive summary (read this first)

Research-only multi-scale path sampler on the frozen V5.1 numeric anchor.
Only historical block length changes: draw coherent 1-, 5-, or 20-observation
blocks with fixed 25/50/25 probabilities. The existing pool weights, drift,
fragility widening, target-frequency conversion, anchors, and text layer stay
unchanged. F3 returns the exact V5.1 Numeric V3 forecast object.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from .numeric_v1 import (
    _RETURN_TARGETS,
    NumericForecast,
    _diff_without_gaps,
    _sample_blocks,
    _state_matched_starts,
)
from .numeric_v3 import forecast_numeric_v3
from .numeric_v21 import V21_CONFIG


@dataclass(frozen=True)
class MultiScaleConfig:
    """Predeclared ablation; no tuning on V9 manifest labels."""

    sizes: tuple[int, ...] = (1, 5, 20)
    probabilities: tuple[float, ...] = (0.25, 0.50, 0.25)


V9_A = MultiScaleConfig()


def sample_multiscale_blocks(
    steps: pd.DataFrame,
    n_draws: int,
    max_horizon: int,
    recent_weight: float,
    uncertainty_scale: float,
    drift: NDArray[np.float64],
    seed: int,
    effective_state_match_share: float,
    mixture: MultiScaleConfig = V9_A,
) -> tuple[NDArray[np.float64], dict[str, Any]]:
    """One block start shared by every asset; uninterrupted rows form each block."""
    sizes = np.asarray(mixture.sizes, dtype=int)
    probabilities = np.asarray(mixture.probabilities, dtype=float)
    if (not len(sizes) or len(sizes) != len(probabilities)
            or (sizes < 1).any() or not np.isfinite(probabilities).all()
            or (probabilities < 0).any() or not np.isclose(probabilities.sum(), 1)):
        raise ValueError("invalid fixed multi-scale mixture")
    if len(sizes) == 1 and int(sizes[0]) == V21_CONFIG.block_size:
        # Exact ablation control, including the V2.1 pool/start RNG sequence.
        return _sample_blocks(
            steps, n_draws, max_horizon, recent_weight, uncertainty_scale,
            drift, seed, V21_CONFIG, effective_state_match_share,
        )
    rng = np.random.default_rng(seed)
    # Separate stream: a degenerate 5-day mixture reproduces the V2.1 sampler
    # exactly rather than shifting its existing pool/start RNG sequence.
    length_rng = np.random.default_rng(seed ^ 0x91A5C01)
    values = steps.to_numpy(dtype=float)
    n_rows, n_assets = values.shape
    recent_start = max(0, n_rows - V21_CONFIG.recent_window)
    full_mean = values.mean(axis=0)
    recent_mean = values[recent_start:].mean(axis=0)
    state: dict[int, tuple[int, int, list[int], NDArray[np.float64]]] = {}
    for requested in set(int(size) for size in sizes):
        size = min(requested, max_horizon, n_rows)
        matched = _state_matched_starts(steps, size, recent_start, V21_CONFIG)
        matched_mean = (
            np.concatenate([values[start : start + size] for start in matched]).mean(axis=0)
            if matched else full_mean
        )
        state[requested] = (
            max(recent_start, n_rows - size),
            max(0, n_rows - size),
            matched,
            matched_mean,
        )
    paths = np.empty((n_draws, max_horizon, n_assets), dtype=float)
    selection_counts = {int(size): 0 for size in sizes}
    cursor = np.zeros(n_draws, dtype=int)
    while np.any(cursor < max_horizon):
        active = np.flatnonzero(cursor < max_horizon)
        lengths = length_rng.choice(sizes, size=len(active), p=probabilities)
        pool_draws = rng.random(len(active))
        for requested in sizes:
            mask = lengths == requested
            ids = active[mask]
            if not len(ids):
                continue
            requested = int(requested)
            selection_counts[requested] += len(ids)
            size = min(requested, max_horizon, n_rows)
            recent_last, full_last, matched, matched_mean = state[requested]
            pool = pool_draws[mask]
            recent = pool < recent_weight
            analogue = (~recent & bool(matched)
                        & ((pool - recent_weight) / max(1 - recent_weight, 1e-12)
                           < effective_state_match_share))
            full = ~recent & ~analogue
            starts = np.empty(len(ids), dtype=int)
            centres = np.empty((len(ids), n_assets), dtype=float)
            if np.any(recent):
                count = int(recent.sum())
                starts[recent] = (rng.integers(recent_start, recent_last + 1, size=count)
                                  if recent_last > recent_start else recent_start)
                centres[recent] = recent_mean
            if np.any(analogue):
                starts[analogue] = np.asarray(matched)[rng.integers(
                    0, len(matched), size=int(analogue.sum())
                )]
                centres[analogue] = matched_mean
            if np.any(full):
                starts[full] = (rng.integers(0, full_last + 1, size=int(full.sum()))
                                if full_last > 0 else 0)
                centres[full] = full_mean
            for offset in range(size):
                valid = cursor[ids] + offset < max_horizon
                valid_ids = ids[valid]
                paths[valid_ids, cursor[valid_ids] + offset, :] = (
                    values[starts[valid] + offset] - centres[valid]
                ) * uncertainty_scale + drift
            cursor[ids] = np.minimum(cursor[ids] + size, max_horizon)
    return paths, {
        "configured_state_match_share": V21_CONFIG.state_match_share,
        "effective_state_match_share": effective_state_match_share,
        "state_matched_block_count": {
            str(size): len(state[int(size)][2]) for size in sizes
        },
        "block_lengths": list(map(int, sizes)),
        "block_probabilities": probabilities.tolist(),
        "block_selection_counts": selection_counts,
    }


def forecast_numeric_v9a(
    histories: dict[str, pd.Series],
    assets: list[str],
    horizons: list[int],
    target_type: str,
    target_frequency: str,
    n_draws: int,
    seed: int,
    family: str,
    mixture: MultiScaleConfig = V9_A,
) -> NumericForecast:
    """Preserve baseline metadata and replace sampled paths outside frozen F3."""
    baseline = forecast_numeric_v3(
        histories, assets, horizons, target_type, target_frequency, n_draws, seed, family
    )
    return apply_multiscale_paths(
        baseline, histories, assets, target_type, n_draws, seed, family, mixture
    )


def apply_multiscale_paths(
    baseline: NumericForecast,
    histories: dict[str, pd.Series],
    assets: list[str],
    target_type: str,
    n_draws: int,
    seed: int,
    family: str,
    mixture: MultiScaleConfig = V9_A,
) -> NumericForecast:
    """Apply the ablation to an already computed V5.1 numeric forecast."""
    if family == "T2-F3":
        return baseline
    prepared = {
        asset: (histories[asset].sort_index().astype(float)
                if target_type in _RETURN_TARGETS
                else _diff_without_gaps(histories[asset].sort_index().astype(float)))
        for asset in assets
    }
    steps = pd.DataFrame(prepared).dropna()
    maximum = max(baseline.metadata["observation_horizons"])
    regime = baseline.metadata["regime"]
    effective_share = V21_CONFIG.state_match_share * (1 - float(regime["fragility"]))
    drift = np.array([baseline.metadata["daily_drift"][asset] for asset in assets])
    path_steps, sampling = sample_multiscale_blocks(
        steps.tail(min(V21_CONFIG.full_window, len(steps))),
        n_draws,
        maximum,
        float(regime["recent_weight"]),
        float(regime["uncertainty_scale"]),
        drift,
        seed,
        effective_share,
        mixture,
    )
    cumulative = np.cumsum(path_steps, axis=1)
    anchor = np.asarray([baseline.metadata["anchor"][asset] for asset in assets])
    samples = np.empty_like(baseline.samples)
    for horizon_index, observation_horizon in enumerate(baseline.metadata["observation_horizons"]):
        samples[:, :, horizon_index] = anchor + cumulative[:, observation_horizon - 1, :]
    if not np.isfinite(samples).all():
        raise ValueError("V9-A path produced non-finite samples")
    meta = dict(baseline.metadata)
    meta.update(model="v9-a-multi-scale", sampling=sampling)
    return NumericForecast(samples=samples, metadata=meta)

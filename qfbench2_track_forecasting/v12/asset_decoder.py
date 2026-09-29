"""Frozen one-dimensional conditional law shared by V12 and V13."""

from __future__ import annotations

import numpy as np

from .horizon_expert import predict
from .state_transition import probabilities, state_features


def law(artifact: dict, x: np.ndarray, g: np.ndarray, coverage: np.ndarray,
        asset_index: int, horizon: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    raw = state_features(x, g, coverage, horizon)
    p = probabilities(raw, artifact)
    loading = np.asarray(artifact["decoder_loadings"])[asset_index]
    covariance = np.asarray(artifact["state_covariance"])
    residual_var = float(artifact["residual_sd"][asset_index]) ** 2
    variance = np.einsum("i,sij,j->s", loading, covariance, loading) + residual_var
    scale = np.sqrt(max(horizon, 1) / 21.)
    location = np.asarray(artifact["state_location"]) @ loading
    reliability = float(artifact["location_reliability"])
    expert = float(predict(x[asset_index:asset_index+1], horizon,
                           np.asarray(artifact["long_expert"]))[0])
    mean = reliability * (float(artifact["decoder_mean"][asset_index]) + location) * scale + expert
    return p, mean, np.sqrt(np.maximum(variance, 1e-10)) * scale


def sample_cell(artifact: dict, x: np.ndarray, g: np.ndarray,
                coverage: np.ndarray, asset_index: int, horizon: int,
                n: int, rng: np.random.Generator) -> np.ndarray:
    """Samples frozen marginal law directly, without invoking the joint generator."""
    from .residual_model import radial
    p, mean, sd = law(artifact, x, g, coverage, asset_index, horizon)
    state = rng.choice(5, size=n, p=p)
    return mean[state] + sd[state] * rng.standard_normal(n) * radial(
        rng, float(artifact["student_df"]), (n,))

"""## Executive summary (read this first)

Numeric v3 is an experimental dynamic cross-asset transmission layer over the frozen V2.1
distribution. It estimates a recent-versus-long correlation regime, regularizes that regime into
latent eigen-factors, and transports the sampled worlds toward the current dependence structure.

The transport uses rank reordering. Every asset-horizon keeps exactly the same marginal draws as
V2.1, so its centre, width, skew and tails cannot change. Only which asset outcomes occur together
inside a draw changes. Single-asset cards bypass the layer exactly. No semantic shock label is
invented from numeric data; policy, inflation and growth labels belong to the later text engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from .numeric_v1 import NumericForecast, _diff_without_gaps
from .numeric_v21 import forecast_numeric_v21

_EIGEN_FLOOR = 1e-6


@dataclass(frozen=True)
class TransmissionConfig:
    """Auditable settings for one dynamic dependence candidate."""

    name: str
    strength: float = 0.50
    recent_window: int = 60
    long_window: int = 252
    recent_weight_base: float = 0.65
    recent_weight_fragility_slope: float = 0.50
    identity_shrinkage: float = 0.10


V3_CONFIG = TransmissionConfig(
    name="F3-routed dynamic latent-factor transmission v3",
    strength=0.25,
    long_window=1260,
    identity_shrinkage=0.0,
)


def _nearest_correlation(matrix: NDArray[np.float64]) -> NDArray[np.float64]:
    """Return a finite positive-semidefinite correlation matrix."""
    symmetric = 0.5 * (matrix + matrix.T)
    values, vectors = np.linalg.eigh(np.nan_to_num(symmetric, nan=0.0))
    positive = vectors @ np.diag(np.clip(values, _EIGEN_FLOOR, None)) @ vectors.T
    scale = np.sqrt(np.clip(np.diag(positive), _EIGEN_FLOOR, None))
    correlation = positive / np.outer(scale, scale)
    np.fill_diagonal(correlation, 1.0)
    return np.asarray(correlation, dtype=np.float64)


def _matrix_power(matrix: NDArray[np.float64], power: float) -> NDArray[np.float64]:
    """Stable symmetric matrix power for correlation transport."""
    values, vectors = np.linalg.eigh(_nearest_correlation(matrix))
    powered = vectors @ np.diag(np.clip(values, _EIGEN_FLOOR, None) ** power) @ vectors.T
    return np.asarray(powered, dtype=np.float64)


def _target_correlation(
    steps: pd.DataFrame,
    fragility: float,
    config: TransmissionConfig,
) -> tuple[NDArray[np.float64], float, NDArray[np.float64]]:
    """Blend recent and long dependence, trusting recent data less when it is fragile."""
    n_assets = steps.shape[1]
    identity = np.eye(n_assets, dtype=float)
    long = steps.tail(min(config.long_window, len(steps))).corr().to_numpy(dtype=float)
    recent = steps.tail(min(config.recent_window, len(steps))).corr().to_numpy(dtype=float)
    recent_weight = float(
        np.clip(
            config.recent_weight_base - config.recent_weight_fragility_slope * fragility,
            0.15,
            0.75,
        )
    )
    blended = recent_weight * recent + (1.0 - recent_weight) * long
    regularized = (1.0 - config.identity_shrinkage) * blended + config.identity_shrinkage * identity
    target = _nearest_correlation(regularized)
    eigenvalues = np.linalg.eigvalsh(target)[::-1]
    return target, recent_weight, np.asarray(eigenvalues, dtype=np.float64)


def _rank_transport(
    samples: NDArray[np.float64],
    target_correlation: NDArray[np.float64],
    strength: float,
    reference_horizon_index: int,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Reorder each marginal toward a target correlation without changing its values."""
    n_draws, n_assets, n_horizons = samples.shape
    max_horizon_values = samples[:, :, reference_horizon_index]
    source_correlation = _nearest_correlation(
        np.asarray(np.corrcoef(max_horizon_values, rowvar=False), dtype=np.float64)
    )
    transport = _matrix_power(source_correlation, -0.5) @ _matrix_power(target_correlation, 0.5)
    blend = (1.0 - strength) * np.eye(n_assets) + strength * transport

    transformed = np.empty_like(samples)
    for horizon_index in range(n_horizons):
        values = samples[:, :, horizon_index]
        means = values.mean(axis=0)
        scales = values.std(axis=0, ddof=1)
        scales = np.clip(scales, _EIGEN_FLOOR, None)
        scores = ((values - means) / scales) @ blend
        for asset_index in range(n_assets):
            order = np.argsort(scores[:, asset_index], kind="mergesort")
            sorted_values = np.sort(values[:, asset_index], kind="mergesort")
            transformed[order, asset_index, horizon_index] = sorted_values

    output_correlation = _nearest_correlation(
        np.asarray(
            np.corrcoef(transformed[:, :, reference_horizon_index], rowvar=False),
            dtype=np.float64,
        )
    )
    return transformed, source_correlation, output_correlation


def apply_dynamic_transmission(
    baseline: NumericForecast,
    histories: dict[str, pd.Series],
    assets: list[str],
    target_type: str,
    config: TransmissionConfig,
    family: str = "T2-F3",
    reference_horizon_index: int = -1,
) -> NumericForecast:
    """Change only cross-asset draw pairing under the current correlation regime."""
    if family != "T2-F3" or len(assets) < 2 or config.strength <= 0.0:
        return NumericForecast(samples=baseline.samples.copy(), metadata=dict(baseline.metadata))

    return_targets = {"log_return", "return", "simple_return", "pct_change"}
    prepared = {
        asset: (
            histories[asset].sort_index().astype(float)
            if target_type in return_targets
            else _diff_without_gaps(histories[asset].sort_index().astype(float))
        )
        for asset in assets
    }
    steps = pd.DataFrame(prepared).dropna()
    fragility = float(baseline.metadata["regime"]["fragility"])
    target, recent_weight, eigenvalues = _target_correlation(steps, fragility, config)
    samples, source, output = _rank_transport(
        baseline.samples,
        target,
        float(np.clip(config.strength, 0.0, 1.0)),
        reference_horizon_index,
    )

    metadata: dict[str, Any] = dict(baseline.metadata)
    metadata["model"] = config.name
    metadata["transmission"] = {
        "strength": config.strength,
        "recent_window": config.recent_window,
        "long_window": config.long_window,
        "recent_weight": recent_weight,
        "identity_shrinkage": config.identity_shrinkage,
        "source_correlation": source.tolist(),
        "target_correlation": target.tolist(),
        "output_correlation": output.tolist(),
        "latent_eigenvalues": eigenvalues.tolist(),
        "first_factor_variance_share": float(eigenvalues[0] / eigenvalues.sum()),
    }
    return NumericForecast(samples=samples, metadata=metadata)


def forecast_numeric_v3(
    histories: dict[str, pd.Series],
    assets: list[str],
    horizons: list[int],
    target_type: str,
    target_frequency: str,
    n_draws: int,
    seed: int,
    family: str,
    config: TransmissionConfig = V3_CONFIG,
) -> NumericForecast:
    """Generate V2.1 marginals and dynamically pair them into joint worlds."""
    baseline = forecast_numeric_v21(
        histories,
        assets,
        horizons,
        target_type,
        target_frequency,
        n_draws,
        seed,
    )
    return apply_dynamic_transmission(
        baseline,
        histories,
        assets,
        target_type,
        config,
        family=family,
        reference_horizon_index=int(np.argmax(horizons)),
    )

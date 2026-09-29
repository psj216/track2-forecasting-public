"""Draw complete joint worlds, coupling the same latent shock across horizons."""

from __future__ import annotations

import numpy as np

from .asset_decoder import law
from .residual_model import radial


def worlds(artifact: dict, x: np.ndarray, g: np.ndarray, coverage: np.ndarray,
           asset_indices: list[int], horizons: list[int], n: int, seed: int) -> np.ndarray:
    if n <= 0 or any(h <= 0 for h in horizons):
        raise ValueError("Positive draws and horizons required")
    rng = np.random.default_rng(seed)
    # A common Brownian shock gives coherent within-asset and cross-asset paths.
    hs = sorted(set(horizons))
    z_factor = np.zeros((n, 5))
    z_idio = np.zeros((n, len(asset_indices)))
    previous = 0
    factor_at, idio_at = {}, {}
    for h in hs:
        gap = h - previous
        z_factor += np.sqrt(gap) * rng.standard_normal((n, 5))
        z_idio += np.sqrt(gap) * rng.standard_normal((n, len(asset_indices)))
        factor_at[h] = z_factor.copy() / np.sqrt(h)
        idio_at[h] = z_idio.copy() / np.sqrt(h)
        previous = h
    shared_state_u = rng.random(n)
    radial_shock = radial(rng, float(artifact["student_df"]), (n,))
    output = np.empty((n, len(horizons), len(asset_indices)))
    loading = np.asarray(artifact["decoder_loadings"])
    residual_sd = np.asarray(artifact["residual_sd"])
    covariance = np.asarray(artifact["state_covariance"])
    for j, h in enumerate(horizons):
        # Joint state draws are conditional on the synchronized current date.
        for k, a in enumerate(asset_indices):
            p, mean, sd = law(artifact, x, g, coverage, a, h)
            state = np.searchsorted(np.cumsum(p), shared_state_u).clip(max=4)
            # Same factor path for all assets; diagonal residual shares its time path.
            shock = np.empty(n)
            for s in range(5):
                sel = state == s
                if not np.any(sel):
                    continue
                chol = np.linalg.cholesky(covariance[s] + 1e-8 * np.eye(5))
                factor = factor_at[h][sel] @ chol.T
                shock[sel] = factor @ loading[a] + idio_at[h][sel, k] * residual_sd[a]
            output[:, j, k] = mean[state] + np.sqrt(h / 21.) * radial_shock * shock
    if not np.all(np.isfinite(output)):
        raise ValueError("Non-finite joint forecast")
    return output

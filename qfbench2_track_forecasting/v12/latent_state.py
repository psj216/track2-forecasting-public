"""Five-factor masked PCA and five ordinal conditional future states."""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize


def psd(matrix: np.ndarray, floor: float = 1e-7) -> np.ndarray:
    a = (matrix + matrix.T) / 2
    val, vec = np.linalg.eigh(a)
    return (vec * np.maximum(val, floor)) @ vec.T


def softmax(z: np.ndarray) -> np.ndarray:
    z = z - np.max(z, axis=-1, keepdims=True)
    p = np.exp(z)
    return p / np.sum(p, axis=-1, keepdims=True)


def fit_classifier(x: np.ndarray, labels: np.ndarray, states: int = 5) -> np.ndarray:
    n, p = x.shape
    target = np.eye(states)[labels]
    def objective(flat: np.ndarray) -> tuple[float, np.ndarray]:
        w = flat.reshape(p, states)
        prob = softmax(x @ w)
        loss = -np.sum(target * np.log(np.maximum(prob, 1e-12))) / n + 0.05 * np.sum(w*w)
        grad = x.T @ (prob - target) / n + 0.1 * w
        return float(loss), grad.ravel()
    result = minimize(objective, np.zeros(p * states), jac=True, method="L-BFGS-B")
    if not result.success and not np.all(np.isfinite(result.x)):
        raise ValueError("state classifier did not converge")
    return result.x.reshape(p, states)


def fit_factors(y: np.ndarray, mask: np.ndarray, factors: int = 5):
    """Fit unit-neutral PCA, then convert decoder loadings back to native units."""
    n, a = y.shape
    counts = mask.sum(axis=0).clip(min=1)
    mean = (y * mask).sum(axis=0) / counts
    centered = np.where(mask, y - mean, 0)
    pair = mask.astype(float).T @ mask.astype(float)
    raw_cov = centered.T @ centered / np.maximum(pair - 1, 1)
    scale = np.sqrt(np.maximum(np.diag(raw_cov), 1e-8))
    standardized = centered / scale
    cov = standardized.T @ standardized / np.maximum(pair - 1, 1)
    cov = psd(0.8 * cov + 0.2 * np.eye(a))
    values, vectors = np.linalg.eigh(cov)
    axes = vectors[:, -min(factors, a):][:, ::-1]
    if axes.shape[1] < factors:
        axes = np.pad(axes, ((0, 0), (0, factors - axes.shape[1])))
    scores = standardized @ axes
    return mean, axes * scale[:, None], scores, float(np.sum(values[-factors:]) / np.sum(values)), scale, axes / scale[:, None]

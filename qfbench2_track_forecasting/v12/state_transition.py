"""As-of feature normalization and state probabilities; fitting only in training."""

import numpy as np

from .latent_state import softmax


def state_features(x: np.ndarray, g: np.ndarray, coverage: np.ndarray, horizon: int) -> np.ndarray:
    valid = x[coverage]
    mean = np.mean(valid, axis=0) if len(valid) else np.zeros(x.shape[1])
    dispersion = np.std(valid, axis=0) if len(valid) else np.zeros(x.shape[1])
    return np.r_[1., mean, dispersion, g, float(np.mean(coverage)), np.log1p(horizon)]


def probabilities(raw: np.ndarray, artifact: dict) -> np.ndarray:
    center = np.asarray(artifact["feature_center"])
    scale = np.asarray(artifact["feature_scale"])
    normalized = np.clip((raw - center) / scale, -8, 8)
    normalized[0] = 1.
    p = softmax(normalized @ np.asarray(artifact["state_logits"]))
    # Unsupported sparse inputs use the frozen prior instead of overconfident states.
    coverage = raw[-2]
    threshold = artifact["coverage_floor"]
    reliability = min(1., max(0., coverage / max(threshold, 1e-6)))
    return reliability * p + (1 - reliability) * np.asarray(artifact["state_prior"])

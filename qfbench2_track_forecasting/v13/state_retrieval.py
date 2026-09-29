"""Nineteen frozen state features; cutoff-safe 32-neighbor retrieval."""

import numpy as np


def state_vector(local_features: np.ndarray, available: np.ndarray) -> np.ndarray:
    active = local_features[available]
    return np.mean(active, axis=0) if len(active) else np.zeros(19)


def nearest(current: np.ndarray, bank_vectors: np.ndarray,
            eligible: np.ndarray, k: int = 32) -> np.ndarray:
    indices = np.flatnonzero(eligible)
    if not len(indices):
        return indices
    reference = bank_vectors[indices]
    scale = np.maximum(np.std(reference, axis=0), 0.1)
    distance = np.sum(((reference - current) / scale) ** 2, axis=1)
    return indices[np.argsort(distance, kind="stable")[:k]]

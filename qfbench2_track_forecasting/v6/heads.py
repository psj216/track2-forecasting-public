"""## Executive summary (read this first)

Apply bounded family specialists to shared empirical event paths. F3 permutes whole
asset paths, preserving every asset-horizon marginal exactly. Other heads retain the
baseline outside their calibrated transformation or stratified mixture sleeve.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class Candidate:
    name: str
    strength: float
    vol_scaled: bool = False
    tail_fraction: float = 0.0


def candidates(family: str) -> tuple[Candidate, ...]:
    if family == "T2-F1":
        return (Candidate("center-width-10", 0.10), Candidate("center-width-20", 0.20, True))
    if family == "T2-F3":
        return (Candidate("joint-15", 0.15), Candidate("joint-30", 0.30))
    result = (
        Candidate("raw-10", 0.10),
        Candidate("raw-20", 0.20),
        Candidate("scaled-20", 0.20, True),
        Candidate("raw-30", 0.30),
    )
    return result + (Candidate("body-tail", 0.20, True, 0.05),) if family == "T2-F4" else result


def apply_head(
    base: NDArray[np.float64],
    paths: NDArray[np.float64],
    weights: NDArray[np.float64],
    anchor: NDArray[np.float64],
    family: str,
    target: str,
    config: Candidate,
    trust: float,
    seed: int,
) -> NDArray[np.float64]:
    if trust <= 0 or len(paths) == 0:
        return base
    rng = np.random.default_rng(seed ^ 0x6E610)
    n = len(base)
    strength = config.strength * trust
    current = paths + (anchor[None, :, None] if target == "level" else 0.0)
    if family == "T2-F1":
        center = np.median(base, axis=0)
        event_center = np.sum(current * weights[:, None, None], axis=0)
        spread = np.maximum(np.std(base, axis=0), 1e-8)
        shift = np.clip(event_center - center, -spread, spread) * strength
        event_sd = np.sqrt(np.sum(weights[:, None, None] * (current - event_center) ** 2, axis=0))
        factor = np.clip(1 + strength * (event_sd / spread - 1), 0.9, 1.1)
        return np.asarray(center + shift + (base - center) * factor, dtype=np.float64)
    if family == "T2-F3":
        if base.shape[1] < 2:
            return base
        idx = rng.choice(len(paths), n, p=weights)
        reference = -1
        analog = current[idx, :, reference]
        analog = (analog - analog.mean(0)) / np.maximum(analog.std(0), 1e-8)
        initial = base[:, :, reference]
        initial = (initial - initial.mean(0)) / np.maximum(initial.std(0), 1e-8)
        score = (1 - strength) * initial + strength * analog
        out = base.copy()
        for a in range(base.shape[1]):
            source = np.argsort(base[:, a, reference], kind="stable")
            destination = np.argsort(score[:, a], kind="stable")
            out[destination, a, :] = base[source, a, :]
        return out
    count = int(n * strength)
    if count < 1:
        return base
    # Systematic allocation avoids random episode-count noise at low draw counts.
    u = (np.arange(count) + rng.random()) / count
    chosen = np.searchsorted(np.cumsum(weights), u, side="right").clip(max=len(paths) - 1)
    rng.shuffle(chosen)
    if family == "T2-F4" and config.tail_fraction:
        tail_count = min(count, int(n * config.tail_fraction * trust))
        magnitude = np.max(np.abs(paths / np.maximum(np.std(paths, axis=0), 1e-8)), axis=(1, 2))
        extreme = np.flatnonzero(magnitude >= np.quantile(magnitude, 0.8))
        if tail_count and len(extreme) >= 2:
            ew = weights[extreme]
            ew = ew / ew.sum()
            chosen[:tail_count] = rng.choice(extreme, tail_count, p=ew)
    out = base.copy()
    positions = rng.choice(n, count, replace=False)
    out[positions] = current[chosen]
    return out

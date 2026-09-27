"""## Executive summary (read this first)

Rank causal event fingerprints by compatible economic features. Select disjoint
response windows and report effective support rather than counting duplicate speeches.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .fingerprint import Fingerprint
from .responses import Response


def similarity(a: Fingerprint, b: Fingerprint, family: str) -> float:
    # Monetary transmission differs by issuer; a Fed hike is not a BoJ hike.
    if a.major in {"policy", "guidance", "inflation", "growth"} and a.issuer != b.issuer:
        return 0.0
    ax = a.delta if family == "T2-F1" else a.axes
    bx = b.delta if family == "T2-F1" else b.axes
    if not ax or not bx:
        return 0.0
    keys = set(ax) | set(bx)
    av = np.array([ax.get(k, 0.0) for k in sorted(keys)])
    bv = np.array([bx.get(k, 0.0) for k in sorted(keys)])
    cosine = float(av @ bv / max(1e-12, np.linalg.norm(av) * np.linalg.norm(bv)))
    if cosine <= 0.2:
        return 0.0
    words_a, words_b = set(a.tokens), set(b.tokens)
    overlap = len(words_a & words_b) / max(1, len(words_a | words_b))
    return float(
        0.55 * cosine
        + 0.15 * (a.major == b.major)
        + 0.15 * (a.issuer == b.issuer)
        + 0.05 * (a.region == b.region)
        + 0.05 * (a.currentness == b.currentness)
        + 0.05 * overlap
    )


def retrieve(
    query: Fingerprint, responses: list[Response], family: str, max_items: int = 24
) -> tuple[list[Response], NDArray[np.float64], float]:
    ranked = sorted(
        [(similarity(query, r.event.fingerprint, family), r) for r in responses],
        key=lambda pair: (pair[0], pair[1].event.published_at),
        reverse=True,
    )
    selected: list[Response] = []
    scores = []
    episodes = set()
    for score, response in ranked:
        if score < 0.5 or response.event.episode_id in episodes:
            continue
        if any(not (response.end < old.start or response.start > old.end) for old in selected):
            continue
        selected.append(response)
        scores.append(score)
        episodes.add(response.event.episode_id)
        if len(selected) >= max_items:
            break
    weights: NDArray[np.float64] = np.asarray(scores, dtype=np.float64) ** 3
    if len(weights):
        weights /= weights.sum()
    ess = float(1 / np.sum(weights**2)) if len(weights) else 0.0
    return selected, weights, ess

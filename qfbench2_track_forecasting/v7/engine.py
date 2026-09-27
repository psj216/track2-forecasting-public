"""## Executive summary (read this first)

Use V5.1 unchanged outside F2. F2 adds a small empirical event sleeve when
compatible, independent and fully matured historical responses exist.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from ..v6.responses import frame_at
from .catalog import load_catalog
from .encoder import current_queries
from .retrieval import retrieve, similarity


def reliability(ess: float, mean_similarity: float, confidence: float) -> float:
    # Fixed before outer evaluation; zero support is an exact fallback.
    coverage = min(1.0, ess / 8.0)
    return float(np.clip(coverage * mean_similarity * confidence, 0, 1))


def sleeve_share(score: float) -> float:
    # Deliberately conservative. Any calibration must use older training folds only.
    return 0.0 if score < 0.15 else min(0.12, 0.04 + 0.12 * (score - 0.15))


def apply_v7(
    base: NDArray[np.float64],
    histories: dict[str, pd.Series],
    assets: list[str],
    horizons: list[int],
    target: str,
    frequency: str,
    family: str,
    asof: str,
    seed: int,
    text_dir: Path,
    catalog_root: Path | None = None,
) -> tuple[NDArray[np.float64], dict[str, Any]]:
    meta: dict[str, Any] = {
        "config": "v7-f2-event-memory",
        "applied": False,
        "baseline_fallback_exact": True,
        "reason": "family_frozen",
        "encoder_version": 1,
        "retriever_version": 1,
    }
    if family != "T2-F2":
        return base, meta
    if target not in {"level", "log_return"} or any(a not in histories for a in assets):
        meta["reason"] = "unsupported_grid"
        return base, meta
    root = catalog_root or Path(os.environ.get("V7_CATALOG_PATH", "/opt/v7_catalog"))
    if not (root / "catalog_manifest.json").is_file():
        meta["reason"] = "catalog_unavailable"
        return base, meta
    events, manifest = load_catalog(root, asof)
    meta.update(catalog_version=manifest["catalog_version"], catalog_records=len(events))
    queries = current_queries(text_dir, asof)
    if not queries:
        meta["reason"] = "no_current_event"
        return base, meta
    frame = frame_at(histories, assets, asof)
    if len(frame) < 100:
        meta["reason"] = "insufficient_panel_history"
        return base, meta
    # The freshest interpreted event is the current card's evidence. Choosing an
    # older document solely because it has more analogs creates stale activation.
    freshest = queries[0].published_at
    ranked = []
    for q in (item for item in queries if item.published_at == freshest):
        pool, weights, ess = retrieve(q, events, frame, horizons, target, frequency, asof)
        quality = float(np.dot(weights, [similarity(q, r.event) for r in pool])) if pool else 0.0
        trust = reliability(ess, quality, q.fingerprint.confidence)
        ranked.append((trust, q, pool, weights, ess))
    trust, query, pool, weights, ess = max(ranked, key=lambda row: row[0])
    alpha = sleeve_share(trust)
    meta.update(
        eligible=bool(pool),
        query_doc_id=query.doc_id,
        query_event_type=query.event_type,
        query_date=query.published_at,
        analog_count=len(pool),
        effective_sample_size=ess,
        reliability=trust,
        sleeve=alpha,
    )
    if not pool or int(len(base) * alpha) == 0:
        meta["reason"] = "weak_event_support"
        return base, meta
    if base.shape[1:] != (len(assets), len(horizons)):
        raise ValueError("V7 draw grid mismatch")
    count = int(len(base) * alpha)
    rng = np.random.default_rng(seed ^ 0x736E7)
    positions = rng.choice(len(base), count, replace=False)
    systematic = (np.arange(count) + rng.random()) / count
    indices = np.searchsorted(np.cumsum(weights), systematic, side="right").clip(max=len(pool) - 1)
    rng.shuffle(indices)
    anchor = frame.iloc[-1].to_numpy(dtype=float)
    out = base.copy()
    for position, index in zip(positions, indices, strict=True):
        out[position] = pool[index].path + (anchor[:, None] if target == "level" else 0.0)
    meta.update(
        applied=True,
        baseline_fallback_exact=False,
        reason="event_sleeve",
        max_response_date=max(str(r.end.date()) for r in pool),
        analog_dates=[r.event.published_at for r in pool],
        analog_sources=[r.event.source_url for r in pool],
    )
    return out, meta

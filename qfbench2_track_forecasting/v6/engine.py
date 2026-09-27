"""## Executive summary (read this first)

Gate all four family specialists behind a causal event library and per-card historical
selection. Every rejection returns the same baseline buffer supplied by V5.1.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from .catalog import load_catalog
from .fingerprint import current_fingerprint
from .responses import extract, frame_at
from .retrieval import retrieve
from .walkforward import calibrate, materialize


def apply_v6(
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
    value_unit: str,
    catalog_root: Path | None = None,
) -> tuple[NDArray[np.float64], dict[str, Any]]:
    meta = {
        "config": "v6-full",
        "applied": False,
        "baseline_fallback_exact": True,
        "reason": "unsupported_grid",
    }
    if family not in {"T2-F1", "T2-F2", "T2-F3", "T2-F4"} or target not in {"level", "log_return"}:
        return base, meta
    if family == "T2-F3" and len(assets) < 2:
        return base, meta
    if any(a not in histories for a in assets):
        return base, meta
    if base.shape[1:] != (len(assets), len(horizons)):
        raise ValueError("V6 draw grid mismatch")
    root = catalog_root or Path(os.environ.get("V6_CATALOG_PATH", "/opt/v6_catalog"))
    if not (root / "index.json").is_file():
        meta["reason"] = "catalog_unavailable"
        return base, meta
    records = load_catalog(root, asof)
    query = current_fingerprint(text_dir, asof, family)
    if query is None:
        meta["reason"] = "no_qualified_current_fingerprint"
        return base, meta
    meta.update(fingerprint=query.payload(), catalog_records=len(records))
    frame = frame_at(histories, assets, asof)
    if len(frame) < 180:
        meta["reason"] = "insufficient_panel_history"
        return base, meta
    responses = [
        r
        for e in records
        if (r := extract(frame, e, horizons, target, frequency, asof)) is not None
    ]
    pool, weights, ess = retrieve(query, responses, family)
    meta.update(analog_count=len(pool), effective_sample_size=ess)
    if ess < 4:
        meta["reason"] = "insufficient_effective_support"
        return base, meta
    config, calibration = calibrate(
        frame, records, query, assets, horizons, target, frequency, family, asof, seed, value_unit
    )
    meta["calibration"] = calibration
    if config is None:
        meta["reason"] = calibration["reason"]
        return base, meta
    out = materialize(
        base, pool, weights, ess, frame, family, target, config, query.confidence, seed
    )
    changed = not np.array_equal(out, base)
    meta.update(
        applied=changed,
        baseline_fallback_exact=not changed,
        reason="validated_event_response" if changed else "unchanged",
        selected=config.name,
        max_response_date=max(str(r.end.date()) for r in pool),
        analog_sources=[r.event.source_url for r in pool],
        analog_dates=[r.event.published_at for r in pool],
    )
    return out, meta

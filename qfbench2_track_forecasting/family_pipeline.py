"""## Executive summary (read this first)

Run opt-in family specialists on the unchanged V3 numeric anchor. F1 may load a
strictly earlier fitted calibration; F2/F4 use a grounded text route to sample
historical worlds. F3 returns the original draws without a model call. This is
an experimental pipeline, not a claim of leaderboard improvement.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from .family_calibration import apply_family_calibration, load_family_calibration
from .historical_heads import apply_historical_head
from .regime_router import interpret_regime


def run_family_heads(
    samples: NDArray[np.float64],
    histories: dict[str, pd.Series],
    assets: list[str],
    horizons: list[int],
    target_type: str,
    target_frequency: str,
    family: str,
    asof: str,
    seed: int,
    text_dir: Path,
    *,
    enabled: bool,
    panel_context: dict[str, Any] | None = None,
) -> tuple[NDArray[np.float64], dict[str, Any]]:
    """Record each failure/gate explicitly while preserving exact fallback draws."""
    meta: dict[str, Any] = {
        "enabled": enabled,
        "family": family,
        "config": "v3-family-heads-experimental",
        "applied": False,
        "numeric_fallback_exact": True,
        "reason": "disabled" if not enabled else "family frozen",
        "samples_changed": False,
    }
    if not enabled or family == "T2-F3":
        return samples.copy(), meta
    if family == "T2-F1":
        config_path = os.environ.get("F1_CALIBRATION_PATH", "").strip()
        if not config_path:
            meta["reason"] = "no admitted F1 calibration configured"
            return samples.copy(), meta
        try:
            raw = json.loads(Path(config_path).read_text(encoding="utf-8"))
            config = load_family_calibration(Path(config_path))
            output = apply_family_calibration(
                samples,
                histories,
                assets,
                horizons,
                target_type,
                family,
                asof,
                config,
            )
        except (OSError, ValueError, TypeError, KeyError):
            meta["reason"] = "F1 calibration invalid, unavailable, or not earlier than as-of"
            return samples.copy(), meta
        changed = not np.array_equal(output, samples)
        meta.update(
            applied=changed,
            samples_changed=changed,
            numeric_fallback_exact=not changed,
            calibration=raw,
            reason="F1 calibration applied" if changed else "F1 identity",
        )
        return output, meta
    if family not in {"T2-F2", "T2-F4"}:
        return samples.copy(), meta
    route = interpret_regime(
        text_dir=text_dir,
        family=family,
        asof=asof,
        assets=assets,
        horizons=horizons,
        target_type=target_type,
        panel_context=panel_context,
    )
    if route.gate_passed:
        try:
            output, head = apply_historical_head(
                samples,
                histories,
                assets,
                horizons,
                target_type,
                target_frequency,
                family,
                asof,
                seed,
                route.decision,
                evidence_valid=True,
                direction_asset=route.decision.direction_asset if route.decision else None,
            )
            meta.update(head)
        except ValueError:
            output = samples.copy()
            meta["reason"] = "historical head rejected input"
    else:
        output = samples.copy()
        meta["reason"] = "text route did not pass evidence/confidence gate"
    changed = not np.array_equal(output, samples)
    meta.update(
        applied=changed,
        samples_changed=changed,
        numeric_fallback_exact=not changed,
        config="v3-family-heads-experimental",
        router=route.metadata(samples_changed=changed),
    )
    return output, meta

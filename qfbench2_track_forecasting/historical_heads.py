"""## Executive summary (read this first)

Opt-in F2 and F4 heads replace a bounded number of complete V3 worlds with actual
past trajectories. Text selects a direction and horizon, never a numeric shock.
Past trajectories have numeric labels only: a policy narrative does not prove
that an old positive block was a policy event. Caps are experimental, not fitted.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from .numeric_v1 import _diff_without_gaps, _observation_period_business_days

if TYPE_CHECKING:
    from .regime_router import RegimeDecision


def apply_historical_head(
    samples: NDArray[np.float64],
    histories: dict[str, pd.Series],
    assets: list[str],
    horizons: list[int],
    target_type: str,
    target_frequency: str,
    family: str,
    asof: str,
    seed: int,
    decision: RegimeDecision | None,
    *,
    evidence_valid: bool = False,
    direction_asset: str | None = None,
) -> tuple[NDArray[np.float64], dict[str, Any]]:
    """Use only pre-cutoff history and a trusted evidence gate; otherwise exact V3.

    Direction means a rise/fall in the quoted target, not currency strength or a
    generic policy rate. Multi-asset callers must explicitly identify that target.
    The reference horizon conditions selection, but an entire historical path is
    always copied. Simple-return compounding is deliberately unsupported here.
    """
    meta: dict[str, Any] = {
        "model": "v3-historical-head-experimental",
        "applied": False,
        "sleeve_weight": 0.0,
        "calibrated": False,
        "historical_labels": "numeric_direction_and_tail_only",
    }

    def unchanged(reason: str) -> tuple[NDArray[np.float64], dict[str, Any]]:
        meta["reason"] = reason
        return samples.copy(), meta

    if family not in {"T2-F2", "T2-F4"}:
        return unchanged("family_bypass")
    if decision is None or not evidence_valid or not decision.evidence:
        return unchanged("evidence_gate_closed")
    if not np.isfinite(decision.confidence) or not 0.65 <= decision.confidence <= 1:
        return unchanged("low_or_invalid_confidence")
    if decision.regime == "continuation":
        return unchanged("continuation_keeps_anchor")
    if decision.regime not in {
        "policy_shift",
        "inflation_shift",
        "growth_shift",
        "liquidity_stress",
    }:
        return unchanged("unsupported_regime")
    if target_type not in {"level", "log_return"}:
        return unchanged("unsupported_target_type")
    if not assets or not horizons or any(h <= 0 for h in horizons):
        raise ValueError("assets and positive business-day horizons are required")
    if samples.ndim != 3 or samples.shape[1:] != (len(assets), len(horizons)):
        raise ValueError("samples must be draw by asset by horizon")
    if not np.isfinite(samples).all():
        raise ValueError("anchor samples must be finite")
    reference = direction_asset or (assets[0] if len(assets) == 1 else None)
    if reference not in assets:
        return unchanged("ambiguous_direction_asset")
    if decision.direction not in {-1, 0, 1} or decision.horizon not in {"short", "medium", "long"}:
        return unchanged("invalid_switch")
    if family == "T2-F2" and decision.direction == 0:
        return unchanged("no_direction")
    if family == "T2-F4" and decision.tail_side not in {"lower", "upper", "both"}:
        return unchanged("no_tail_request")

    cutoff = pd.to_datetime(asof, utc=True, errors="coerce")
    if pd.isna(cutoff):
        return unchanged("invalid_cutoff")
    prepared: dict[str, pd.Series] = {}
    anchors: list[float] = []
    for asset in assets:
        if asset not in histories:
            return unchanged("missing_history")
        original = histories[asset]
        dates = pd.to_datetime(original.index, utc=True, errors="coerce")
        series = pd.Series(original.to_numpy(dtype=float), index=dates)
        series = series.loc[series.index.notna() & (series.index <= cutoff)].sort_index()
        if series.index.has_duplicates or series.empty or not np.isfinite(series.iloc[-1]):
            return unchanged("invalid_history")
        anchors.append(float(series.iloc[-1]) if target_type == "level" else 0.0)
        prepared[asset] = _diff_without_gaps(series) if target_type == "level" else series
    # Keep missing rows until windows are screened. Dropping them would glue gaps.
    steps = pd.DataFrame(prepared).replace([np.inf, -np.inf], np.nan)
    period = _observation_period_business_days(steps) if target_frequency != "daily" else 1
    observation_horizons = [max(1, int(np.ceil(h / period))) for h in horizons]
    maximum = max(observation_horizons)
    if len(steps) < max(60, maximum + 30):
        return unchanged("insufficient_history")
    dates_days = steps.index.to_numpy(dtype="datetime64[D]")
    gaps = np.r_[False, np.busday_count(dates_days[:-1], dates_days[1:]) > max(5, 2 * period)]
    values = steps.to_numpy(dtype=float)
    values[gaps] = np.nan
    windows = np.lib.stride_tricks.sliding_window_view(values, maximum, axis=0)
    valid = np.isfinite(windows).all(axis=(1, 2))
    starts = np.flatnonzero(valid)
    windows = windows[valid]
    if len(windows) < 30:
        return unchanged("insufficient_contiguous_worlds")
    cumulative = np.cumsum(windows, axis=2)
    ordered = sorted(set(observation_horizons))
    selected_horizon = {
        "short": ordered[0],
        "medium": ordered[len(ordered) // 2],
        "long": ordered[-1],
    }[decision.horizon]
    moves = cumulative[:, assets.index(reference), selected_horizon - 1]
    if family == "T2-F2":
        selected = np.flatnonzero(moves * decision.direction > 0)
        cap = 0.15
    else:
        low, high = np.quantile(moves, [0.05, 0.95])
        mask = np.zeros(len(moves), dtype=bool)
        if decision.tail_side in {"lower", "both"}:
            mask |= (moves <= low) & (moves < 0)
        if decision.tail_side in {"upper", "both"}:
            mask |= (moves >= high) & (moves > 0)
        selected = np.flatnonzero(mask)
        cap = 0.10
    # Overlapping starts can exaggerate support from a single episode. Require
    # at least three separated conditioning windows in addition to ten starts.
    separated = 0
    previous = -selected_horizon
    for start in starts[selected]:
        if start - previous >= selected_horizon:
            separated += 1
            previous = int(start)
    meta.update(
        {
            "candidate_worlds": int(len(selected)),
            "separated_conditioning_windows": separated,
            "observation_horizons": observation_horizons,
            "conditioning_horizon": selected_horizon,
            "direction_asset": reference,
            "sleeve_cap": cap,
        }
    )
    if len(selected) < 10 or separated < 3:
        return unchanged("sparse_historical_support")
    weight = cap * (decision.confidence - 0.65) / 0.35
    count = min(len(samples), int(np.floor(len(samples) * weight + 1e-9)))
    if count == 0:
        return unchanged("zero_allocation")
    rng = np.random.default_rng(seed)
    destination = rng.choice(len(samples), size=count, replace=False)
    source = rng.choice(selected, size=count, replace=True)
    historical = cumulative[source][:, :, np.array(observation_horizons) - 1]
    historical += np.asarray(anchors)[None, :, None]
    result = samples.copy()
    result[destination] = historical
    meta.update(
        {
            "applied": True,
            "reason": "experimental_historical_world_mixture",
            "sleeve_weight": count / len(samples),
            "replacement_draws": count,
            "regime": decision.regime,
            "tail_side": decision.tail_side,
            "confidence": decision.confidence,
            "evidence": list(decision.evidence),
            "history_last_date": str(steps.index[-1].date()),
        }
    )
    return result, meta

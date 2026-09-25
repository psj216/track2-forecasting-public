"""## Executive summary (read this first)

Calibrate F1 centers and widths while preserving each V3 world's marginal rank.
For example, a 50 percent persistence center blends the V3 sample mean with the
last observed level. F3 and all non-F1 families bypass this layer exactly.
Learned configurations carry the last training-label date and cannot time travel.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.typing import NDArray


@dataclass(frozen=True)
class FamilyCalibration:
    """A family-wide thin head; never an asset- or card-specific coefficient."""

    name: str = "identity"
    center: str = "v3"
    center_weight: float = 0.0
    scale: float = 1.0
    horizon_tilt: float = 0.0
    trained_through: str | None = None


def candidate_grid() -> tuple[FamilyCalibration, ...]:
    """Small declared grid including exact identity and one-factor ablations."""
    return (
        FamilyCalibration(),
        FamilyCalibration("persistence-50", "persistence", 0.5),
        FamilyCalibration("reversion-25", "reversion", 0.25),
        FamilyCalibration("trend-25", "trend", 0.25),
        FamilyCalibration("scale-85", scale=0.85),
        FamilyCalibration("scale-95", scale=0.95),
        FamilyCalibration("scale-105", scale=1.05),
        FamilyCalibration("horizon-minus10", horizon_tilt=-0.10),
        FamilyCalibration("horizon-plus10", horizon_tilt=0.10),
        FamilyCalibration("persistence-scale95", "persistence", 0.5, 0.95),
        FamilyCalibration("persistence-horizon", "persistence", 0.5, 1.0, -0.10),
        FamilyCalibration("reversion-horizon", "reversion", 0.25, 1.0, -0.10),
    )


def apply_family_calibration(
    samples: NDArray[np.float64],
    histories: dict[str, pd.Series],
    assets: list[str],
    horizons: list[int],
    target_type: str,
    family: str,
    as_of: str,
    config: FamilyCalibration,
) -> NDArray[np.float64]:
    """Apply a positive affine transform to each F1 asset/horizon world coordinate.

    This preserves sampled dependence ranks, not exact cumulative shock paths.
    Width is referenced to 21 business days and bounded to [0.70, 1.30].
    """
    if family != "T2-F1" or config == FamilyCalibration():
        return samples.copy()
    if config.center not in {"v3", "persistence", "reversion", "trend"}:
        raise ValueError("unknown center expert")
    if not (0 <= config.center_weight <= 0.5 and 0.75 <= config.scale <= 1.25):
        raise ValueError("calibration parameters exceed conservative bounds")
    if not -0.15 <= config.horizon_tilt <= 0.15:
        raise ValueError("horizon tilt exceeds conservative bounds")
    cutoff = pd.Timestamp(as_of)
    if config.trained_through is not None and pd.Timestamp(config.trained_through) >= cutoff:
        raise ValueError("calibration training labels must end before forecast as-of")
    if config.center_weight == 0 and config.scale == 1 and config.horizon_tilt == 0:
        return samples.copy()
    if samples.ndim != 3 or samples.shape[1:] != (len(assets), len(horizons)):
        raise ValueError("draw shape does not match assets/horizons")
    if not horizons or min(horizons) < 1 or not np.isfinite(samples).all():
        raise ValueError("invalid horizons or draws")
    if target_type != "level":
        return samples.copy()
    center = samples.mean(axis=0)
    expert = center.copy()
    hs = np.asarray(horizons, dtype=float)
    for index, asset in enumerate(assets):
        series = histories[asset].sort_index().dropna()
        series = series.loc[pd.to_datetime(series.index) <= cutoff].astype(float)
        if len(series) < 60:
            return samples.copy()
        last = float(series.iloc[-1])
        if config.center == "persistence":
            expert[index] = last
        elif config.center == "reversion":
            long_mean = float(series.tail(252).mean())
            expert[index] = last + (long_mean - last) * (1 - np.exp(-hs / 126.0))
        elif config.center == "trend":
            dates = pd.DatetimeIndex(pd.to_datetime(series.tail(60).index))
            elapsed = max(float(np.busday_count(dates[0].date(), dates[-1].date())), 1.0)
            slope = (last - float(series.iloc[-60])) / elapsed
            # Bound center movement using current model uncertainty at each horizon.
            cap = 0.5 * samples[:, index, :].std(axis=0)
            expert[index] = last + np.clip(slope * hs, -cap, cap)
    calibrated_center = center + config.center_weight * (expert - center)
    widths = np.clip(config.scale * (hs / 21.0) ** config.horizon_tilt, 0.70, 1.30)
    return np.asarray(calibrated_center + (samples - center) * widths, dtype=np.float64)


def load_family_calibration(path: Path) -> FamilyCalibration:
    """Load a fitted config; require provenance date before runtime activation."""
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict) or not isinstance(payload.get("trained_through"), str):
        raise ValueError("fitted configuration requires trained_through date")
    config = FamilyCalibration(**payload)
    timestamp = pd.Timestamp(config.trained_through)
    if pd.isna(timestamp):
        raise ValueError("invalid trained_through date")
    if config.center not in {"v3", "persistence", "reversion", "trend"}:
        raise ValueError("unknown center expert")
    if not (
        0 <= config.center_weight <= 0.5
        and 0.75 <= config.scale <= 1.25
        and -0.15 <= config.horizon_tilt <= 0.15
    ):
        raise ValueError("calibration parameters exceed conservative bounds")
    return config

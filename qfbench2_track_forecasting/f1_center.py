"""## Executive summary (read this first)

Shift only F1 V3 sample centers using a frozen, cutoff-safe historical bias table.
The residual shape, variance, tail widths, and draw ordering stay unchanged.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.typing import NDArray


def horizon_group(horizon: int) -> str:
    """Use three declared business-day ranges, shared across all assets."""
    return "short" if horizon <= 21 else "medium" if horizon <= 63 else "long"


def frequency_group(frequency: str) -> str:
    return "monthly" if frequency.lower() in {"monthly", "quarterly"} else "daily"


@dataclass(frozen=True)
class CenterBias:
    trained_through: str
    strength: float
    cap: float
    biases: dict[str, float]


def load_center_bias(path: Path) -> CenterBias:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if set(payload) != {"trained_through", "strength", "cap", "biases"}:
        raise ValueError("invalid F1 center config")
    model = CenterBias(**payload)
    if pd.isna(pd.Timestamp(model.trained_through)):
        raise ValueError("invalid training date")
    if not (0 < model.strength <= 0.5 and 0 < model.cap <= 0.25):
        raise ValueError("F1 center strength or cap outside conservative bounds")
    if any(
        key not in {f"{f}:{h}" for f in ("daily", "monthly") for h in ("short", "medium", "long")}
        or not np.isfinite(value)
        or abs(value) > 1
        for key, value in model.biases.items()
    ):
        raise ValueError("invalid F1 bias table")
    return model


def apply_center_bias(
    samples: NDArray[np.float64],
    horizons: list[int],
    target_frequency: str,
    target_type: str,
    family: str,
    asof: str,
    model: CenterBias,
) -> NDArray[np.float64]:
    """Return exact V3 for every excluded family, target type, or training overlap."""
    if family != "T2-F1" or target_type != "level":
        return samples.copy()
    if pd.Timestamp(asof) <= pd.Timestamp(model.trained_through):
        return samples.copy()
    if samples.ndim != 3 or samples.shape[2] != len(horizons):
        raise ValueError("invalid F1 draw grid")
    output = samples.copy()
    freq = frequency_group(target_frequency)
    for hi, horizon in enumerate(horizons):
        bias = model.biases.get(f"{freq}:{horizon_group(horizon)}", 0.0)
        for ai in range(samples.shape[1]):
            spread = float(np.std(samples[:, ai, hi]))
            shift = np.clip(model.strength * bias, -model.cap, model.cap) * spread
            output[:, ai, hi] += shift
    return output

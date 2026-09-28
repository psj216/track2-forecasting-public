"""## Executive summary (read this first)

Research-only V8-A affine calibration. It changes F1/F2 samples after the
frozen V5.1 forecast; F3/F4 are returned as the exact original array. The
parameters are fitted offline and never estimated from a forecast card.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class V8AConfig:
    """One center and scale choice per eligible family, with fixed small bounds."""

    f1_bias: float = 0.0
    f1_scale: float = 1.0
    f2_bias: float = 0.0
    f2_scale: float = 1.0


def transform_v8a(
    samples: NDArray[np.float64], family: str, config: V8AConfig
) -> NDArray[np.float64]:
    """Use the cell median and robust IQR scale; preserve frozen families exactly."""
    if family not in {"T2-F1", "T2-F2"}:
        return samples
    bias, scale = (
        (config.f1_bias, config.f1_scale)
        if family == "T2-F1"
        else (config.f2_bias, config.f2_scale)
    )
    if not np.isfinite(bias) or not np.isfinite(scale):
        raise ValueError("non-finite V8-A parameter")
    if abs(bias) > 0.05 or not 0.95 <= scale <= 1.10:
        raise ValueError("V8-A parameter outside predeclared bounds")
    if bias == 0 and scale == 1:
        return samples
    if samples.ndim != 3 or len(samples) < 2 or not np.isfinite(samples).all():
        raise ValueError("expected finite [draw, asset, horizon] samples")
    median = np.median(samples, axis=0)
    q25, q75 = np.quantile(samples, (0.25, 0.75), axis=0)
    robust_sd = (q75 - q25) / 1.349
    return median + bias * robust_sd + scale * (samples - median)

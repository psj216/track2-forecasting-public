"""## Executive summary (read this first)

At origin t, use only t-1 source shocks and the t target gate. Frozen
coefficients make inference fit-free; V5.1 receives only an additive shift.
"""

import numpy as np

from .location_shift import apply, native_shift
from .propagation_model import predict
from .shock_detector import excess
from .unreacted_gate import unreacted


def signal(coef, z, row, target, horizons):
    if row < 1:
        raise ValueError("Need a prior business observation")
    source = excess(z[row - 1])
    pred, contribution = predict(coef, source, target)
    gated = bool(unreacted(z[row, target]))
    alpha = pred * gated
    peer = np.arange(len(source)) != target
    dominant = int(np.argmax(np.where(peer, np.abs(contribution).sum(axis=0), -1)))
    return alpha, contribution, dominant, source, gated


def forecast(draws, alpha, sigma, horizons):
    result = np.array(draws, dtype=float, copy=True)
    shifts = np.asarray([native_shift(a, sigma, h) for a, h in zip(alpha, horizons)])
    return apply(result, shifts[None, :]), shifts

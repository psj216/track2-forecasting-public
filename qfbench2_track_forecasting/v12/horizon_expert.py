"""Shared long-horizon residual expert, gated only by horizon."""

import numpy as np


def predict(x: np.ndarray, horizon: int, coefficients: np.ndarray) -> np.ndarray:
    if horizon < 126:
        return np.zeros(len(x))
    # z_504, trend_504, regime_duration, plus intercept.
    return np.c_[np.ones(len(x)), x[:, 9], x[:, 7], x[:, 17]] @ coefficients

"""## Executive summary (read this first)

Future truth defines a supervised label and never a feature.
"""
import numpy as np
from qfbench2_track_forecasting.v12.data_parity import _label

EPSILON = 1e-8
HORIZONS = (5, 21, 63, 126, 189)

def target(series, kind, origin, horizon):
    result = _label(series, 'log_return' if kind == 'return' else kind,
                    origin, horizon, '2100-01-01', False)
    if result is None:
        return None
    change, end = result
    return (change + float(series.loc[origin]) if kind == 'level' else change), end

def oracle_label(draws, truth):
    x = np.asarray(draws, float)
    median = float(np.median(x))
    sd = float(np.std(x, ddof=0))
    return median, sd, (float(truth) - median) / max(sd, EPSILON)

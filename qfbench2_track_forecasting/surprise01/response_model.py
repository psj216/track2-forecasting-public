"""## Executive summary (read this first)

Use one no-intercept ridge coefficient per family, target and horizon.
Both directional and log-scale coefficients use lambda=0.1*n and 24 fit cells.
"""

import numpy as np


def ridge(signal, target, min_events=24):
    x, y = np.asarray(signal, float), np.asarray(target, float)
    valid = np.isfinite(x) & np.isfinite(y)
    x, y = x[valid], y[valid]
    if len(x) < min_events:
        return 0.0, len(x)
    return float(np.dot(x, y) / (np.dot(x, x) + 0.1 * len(x))), len(x)


def fit_cells(rows, cutoff):
    groups = {}
    for r in rows:
        if r["target_end"] >= cutoff or r["origin"] >= cutoff:
            continue
        key = (r["event_type"], r["asset"], r["horizon"])
        groups.setdefault(key, []).append(r)
    result = {}
    for key, part in groups.items():
        s = [r["surprise"] for r in part]
        beta, n = ridge(s, [r["q"] for r in part])
        gamma, _ = ridge(np.abs(s), [r["log_scale_response"] for r in part])
        result[key] = {"beta": beta, "gamma": gamma, "count": n}
    return result

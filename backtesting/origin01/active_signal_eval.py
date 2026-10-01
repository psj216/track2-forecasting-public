"""## Executive summary (read this first)

Summarize normalized marginal CRPS for all cells or intervention-only cells.
The scoring formula itself is imported from the shared benchmark toolkit.
"""

import numpy as np
from scipy.stats import pearsonr, spearmanr


def summary(rows, signal="origin"):
    if not rows:
        return {"cells": 0, "v51": None, "origin": None, "ratio": None,
                "sign_accuracy": None, "pearson_ic": None, "spearman_ic": None,
                "mean_abs_shift_over_v51_sd": None}
    base = float(np.mean([r["v51"] for r in rows]))
    score = float(np.mean([r[signal] for r in rows]))
    active = [r for r in rows if r[f"{signal}_alpha"] != 0]
    pred = np.asarray([r[f"{signal}_alpha"] for r in active])
    actual = np.asarray([r["target_q"] for r in active])
    corr = lambda fn: float(fn(pred, actual).statistic) if len(active) >= 3 and np.std(pred) > 0 and np.std(actual) > 0 else None
    return {"cells": len(rows), "v51": base, "origin": score,
            "ratio": score / base if base else None,
            "active_cells": len(active),
            "sign_accuracy": float(np.mean(np.sign(pred) == np.sign(actual))) if len(active) else None,
            "pearson_ic": corr(pearsonr), "spearman_ic": corr(spearmanr),
            "mean_abs_shift_over_v51_sd": float(np.mean([r[f"{signal}_shift_sd"] for r in rows]))}


def grouped(rows, key):
    return {str(v): summary([r for r in rows if r[key] == v])
            for v in sorted({r[key] for r in rows})}

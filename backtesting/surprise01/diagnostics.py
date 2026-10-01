"""## Executive summary (read this first)

Report directional and dispersion information separately, alongside cell and event counts.
"""

import numpy as np
from scipy.stats import pearsonr, spearmanr


def aggregate(rows, head):
    if not rows:
        return {"cells": 0, "events": 0, "v51": None, "candidate": None, "ratio": None}
    base = float(np.mean([r["v51"] for r in rows]))
    candidate = float(np.mean([r[head] for r in rows]))
    scale_head = head.endswith("scale") and not head.endswith("combined")
    pkey = head + "_dispersion" if scale_head else head + "_alpha"
    ykey = "log_scale_response" if scale_head else "q"
    active = [r for r in rows if r[head + "_active"]]
    x, y = np.asarray([r[pkey] for r in active]), np.asarray([r[ykey] for r in active])
    corr = lambda f: float(f(x, y).statistic) if len(active) > 2 and np.std(x) > 0 and np.std(y) > 0 else None
    return {"cells": len(rows), "events": len({r["event_id"] for r in rows}),
            "release_date_clusters": len({r["release_date"] for r in rows}),
            "v51": base, "candidate": candidate, "ratio": candidate / base,
            "active_cells": len(active), "active_events": len({r["event_id"] for r in active}),
            "sign_accuracy": float(np.mean(np.sign(x) == np.sign(y))) if len(active) and not scale_head else None,
            "pearson_ic": corr(pearsonr), "spearman_ic": corr(spearmanr),
            "ic_target": "future log path scale / V5.1 SD" if scale_head else "normalized future movement",
            "mean_abs_location_shift_over_v51_sd": float(np.mean([r[head + "_shift_sd"] for r in rows])),
            "mean_scale_multiplier": float(np.mean([r[head + "_factor"] for r in rows]))}

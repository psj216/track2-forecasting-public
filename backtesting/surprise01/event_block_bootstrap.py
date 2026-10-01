"""## Executive summary (read this first)

Resample whole release-date clusters, retaining all families/assets/horizons.
This prevents cell count from being mistaken for independent event count.
"""

import numpy as np
import pandas as pd


def interval(rows, head, n_bootstrap=2000, seed=1902):
    if not rows:
        return {"clusters": 0, "ratio_ci95": None}
    frame = pd.DataFrame(rows)
    grouped = frame.groupby("release_date")[["v51", head]].sum()
    values = grouped.to_numpy()
    if len(values) < 2:
        return {"clusters": len(values), "ratio_ci95": None}
    rng = np.random.default_rng(seed)
    indexes = rng.integers(0, len(values), size=(n_bootstrap, len(values)))
    sums = values[indexes].sum(axis=1)
    ratios = sums[:, 1] / sums[:, 0]
    return {"clusters": len(values), "resampling_unit": "whole release date",
            "replicates": n_bootstrap, "ratio_ci95": np.quantile(ratios, [.025, .975]).tolist(),
            "limitation": "Overlapping multi-month targets retain serial dependence across distinct release dates"}

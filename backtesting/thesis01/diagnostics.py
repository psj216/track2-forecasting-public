"""## Executive summary (read this first)

Aggregate unit-normalized marginal scores and signal correlations without
publishing the per-origin realized outcomes.
"""

from collections import defaultdict

import numpy as np
from scipy.stats import spearmanr


def correlation(x: np.ndarray, y: np.ndarray) -> dict:
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 3 or np.std(x[mask]) < 1e-12 or np.std(y[mask]) < 1e-12:
        return {"n": int(mask.sum()), "pearson": None, "spearman": None}
    return {"n": int(mask.sum()),
            "pearson": float(np.corrcoef(x[mask], y[mask])[0, 1]),
            "spearman": float(spearmanr(x[mask], y[mask]).statistic)}


def aggregate(rows: list[dict]) -> dict:
    if not rows:
        return {"cells": 0, "baseline_crps": None, "thesis_crps": None, "ratio": None}
    base = float(np.mean([r["base_norm"] for r in rows]))
    thesis = float(np.mean([r["thesis_norm"] for r in rows]))
    return {"cells": len(rows), "baseline_crps": base, "thesis_crps": thesis,
            "ratio": thesis / base, "directional_sign_accuracy": float(np.mean([
                r["correct_sign"] for r in rows if r["correct_sign"] is not None]))
            if any(r["correct_sign"] is not None for r in rows) else None,
            "mean_shift_abs_over_baseline_sd": float(np.mean([
                r["shift_over_sd"] for r in rows])),
            "mean_signed_shift_native": float(np.mean([r["shift"] for r in rows]))}


def group(rows: list[dict], field: str) -> dict:
    buckets = defaultdict(list)
    for row in rows:
        buckets[str(row[field])].append(row)
    return {key: aggregate(values) for key, values in sorted(buckets.items())}

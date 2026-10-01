"""## Executive summary (read this first)

Partition private outcomes into disjoint families, horizons, and pair topologies.
All public outputs are grouped; native losses from unlike units are never summed.
"""

import numpy as np
from .scorer_adapter import aggregate


def summarize(rows, key="ratio"):
    if not rows:
        return {"cases": 0, "score": None, "arithmetic_sensitivity": None}
    values = [r[key] for r in rows]
    return {"cases": len(rows), "score": aggregate(values),
            "arithmetic_sensitivity": float(np.mean(values))}


def partitions(rows, field):
    return {str(v): [r for r in rows if r[field] == v] for v in sorted({r[field] for r in rows})}


def pair_kind(a, h, b, k):
    if a == b:
        return "same_asset_different_horizon"
    if h == k:
        return "different_asset_same_horizon"
    return "different_asset_different_horizon"

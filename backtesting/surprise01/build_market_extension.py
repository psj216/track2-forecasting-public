"""## Executive summary (read this first)

This study accepts only the existing 25 public daily prefixes through 2024.
The failed date-limited FRED audit is not an accepted 2025 extension.
"""

from pathlib import Path
from qfbench2_track_forecasting.thesis01.asset_semantics import load_universe


def historical_market(root: Path):
    series, kinds, _ = load_universe(root)
    return {a: s.loc[:"2024-12-18"] for a, s in series.items()}, kinds


def extension_status():
    return {"status": "NO_INDEPENDENT_FINAL_HOLDOUT",
            "accepted_market_extension": False,
            "reason": "FRED ignored date parameters; full file loaded during pre-freeze source audit",
            "outcome_scores_2025_computed": False}

"""## Executive summary (read this first)

Use the verified R2 public-panel catalog for asset units. Factor values are daily
return increments; rates and foreign exchange values are levels.
"""

from pathlib import Path

from qfbench2_track_forecasting.v12.data_parity import catalog


def load_universe(root: Path):
    """Return the 25 public prefixes and their types, without V12 predictions."""
    series, kinds, first_target = catalog(root)
    return series, kinds, first_target


def family(asset: str, kind: str) -> str:
    if kind in {"return", "log_return"}:
        return "Factor/Equity"
    if asset.startswith("UST_"):
        return "Rates"
    return "FX"

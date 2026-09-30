"""## Executive summary (read this first)

A level changes by its first difference. A daily return already is an increment.
No future observations enter an innovation at the origin.
"""

import pandas as pd


def innovations(panel: pd.DataFrame, kinds: dict[str, str]) -> pd.DataFrame:
    columns = {}
    for asset in panel:
        kind = kinds[asset]
        if kind == "level":
            columns[asset] = panel[asset].diff()
        elif kind in {"return", "log_return"}:
            columns[asset] = panel[asset].copy()
        else:
            raise ValueError(f"Unsupported representation: {kind}")
    return pd.DataFrame(columns, index=panel.index)

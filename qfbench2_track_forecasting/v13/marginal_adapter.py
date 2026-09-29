"""Independent conditional V12 one-dimensional sampling, no joint generator call."""

import numpy as np
import pandas as pd

from qfbench2_track_forecasting.v12.asset_decoder import sample_cell
from qfbench2_track_forecasting.v12.joint_features import features


def conditional_marginals(artifact: dict, panel: pd.DataFrame, assets: list[str],
                          horizons: list[int], asof: str, draws: int, seed: int,
                          target_type: str) -> np.ndarray:
    known = artifact["assets"]
    x, g, coverage = features(panel, known, asof)
    rng = np.random.default_rng(seed)
    out = np.empty((draws, len(horizons), len(assets)))
    past = panel.loc[pd.to_datetime(panel.date) <= pd.Timestamp(asof)]
    for j, h in enumerate(horizons):
        for k, asset in enumerate(assets):
            a = known.index(asset)
            cell = sample_cell(artifact, x, g, coverage, a, h, draws, rng)
            if target_type == "level":
                rows = past.loc[past.asset == asset].sort_values("date")
                if rows.empty:
                    raise ValueError(f"Missing as-of prefix for {asset}")
                cell += float(rows.value.iloc[-1])
            out[:, j, k] = cell
    return out

"""## Executive summary (read this first)

Keep V5.1 draws intact except for one identical additive shift per asset/horizon.
The research baseline calls the V5.1 runtime with no synthetic text evidence.
"""

from pathlib import Path

import numpy as np
import pandas as pd


def shift_only(draws: np.ndarray, beta: float, tension: float,
               sigma: float, horizon: int) -> np.ndarray:
    return np.asarray(draws) + beta * tension * sigma * np.sqrt(horizon)


def v51_no_text_prior(series: pd.Series, asset: str, kind: str, horizons: list[int],
                      family: str, asof: str, seed: int = 19,
                      n_draws: int = 500) -> np.ndarray:
    """Execute Numeric V3 plus the actual V5.1 routing with an empty corpus.

    Historical panel research has no origin-specific frozen text. This explicit
    ablation must not be confused with a complete V5.1 card forecast.
    """
    from qfbench2_track_forecasting.numeric_v3 import forecast_numeric_v3
    from qfbench2_track_forecasting.text_first_v5 import apply_text_first_v5

    prefix = series.loc[:pd.Timestamp(asof)]
    history = pd.Series(prefix.to_numpy(dtype=float), index=prefix.index.strftime("%Y-%m-%d"))
    result = forecast_numeric_v3({asset: history}, [asset], horizons, kind, "daily",
                                 n_draws, seed, family)
    adjusted, _ = apply_text_first_v5(
        result.samples, {asset: history} if family in {"T2-F1", "T2-F4"} else {},
        [asset], horizons, kind, "daily", family, asof, seed,
        Path("/nonexistent/thesis01/frozen-text"), "", interpreter_version="v5.1")
    return np.asarray(adjusted[:, 0, :], dtype=float)

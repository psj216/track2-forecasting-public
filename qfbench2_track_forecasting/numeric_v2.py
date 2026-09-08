"""## Executive summary (read this first)

Numeric v2 keeps V1's target handling, drift, fragility and joint path sampler. It adds one
historical state-matched pool. For every old block, only information available before that block
is used to compare its 20/120-day volatility ratio and momentum with the current market state.

Pseudo-asof tests selected a 75 percent maximum conditional share for this pool. The effective
share is multiplied by one minus current fragility. It applies only after a draw is assigned away
from recent history, so full-history scenarios are suppressed but never removed and regain weight
when the current state is less trustworthy.
"""

from __future__ import annotations

import pandas as pd

from .numeric_v1 import NumericConfig, NumericForecast, forecast_numeric

V2_CONFIG = NumericConfig(
    name="regime-matched joint block bootstrap v2",
    state_match_share=0.75,
)


def forecast_numeric_v2(
    histories: dict[str, pd.Series],
    assets: list[str],
    horizons: list[int],
    target_type: str,
    n_draws: int,
    seed: int,
) -> NumericForecast:
    """Generate the selected V2 distribution under the frozen V2 configuration."""
    return forecast_numeric(histories, assets, horizons, target_type, n_draws, seed, V2_CONFIG)

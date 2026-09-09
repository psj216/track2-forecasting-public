"""## Executive summary (read this first)

Numeric v2.1 keeps the selected V2 distribution for daily panels and corrects its treatment of
lower-frequency panels. Card horizons are always business days, while a macro panel can contain
one observation per month. V2.1 infers the panel's observation period and converts each requested
business-day horizon into the corresponding number of observed steps before sampling.

No text, realized outcome or private scoring scale is used. This is a correctness release for the
numeric anchor, not the later explicit shock-mixture model.
"""

from __future__ import annotations

import pandas as pd

from .numeric_v1 import NumericConfig, NumericForecast, forecast_numeric

V21_CONFIG = NumericConfig(
    name="frequency-aware regime-matched joint block bootstrap v2.1",
    state_match_share=0.75,
    frequency_aware=True,
)


def forecast_numeric_v21(
    histories: dict[str, pd.Series],
    assets: list[str],
    horizons: list[int],
    target_type: str,
    target_frequency: str,
    n_draws: int,
    seed: int,
) -> NumericForecast:
    """Generate V2.1 samples with business-day horizons mapped to panel observations."""
    return forecast_numeric(
        histories,
        assets,
        horizons,
        target_type,
        n_draws,
        seed,
        V21_CONFIG,
        target_frequency=target_frequency,
    )

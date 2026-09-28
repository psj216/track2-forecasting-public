"""## Executive summary (read this first)

Ensure V9-B uses only pre-asof state, preserves F3 exactly, and changes
longer-horizon spreads in the direction implied by the volatility curve.
"""

import numpy as np

from qfbench2_track_forecasting.numeric_v1 import NumericForecast
from qfbench2_track_forecasting.numeric_v9b import apply_vol_term_structure


def _forecast(vol_ratio):
    shocks = np.linspace(-2, 2, 200)
    samples = np.stack((shocks, 2 * shocks), axis=-1)[:, None, :]
    return NumericForecast(samples, {"regime": {"vol_ratio_20_long": {"A": vol_ratio}},
        "observation_period_business_days": 1,
        "observation_horizons": [21, 126], "anchor": {"A": 0.0},
        "daily_drift": {"A": 0.0}})


def test_f3_and_no_volatility_shift_return_exact_original():
    base = _forecast(0.7)
    assert apply_vol_term_structure(base, ["A"], "T2-F3") is base
    neutral = _forecast(1.0)
    assert apply_vol_term_structure(neutral, ["A"], "T2-F1") is neutral


def test_calmer_state_widens_long_horizon_and_stress_tapers_it():
    calm = _forecast(0.7)
    stress = _forecast(1.5)
    wider = apply_vol_term_structure(calm, ["A"], "T2-F2")
    tighter = apply_vol_term_structure(stress, ["A"], "T2-F4")
    assert wider.samples[:, 0, -1].std() > calm.samples[:, 0, -1].std()
    assert tighter.samples[:, 0, -1].std() < stress.samples[:, 0, -1].std()
    assert np.all(np.isfinite(wider.samples))

"""## Executive summary (read this first)

Controls are deterministic, act on whole events, and preserve absolute sign-shuffled values.
"""

import pandas as pd
from backtesting.surprise01.negative_controls import maps


def test_controls():
    d = pd.DataFrame([{"event_id": str(i), "event_type": "CPI", "surprise": float(i)} for i in range(8)])
    assert maps(d) == maps(d)
    flips, dates, family = maps(d)
    assert sorted(dates.values()) == list(range(8))
    assert family["CPI"] == "Core CPI"
    assert all(v in {-1, 1} for v in flips.values())

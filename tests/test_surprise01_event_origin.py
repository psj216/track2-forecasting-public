"""## Executive summary (read this first)

Unknown or post-observation publication time moves the origin to the next day.
"""

import pandas as pd
from backtesting.surprise01.fit_response import event_origin


def test_information_origin():
    dates = pd.bdate_range("2024-01-02", periods=4)
    e = {"release_date": "2024-01-02", "release_timestamp": "2024-01-02T08:30:00-05:00"}
    assert event_origin(e, dates) == dates[0]
    assert event_origin({**e, "release_timestamp": None}, dates) == dates[1]
    assert event_origin({**e, "release_timestamp": "2024-01-02T14:00:00-05:00"}, dates) == dates[1]

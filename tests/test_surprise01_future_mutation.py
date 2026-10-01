"""## Executive summary (read this first)

Future market mutations cannot change the no-text baseline or its update.
"""

import numpy as np
import pandas as pd
from backtesting.surprise01.fit_response import baseline_group
from qfbench2_track_forecasting.surprise01.engine import update


def test_future_mutation():
    dates = pd.bdate_range("2010-01-01", periods=280)
    values = pd.Series(3 + np.sin(np.arange(280.) / 20) / 10, index=dates)
    origin = dates[260]
    a, x = baseline_group({"UST_2Y": values}, {"UST_2Y": "level"}, origin, "Rates")
    changed = values.copy(); changed.loc[dates[261]:] = 1e6
    b, y = baseline_group({"UST_2Y": changed}, {"UST_2Y": "level"}, origin, "Rates")
    assert a == b
    np.testing.assert_array_equal(x, y)
    np.testing.assert_array_equal(update(x[:, 0, 0], 1, .1, .2, .1, 5)[0]["combined"],
                                  update(y[:, 0, 0], 1, .1, .2, .1, 5)[0]["combined"])

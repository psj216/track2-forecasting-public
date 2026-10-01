"""## Executive summary (read this first)

Fixed control seed and no random model fitting make repeated signals identical.
"""

import numpy as np
from backtesting.origin01.negative_controls import source_controls


def test_control_repeats():
    x = np.arange(50.).reshape(10, 5)
    for a, b in zip(source_controls(x), source_controls(x)):
        np.testing.assert_array_equal(a, b)

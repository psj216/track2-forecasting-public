"""## Executive summary (read this first)

The target must have strictly less than one standardized move at origin.
"""

from qfbench2_track_forecasting.origin01.unreacted_gate import unreacted


def test_gate_boundary():
    assert list(unreacted([0, .999, 1, -1, float("nan")])) == [True, True, False, False, False]

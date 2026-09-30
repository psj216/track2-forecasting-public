"""## Executive summary (read this first)

The update leaves centered draws, pairwise differences, and ranks intact.
"""
import numpy as np
from qfbench2_track_forecasting.thesis01.v51_shift import shift_only


def test_location_only():
    draws = np.array([-.2, 1.0, 1.5, 2.0])
    shifted = shift_only(draws, -.3, .5, 2., 21)
    np.testing.assert_allclose(shifted - shifted[0], draws - draws[0])
    assert np.array_equal(np.argsort(shifted), np.argsort(draws))

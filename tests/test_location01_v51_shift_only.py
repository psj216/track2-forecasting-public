"""## Executive summary (read this first)

One native shift is added to every draw, with the fixed numerical cap.
"""
import numpy as np
from qfbench2_track_forecasting.location01.engine import shift

def test_shift_only():
    x=np.arange(60.).reshape(20,3)
    y=shift(x,np.array([.1,-.2,12]),np.array([2.,3.,4.]))
    np.testing.assert_allclose(y-x,np.broadcast_to([.2,-.6,40],x.shape))

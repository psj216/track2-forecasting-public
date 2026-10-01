"""## Executive summary (read this first)

Verify a frozen CEILING-01 diagnostic contract.
"""

import numpy as np
from qfbench2_track_forecasting.ceiling01.joint_oracle import apply
from qfbench2_track_forecasting.ceiling01.scale_oracle import apply as scale

def test_deterministic():
 x=np.random.default_rng(9).normal(size=(200,3));y=np.array([2.,-.1,1.])
 a,m=apply(x,y,proposals=200);b,n=apply(x,y,proposals=200)
 np.testing.assert_array_equal(a,b);assert m==n
 a,m=scale(x,y);b,n=scale(x,y);np.testing.assert_array_equal(a,b);np.testing.assert_array_equal(m,n)

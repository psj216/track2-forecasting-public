"""## Executive summary (read this first)

Verify a frozen CEILING-01 diagnostic contract.
"""

import numpy as np
from qfbench2_track_forecasting.ceiling01.location_oracle import apply

def test_location_preserves_spread():
 x=np.random.default_rng(4).normal(size=(500,3)); y=np.array([4.,-3.,2.]); z=apply(x,y)
 np.testing.assert_allclose(np.median(z,axis=0),y,atol=1e-14)
 np.testing.assert_allclose(z-z[0],x-x[0],atol=1e-14)
 np.testing.assert_array_equal(np.argsort(z,axis=0),np.argsort(x,axis=0))

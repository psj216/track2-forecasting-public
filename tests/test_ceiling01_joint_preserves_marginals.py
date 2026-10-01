"""## Executive summary (read this first)

Verify a frozen CEILING-01 diagnostic contract.
"""

import numpy as np
from qfbench2_track_forecasting.ceiling01.joint_oracle import apply
from qfbench2_track_forecasting.ceiling01.scorer_adapter import components

def test_joint_preserves_marginals():
 x=np.random.default_rng(8).normal(size=(200,4)); y=np.array([1.,3.,-2.,.2])
 z,_=apply(x,y,proposals=300)
 np.testing.assert_array_equal(np.sort(x,axis=0),np.sort(z,axis=0))
 a,b=components(x,y),components(z,y)
 assert np.isclose(a['marginal'],b['marginal'],atol=1e-14)
 assert a['tail']==b['tail']
 assert b['joint']<=a['joint']+1e-12

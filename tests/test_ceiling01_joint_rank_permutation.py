"""## Executive summary (read this first)

Verify a frozen CEILING-01 diagnostic contract.
"""

import numpy as np
from qfbench2_track_forecasting.ceiling01.joint_oracle import apply

def test_joint_rank_permutation_with_ties():
 x=np.round(np.random.default_rng(8).normal(size=(200,3)),1); y=np.array([2.,-1.,.5])
 z,_=apply(x,y,proposals=200)
 for j in range(3):
  a,b=np.unique(x[:,j],return_counts=True); c,d=np.unique(z[:,j],return_counts=True)
  np.testing.assert_array_equal(a,c);np.testing.assert_array_equal(b,d)

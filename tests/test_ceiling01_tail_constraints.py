"""## Executive summary (read this first)

Verify a frozen CEILING-01 diagnostic contract.
"""

import numpy as np
from qfbench2_track_forecasting.ceiling01.tail_oracle import apply
from qfbench2_track_forecasting.tail import tail_pinball

def test_tail_constraints_and_tail_loss():
 x=np.random.default_rng(55).normal(size=(500,3));y=np.array([4.,-.5,-5.]);z=apply(x,y)
 assert z.shape==x.shape
 for q in (.25,.5,.75):np.testing.assert_array_equal(np.quantile(x,q,axis=0),np.quantile(z,q,axis=0))
 assert np.all(np.diff(np.sort(z,axis=0),axis=0)>=0)
 assert tail_pinball(z,y,(.01,.05,.95,.99))<=tail_pinball(x,y,(.01,.05,.95,.99))

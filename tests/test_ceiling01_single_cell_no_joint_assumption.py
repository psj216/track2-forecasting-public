"""## Executive summary (read this first)

Verify a frozen CEILING-01 diagnostic contract.
"""

import numpy as np
from qfbench2_track_forecasting.ceiling01.zero_loss_bounds import replace
from qfbench2_track_forecasting.ceiling01.joint_oracle import apply
from qfbench2_track_forecasting.ceiling01.scorer_adapter import components

def test_single_cell_no_joint_assumption():
 x=np.random.default_rng(1).normal(size=(200,1)); y=np.array([2.]); ref=components(x,y)
 assert ref['joint']==0.
 assert replace(ref,1,('joint',))==1.
 assert np.isclose(replace(ref,1,('marginal',)),2/7)
 z,meta=apply(x,y);np.testing.assert_array_equal(x,z);assert meta['status']=='NO_JOINT'

"""## Executive summary (read this first)

Verify a frozen CEILING-01 diagnostic contract.
"""

import numpy as np
from qfbench2_track_forecasting.ceiling01.zero_loss_bounds import replace
from qfbench2_track_forecasting.ceiling01.scorer_adapter import aggregate

def test_zero_loss_component():
 ref={'marginal':2.,'joint':7.,'tail':.3}
 assert np.isclose(replace(ref,4,('marginal',)),.5)
 assert np.isclose(replace(ref,4,('joint',)),.7)
 assert replace(ref,4,('marginal','joint','tail'))==0.
 assert np.isclose(aggregate([0.,1.]),1e-6)

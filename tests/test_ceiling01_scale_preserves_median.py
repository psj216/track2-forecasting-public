"""## Executive summary (read this first)

Verify a frozen CEILING-01 diagnostic contract.
"""

import numpy as np
from scipy.optimize import minimize_scalar
from qfbench2_common.scoring.crps import crps_ensemble
from qfbench2_track_forecasting.ceiling01.scale_oracle import apply,optimal_scale

def test_scale_preserves_median_and_exact_optimum():
 x=np.random.default_rng(12).normal(size=(500,2)); y=np.array([3.,-.2]); z,a=apply(x,y)
 np.testing.assert_allclose(np.median(z,axis=0),np.median(x,axis=0),atol=1e-14)
 for j in range(2):
  med=np.median(x[:,j]); d=x[:,j]-med
  result=minimize_scalar(lambda b:float(crps_ensemble(med+b*d,y[j])),bounds=(0,100),method='bounded')
  assert float(crps_ensemble(z[:,j],y[j]))<=result.fun+1e-8
 assert .5<=optimal_scale(x[:,0],y[0],(.5,2.))<=2.

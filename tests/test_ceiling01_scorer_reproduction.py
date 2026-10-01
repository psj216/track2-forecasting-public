"""## Executive summary (read this first)

Verify a frozen CEILING-01 diagnostic contract.
"""

import numpy as np
from backtesting.v13_copula.evaluate_proxy import component_scores, geometric
from qfbench2_track_forecasting.ceiling01.scorer_adapter import components, composite_from_components, aggregate

def test_scorer_reproduction():
 x=np.random.default_rng(7).normal(size=(500,4)); y=np.array([.4,1.,-.3,2.])
 a=components(x,y); b=component_scores(x,y)
 for k in ('marginal','joint','tail'): assert a[k]==b[k]
 changed=components(x+.2,y)
 manual=.5*changed['marginal']/a['marginal']+.3*changed['joint']/a['joint']+.2*changed['tail']/a['tail']
 assert np.isclose(manual,composite_from_components(changed,a,4))
 assert aggregate([.7,1.2,.8])==geometric([.7,1.2,.8])

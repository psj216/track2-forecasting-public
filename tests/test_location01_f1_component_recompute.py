"""## Executive summary (read this first)

The F1 joint component is recomputed rather than assumed unchanged after shifts.
"""
import numpy as np
from backtesting.location01.evaluate_multicell import recompute
from qfbench2_track_forecasting.ceiling01.scorer_adapter import components
from qfbench2_track_forecasting.location01.engine import shift

def test_f1_recompute():
    b=np.random.default_rng(19).normal(size=(500,3,2))+np.array([1.,2.])
    truth=np.zeros((3,2));delta=np.array([.1,1.,-.5,.8,.2,-.7])
    baseline,candidate,oracle=recompute(b,truth,delta)
    direct=components(shift(b,delta.reshape(3,2),b.std(axis=0)),truth)
    for k in ('marginal','joint','tail'):
        assert candidate[k]==direct[k]
    assert baseline['joint']!=candidate['joint']

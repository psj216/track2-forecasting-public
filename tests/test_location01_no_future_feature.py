"""## Executive summary (read this first)

Truncating every market at the origin leaves the complete feature row unchanged.
"""
import numpy as np
from location01_helpers import panel
from qfbench2_track_forecasting.location01.feature_own_history import history_state
from qfbench2_track_forecasting.location01.engine import prepare,features

def test_no_future_feature():
    s,k,t=panel();x=np.arange(500.)*.001+float(s['EUR'].loc[t])
    def get(series):
        a=history_state(series,k);c,r=prepare(a)
        return features(a,c,r,'EUR','level',t,21,x,float(s['EUR'].loc[t]),1.)
    before=get(s);after=get({a:v.loc[:t] for a,v in s.items()})
    assert before.keys()==after.keys()
    np.testing.assert_allclose(list(before.values()),list(after.values()),equal_nan=True)

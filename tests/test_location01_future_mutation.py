"""## Executive summary (read this first)

Mutating all future markets changes neither features nor real V5.1 draws.
"""
import numpy as np
from location01_helpers import panel
from qfbench2_track_forecasting.thesis01.v51_shift import v51_no_text_prior
from qfbench2_track_forecasting.location01.feature_own_history import history_state
from qfbench2_track_forecasting.location01.engine import prepare,features

def test_future_mutation():
    s,k,t=panel()
    def get(series):
        draws=v51_no_text_prior(series['EUR'],'EUR','level',[5,21],'T2-F2',str(t.date()),19,500)
        a=history_state(series,k);c,r=prepare(a)
        f=features(a,c,r,'EUR','level',t,21,draws[:,1],float(series['EUR'].loc[t]),1.)
        return draws,np.asarray(list(f.values()))
    x,f=get(s)
    for a in s:s[a].loc[s[a].index>t]=1e9
    xx,ff=get(s)
    np.testing.assert_array_equal(x,xx);np.testing.assert_allclose(f,ff,equal_nan=True)

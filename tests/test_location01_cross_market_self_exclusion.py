"""## Executive summary (read this first)

Changing the target's past must not alter its cross-market channel.
"""
import numpy as np
from location01_helpers import panel
from qfbench2_track_forecasting.location01.feature_own_history import history_state
from qfbench2_track_forecasting.location01.feature_cross_market import prepare_cross,cross_market

def test_self_exclusion():
    s,k,t=panel();a=history_state(s,k)
    before=cross_market(prepare_cross(a),'EUR',t,a['assets'])
    s['EUR']=s['EUR']*19;b=history_state(s,k)
    after=cross_market(prepare_cross(b),'EUR',t,b['assets'])
    assert before==after
    assert all(v==0 for c,v in before.items() if c.startswith('X_EUR_'))

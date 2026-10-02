"""## Executive summary (read this first)

Same-day peer mutations cannot alter the primary cross-market features.
"""
from location01_helpers import panel
from qfbench2_track_forecasting.location01.feature_own_history import history_state
from qfbench2_track_forecasting.location01.feature_cross_market import prepare_cross,cross_market

def test_lag_safe():
    s,k,t=panel();a=history_state(s,k)
    before=cross_market(prepare_cross(a),'EUR',t,a['assets'])
    s['UST_2Y'].loc[t]=1e6;b=history_state(s,k)
    assert before==cross_market(prepare_cross(b),'EUR',t,b['assets'])

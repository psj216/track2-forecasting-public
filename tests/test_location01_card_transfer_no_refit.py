"""## Executive summary (read this first)

Card evaluation has no fit calls, and matched features ignore outcome objects.
"""
import ast
import inspect
import numpy as np
from location01_helpers import panel
from backtesting.location01 import evaluate_card_transfer
from backtesting.location01.build_features import card_features
from qfbench2_track_forecasting.location01.feature_own_history import history_state
from qfbench2_track_forecasting.location01.engine import prepare,features

def test_card_transfer_no_refit():
    tree=ast.parse(inspect.getsource(evaluate_card_transfer))
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='fit' for n in ast.walk(tree))
    s,k,t=panel();state=history_state(s,k);cross,reg=prepare(state)
    b=np.arange(500.)[:,None,None]*.001+float(s['EUR'].loc[t])
    schema=sorted(features(state,cross,reg,'EUR','level',t,21,b[:,0,0],float(s['EUR'].loc[t]),1.))
    card={'origin':str(t.date()),'assets':['EUR'],'horizons':[21]}
    x=card_features(card,b,state,cross,reg,schema)
    card['truth']=1e9
    np.testing.assert_array_equal(x,card_features(card,b,state,cross,reg,schema))

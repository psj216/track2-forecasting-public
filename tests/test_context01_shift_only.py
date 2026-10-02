"""## Executive summary (read this first)
Verify the frozen context research contract with synthetic data only.
"""
import numpy as np
from qfbench2_track_forecasting.context01.deterministic_annotator import annotate,matrix
from qfbench2_track_forecasting.context01.context_schema import schema
CARD=dict(id='synthetic',family='T2-F1',origin='2020-01-06',assets=['UST_2Y'],horizons=[21,63],cells=2,target_type='level',frequency='daily')
def annotation(card=CARD):return annotate(card,'Assuming inflation rises, forecast the joint yield path in 2020 above 2 percent.', ['The Federal Reserve may consider uncertainty.'])
from qfbench2_track_forecasting.context01.engine import apply
def test_safety_cap_and_constant_translation():
 x=np.random.default_rng(19).normal(size=(200,2,2));a=apply(x,[99,-99,1,0]);sd=x.std(axis=0);np.testing.assert_allclose(a-x,np.broadcast_to(np.array([[10,-10],[1,0]])*sd,x.shape));np.testing.assert_allclose(a.std(axis=0),sd)

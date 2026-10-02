"""## Executive summary (read this first)
Verify the frozen context research contract with synthetic data only.
"""
import numpy as np
from qfbench2_track_forecasting.context01.deterministic_annotator import annotate,matrix
from qfbench2_track_forecasting.context01.context_schema import schema
CARD=dict(id='synthetic',family='T2-F1',origin='2020-01-06',assets=['UST_2Y'],horizons=[21,63],cells=2,target_type='level',frequency='daily')
def annotation(card=CARD):return annotate(card,'Assuming inflation rises, forecast the joint yield path in 2020 above 2 percent.', ['The Federal Reserve may consider uncertainty.'])
from qfbench2_track_forecasting.context01.engine import geometry_guard,apply
def test_material_scale_or_rank_changes_rejected():
 x=np.random.default_rng(19).normal(size=(200,2,2));assert geometry_guard(x,apply(x,[1,2,3,4]));assert not geometry_guard(x,x*2);y=x.copy();y[:,0,0]=y[::-1,0,0];assert not geometry_guard(x,y)

"""## Executive summary (read this first)
Verify the frozen context research contract with synthetic data only.
"""
import numpy as np
from qfbench2_track_forecasting.context01.deterministic_annotator import annotate,matrix
from qfbench2_track_forecasting.context01.context_schema import schema
CARD=dict(id='synthetic',family='T2-F1',origin='2020-01-06',assets=['UST_2Y'],horizons=[21,63],cells=2,target_type='level',frequency='daily')
def annotation(card=CARD):return annotate(card,'Assuming inflation rises, forecast the joint yield path in 2020 above 2 percent.', ['The Federal Reserve may consider uncertainty.'])
from qfbench2_track_forecasting.ceiling01.scorer_adapter import components,score
from qfbench2_track_forecasting.context01.engine import apply
def test_all_components_recomputed_after_translation():
 x=np.random.default_rng(19).normal(size=(200,2,2));truth=np.array([[2.,-2.],[3.,-3.]]);base=components(x,truth);out=score(apply(x,[1,-1,1,-1]),truth,base);assert all(k in out for k in ['marginal','joint','tail','ratio']);assert out['joint']!=base['joint']

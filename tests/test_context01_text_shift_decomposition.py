"""## Executive summary (read this first)
Verify the frozen context research contract with synthetic data only.
"""
import numpy as np
from qfbench2_track_forecasting.context01.deterministic_annotator import annotate,matrix
from qfbench2_track_forecasting.context01.context_schema import schema
CARD=dict(id='synthetic',family='T2-F1',origin='2020-01-06',assets=['UST_2Y'],horizons=[21,63],cells=2,target_type='level',frequency='daily')
def annotation(card=CARD):return annotate(card,'Assuming inflation rises, forecast the joint yield path in 2020 above 2 percent.', ['The Federal Reserve may consider uncertainty.'])
from qfbench2_track_forecasting.context01.text_effect import location_only,text_shift
def test_full_text_variance_is_separate_from_center_translation():
 x=np.arange(400.).reshape(200,2)/100;t=2*x+3;p=location_only(t,x)
 np.testing.assert_allclose(np.median(p,axis=0),np.median(t,axis=0));np.testing.assert_allclose(np.var(p,axis=0),np.var(x,axis=0));assert not np.allclose(np.var(t,axis=0),np.var(p,axis=0))

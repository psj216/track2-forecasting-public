"""## Executive summary (read this first)
Verify the frozen context research contract with synthetic data only.
"""
import numpy as np
from qfbench2_track_forecasting.context01.deterministic_annotator import annotate,matrix
from qfbench2_track_forecasting.context01.context_schema import schema
CARD=dict(id='synthetic',family='T2-F1',origin='2020-01-06',assets=['UST_2Y'],horizons=[21,63],cells=2,target_type='level',frequency='daily')
def annotation(card=CARD):return annotate(card,'Assuming inflation rises, forecast the joint yield path in 2020 above 2 percent.', ['The Federal Reserve may consider uncertainty.'])
from qfbench2_track_forecasting.context01.residual_target import residual
def test_text_residual_and_zero_dispersion_floor():
 x=np.array([[0.,2.],[2.,2.]]);d=residual(x,np.array([3.,2.]));np.testing.assert_allclose(d,[2.,0.]);assert np.isfinite(d).all()

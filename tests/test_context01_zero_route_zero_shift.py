"""## Executive summary (read this first)
Verify the frozen context research contract with synthetic data only.
"""
import numpy as np
from qfbench2_track_forecasting.context01.deterministic_annotator import annotate,matrix
from qfbench2_track_forecasting.context01.context_schema import schema
CARD=dict(id='synthetic',family='T2-F1',origin='2020-01-06',assets=['UST_2Y'],horizons=[21,63],cells=2,target_type='level',frequency='daily')
def annotation(card=CARD):return annotate(card,'Assuming inflation rises, forecast the joint yield path in 2020 above 2 percent.', ['The Federal Reserve may consider uncertainty.'])
from qfbench2_track_forecasting.context01.context_router import route,EXPERTS
from qfbench2_track_forecasting.context01.engine import apply
def test_unmatched_route_and_unavailable_source_are_exact_zero():
 pred={e:np.array([4.])for e in EXPERTS};av={e:np.array([True])for e in EXPERTS};a=route(['generic_none'],['MKT'],pred,av);assert a[0][0]==a[1][0]==0 and not a[2][0]
 av={e:np.array([False])for e in EXPERTS};b=route(['growth'],['MKT'],pred,av);assert b[0][0]==0
 x=np.arange(200.).reshape(200,1,1);np.testing.assert_array_equal(x,apply(x,a[0]))

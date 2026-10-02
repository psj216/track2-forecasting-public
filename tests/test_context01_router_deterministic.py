"""## Executive summary (read this first)
Verify the frozen context research contract with synthetic data only.
"""
import numpy as np
from qfbench2_track_forecasting.context01.deterministic_annotator import annotate,matrix
from qfbench2_track_forecasting.context01.context_schema import schema
CARD=dict(id='synthetic',family='T2-F1',origin='2020-01-06',assets=['UST_2Y'],horizons=[21,63],cells=2,target_type='level',frequency='daily')
def annotation(card=CARD):return annotate(card,'Assuming inflation rises, forecast the joint yield path in 2020 above 2 percent.', ['The Federal Reserve may consider uncertainty.'])
from qfbench2_track_forecasting.context01.context_router import eligible,route,EXPERTS
def test_priority_and_direct_equity_mapping():
 assert eligible(['equity'],'AUD')==[];assert eligible(['equity'],'MKT')==['F'];assert eligible(['liquidity','rates'],'AUD')==['L','TBILL','TBOND']
 pred={e:np.ones(2)*i for i,e in enumerate(EXPERTS)};av={e:np.ones(2,bool)for e in EXPERTS};a=route(['liquidity'],['AUD','MKT'],pred,av);b=route(['liquidity'],['AUD','MKT'],pred,av)
 np.testing.assert_array_equal(a[0],b[0])

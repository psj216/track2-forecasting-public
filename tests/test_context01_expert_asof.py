"""## Executive summary (read this first)
Verify the frozen context research contract with synthetic data only.
"""
import numpy as np
from qfbench2_track_forecasting.context01.deterministic_annotator import annotate,matrix
from qfbench2_track_forecasting.context01.context_schema import schema
CARD=dict(id='synthetic',family='T2-F1',origin='2020-01-06',assets=['UST_2Y'],horizons=[21,63],cells=2,target_type='level',frequency='daily')
def annotation(card=CARD):return annotate(card,'Assuming inflation rises, forecast the joint yield path in 2020 above 2 percent.', ['The Federal Reserve may consider uncertainty.'])
import pandas as pd
from qfbench2_track_forecasting.location01.model import purged_mask
def test_strict_maturity_and_max_horizon_embargo():
 rows=pd.DataFrame(dict(origin=['2019-01-01','2019-02-01','2019-12-01'],target_end=['2019-04-01','2020-02-01','2019-12-15']));m=purged_mask(rows,'2020-01-06');np.testing.assert_array_equal(m,[True,False,False])

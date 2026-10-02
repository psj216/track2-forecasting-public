"""## Executive summary (read this first)
Verify the frozen context research contract with synthetic data only.
"""
import numpy as np
from qfbench2_track_forecasting.context01.deterministic_annotator import annotate,matrix
from qfbench2_track_forecasting.context01.context_schema import schema
CARD=dict(id='synthetic',family='T2-F1',origin='2020-01-06',assets=['UST_2Y'],horizons=[21,63],cells=2,target_type='level',frequency='daily')
def annotation(card=CARD):return annotate(card,'Assuming inflation rises, forecast the joint yield path in 2020 above 2 percent.', ['The Federal Reserve may consider uncertainty.'])
def test_four_fixed_family_splits_do_not_mix_cards():
 ids=np.repeat(['T2-F1','T2-F2','T2-F3','T2-F4'],6)
 for f in sorted(set(ids)):
  test=ids==f;assert test.sum()==6 and (~test).sum()==18 and not(set(ids[test])&set(ids[~test]))

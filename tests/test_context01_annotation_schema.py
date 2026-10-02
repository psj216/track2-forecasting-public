"""## Executive summary (read this first)
Verify the frozen context research contract with synthetic data only.
"""
import numpy as np
from qfbench2_track_forecasting.context01.deterministic_annotator import annotate,matrix
from qfbench2_track_forecasting.context01.context_schema import schema
CARD=dict(id='synthetic',family='T2-F1',origin='2020-01-06',assets=['UST_2Y'],horizons=[21,63],cells=2,target_type='level',frequency='daily')
def annotation(card=CARD):return annotate(card,'Assuming inflation rises, forecast the joint yield path in 2020 above 2 percent.', ['The Federal Reserve may consider uncertainty.'])
from qfbench2_track_forecasting.context01.context_schema import TOPICS
def test_fixed_schema_finite_and_word_boundaries():
 a=annotation();x,rows,cols=matrix([CARD],{'synthetic':a});assert x.shape==(2,513) and np.isfinite(x).all();assert [s['stage']for s in cols]==sorted(s['stage']for s in cols)
 b=annotate(CARD,'warnings on rates',[]);assert 'geopolitical'not in b['economic_topics']

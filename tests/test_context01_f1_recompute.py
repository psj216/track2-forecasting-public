"""## Executive summary (read this first)
Verify the frozen context research contract with synthetic data only.
"""
import numpy as np
from qfbench2_track_forecasting.context01.deterministic_annotator import annotate,matrix
from qfbench2_track_forecasting.context01.context_schema import schema
CARD=dict(id='synthetic',family='T2-F1',origin='2020-01-06',assets=['UST_2Y'],horizons=[21,63],cells=2,target_type='level',frequency='daily')
def annotation(card=CARD):return annotate(card,'Assuming inflation rises, forecast the joint yield path in 2020 above 2 percent.', ['The Federal Reserve may consider uncertainty.'])
from qfbench2_track_forecasting.ceiling01.scorer_adapter import components,score
from backtesting.context01.evaluate_multi import f1_safety
def test_f1_joint_damage_has_separate_path_verdict():
 base=dict(marginal=1.,joint=1.,tail=1.);c=dict(card_id='x',family='T2-F1',cells=2,single=False,baseline=base,oracle={**base,'ratio':.4},models={'B5':dict(marginal=.9,joint=1.5,tail=.9,ratio=1.1)})
 assert f1_safety([c],'B5')=='CONTEXT_LOCATION_SIGNAL_BUT_PATH_REQUIRED'

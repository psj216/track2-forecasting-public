"""## Executive summary (read this first)
Verify the frozen context research contract with synthetic data only.
"""
import numpy as np
from qfbench2_track_forecasting.context01.deterministic_annotator import annotate,matrix
from qfbench2_track_forecasting.context01.context_schema import schema
CARD=dict(id='synthetic',family='T2-F1',origin='2020-01-06',assets=['UST_2Y'],horizons=[21,63],cells=2,target_type='level',frequency='daily')
def annotation(card=CARD):return annotate(card,'Assuming inflation rises, forecast the joint yield path in 2020 above 2 percent.', ['The Federal Reserve may consider uncertainty.'])
from copy import deepcopy
from backtesting.context01.negative_controls import controlled_annotations
def test_rotation_is_within_family_and_keeps_structure():
 a=deepcopy(CARD);b={**CARD,'id':'b'};anns={'synthetic':annotation(a),'b':annotate(b,'Growth surprise',[])};out=controlled_annotations([a,b],anns,'A')
 assert out['synthetic']['features']['growth']==anns['b']['features']['growth'];assert out['synthetic']['features']['horizons_count']==anns['synthetic']['features']['horizons_count']

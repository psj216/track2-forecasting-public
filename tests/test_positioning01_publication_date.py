"""## Executive summary (read this first)
Adversarial synthetic checks for source publication, revisions, purity and inherited chronology.
"""
import numpy as np
import pandas as pd
import pytest
from qfbench2_track_forecasting.positioning01.publication_alignment import latest,age,cutoff
from qfbench2_track_forecasting.positioning01.normalization import shares,past_z
from qfbench2_track_forecasting.positioning01.source_schema import original_guard
from qfbench2_track_forecasting.positioning01.source_asset_map import admitted
from qfbench2_track_forecasting.positioning01.model import QuantityModel,purged_mask,inner_splits,ALPHAS
from qfbench2_track_forecasting.positioning01.engine import shift,geometry_guard
from qfbench2_track_forecasting.positioning01.positioning_features import report_features
from qfbench2_track_forecasting.positioning01.flow_features import enrich as flow_enrich
from qfbench2_track_forecasting.positioning01.liquidity_features import enrich as liquidity_enrich
from backtesting.positioning01.negative_controls import donor_index,rotate
import hashlib
R=[dict(release_date='2020-01-03',observation_date='2019-12-31',value=2,event_id='a'),dict(release_date='2020-01-10',observation_date='2020-01-07',value=3,event_id='b')]
def test_release_day_excluded_next_business_day_admitted():
 assert latest(R,'2020-01-10',10)['event_id']=='a'
 assert latest(R,'2020-01-13',10)['event_id']=='b'
 assert cutoff('2020-01-13')=='2020-01-10'

def test_after_close_and_unknown_time_cannot_enter_previous_close():
 r=[dict(release_date='2020-01-09',publication_time_et='16:30',event_id='x')]
 assert latest(r,'2020-01-10',10) is None
 assert latest(r,'2020-01-13',10)['event_id']=='x'
 r[0]['publication_time_et']='23:59'
 assert latest(r,'2020-01-10',10) is None

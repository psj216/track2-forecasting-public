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
def test_weekly_measurement_vs_actual_release():
 from backtesting.positioning01.build_source_data import parse_liquidity
 b=b'<pre>January 9, 2020\nMillions of dollars\nReserve Bank credit, Averages of daily figures Week ended Jan 8, 2020\nReserve balances with Federal Reserve Banks 1,200 +1 +2 1,400</pre>'
 x=parse_liquidity(b,'2020-01-09');assert x['value']==1200 and x['observation_date']=='2020-01-08'

def test_historical_abbreviated_reserves_with_footnote_not_number():
 from backtesting.positioning01.build_source_data import parse_liquidity
 b=b'<pre>January 6, 2000\nMillions of dollars\nReserve Bank Credit, Averages of daily figures Week ended Jan 5, 2000\nReserve balances with F.R. Banks (6) 8,798 +3 -5 1,270</pre>'
 assert parse_liquidity(b,'2000-01-06')['value']==8798

def test_original_ascii_format_has_identical_weekly_mean():
 from backtesting.positioning01.build_source_data import parse_liquidity
 b=b'January 9, 2020\nMillions of dollars\nAverages of daily figures Week ended Jan 8, 2020\nReserve balances with Federal Reserve Banks 1,200 +1 +2 1,400'
 assert parse_liquidity(b,'2020-01-09')['value']==1200

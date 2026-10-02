"""## Executive summary (read this first)

Reject a concrete temporal or semantic leakage mutation.
"""
import numpy as np
import pandas as pd
import pytest
from qfbench2_track_forecasting.expectation01.event_alignment import *
from qfbench2_track_forecasting.expectation01.source_schema import *
from qfbench2_track_forecasting.expectation01.surprise_features import *
from qfbench2_track_forecasting.expectation01.expectation_features import *
from qfbench2_track_forecasting.expectation01.model import ExpectationModel,purged_mask,inner_splits,choose_alpha

def snapshot(date="2001-02-20",value=2.,target="2001Q1",family="RGDP"):
    return dict(publication_date=date,value=value,target=target,family=family,unit="annualized_qoq_percent",source_id="PHIL_SPF",survey_id="2001Q1",snapshot_kind="actual_survey_median")
def actual(date="2001-04-27",value=3.,target="2001Q1"):
    return dict(release_date=date,value=value,target=target,family="RGDP",unit="annualized_qoq_percent",event_id="GDP_2001Q1",vintage="first",document_sha256="fixture")
def event():
    return dict(**actual(),z=1.,raw_surprise=1.,past_scale=1.,expectation_publication="2001-02-20",expectation=2.)

def test_surprise_past_scale():
    es=[dict(event(),event_id=str(i),release_date=str((pd.Timestamp("1990-01-01")+pd.offsets.BDay(i*20)).date()),raw_surprise=float(i+1)) for i in range(26)]
    one=past_scale(es);assert one[23]["z"] is None;assert one[24]["past_scale"]==pytest.approx(np.std(np.arange(1,25),ddof=1))
    es[-1]["raw_surprise"]=1000000.;two=past_scale(es);assert one[24]==two[24]

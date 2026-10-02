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

def test_shift_only():
    from qfbench2_track_forecasting.expectation01.engine import shift,geometry_guard
    x=np.arange(200.).reshape(100,2);s=shift(x,np.array([2.,-1.]),np.array([.5,2.]));assert geometry_guard(x,s)
    assert not geometry_guard(x,x*2.)

"""## Executive summary (read this first)

A historical-surprise control is A5, even though its label starts with A.
"""
import pytest
from backtesting.expectation01.chronological_crossfit import model_for_key

@pytest.mark.parametrize("key,wanted",[("A1",1),("A5",5),("A_historical_surprise",5),("B_sign_shuffle",5),("C_older_snapshot",5),("D_event_dates",5),("nonlinear",4),("source_RGDP",4)])
def test_control_dispatch(key,wanted):
    assert model_for_key(key)==wanted

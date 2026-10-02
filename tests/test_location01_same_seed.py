"""## Executive summary (read this first)

The actual no-text V5.1 code path is reproducible with the fixed seed.
"""
import numpy as np
from location01_helpers import panel
from qfbench2_track_forecasting.thesis01.v51_shift import v51_no_text_prior

def test_same_seed():
    s,k,t=panel();args=(s['EUR'],'EUR','level',[5,21,63],'T2-F2',str(t.date()),19,500)
    np.testing.assert_array_equal(v51_no_text_prior(*args),v51_no_text_prior(*args))

"""## Executive summary (read this first)

Daily increments are summed after, rather than including, the origin.
"""
import numpy as np
import pandas as pd
from qfbench2_track_forecasting.location01.oracle_target import target

def test_return_semantics():
    dates=pd.bdate_range('2001-01-02',periods=25)
    s=pd.Series(np.arange(25.),index=dates)
    for kind in ('return','log_return'):
        y,end=target(s,kind,dates[3],5)
        assert y==sum(range(4,9)) and end==dates[8]

"""## Executive summary (read this first)

Level targets retain forecast levels, with a verified endpoint change.
"""
import numpy as np
import pandas as pd
from qfbench2_track_forecasting.location01.oracle_target import target

def test_level_semantics():
    dates=pd.bdate_range('2001-01-02',periods=25)
    s=pd.Series(np.arange(25.)+100,index=dates)
    y,end=target(s,'level',dates[0],5)
    assert y==105 and end==dates[5] and y-s.iloc[0]==5

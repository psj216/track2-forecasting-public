"""## Executive summary (read this first)

Training origins observe the full 189-business-day exclusion and label maturity.
"""
import numpy as np
import pandas as pd
from qfbench2_track_forecasting.location01.model import purged_mask

def test_purge():
    d=pd.bdate_range('2008-01-01','2010-01-15')
    rows=pd.DataFrame({'origin':d,'target_end':d+pd.offsets.BDay(189)})
    boundary=pd.Timestamp('2010-01-01');mask=purged_mask(rows,boundary)
    assert mask.any() and (~mask).any()
    assert (rows.loc[mask,'target_end']<boundary).all()
    assert (rows.loc[mask,'origin']<boundary-pd.offsets.BDay(189)).all()

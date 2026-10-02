"""## Executive summary (read this first)

Inner train and validation labels mature before the external test boundary.
"""
import numpy as np
import pandas as pd
from qfbench2_track_forecasting.location01.model import inner_splits,purged_mask,choose_alpha

def test_inner_no_outer():
    d=pd.bdate_range('2001-01-02','2013-12-31')[::2]
    rows=pd.DataFrame({'origin':d,'target_end':d+pd.offsets.BDay(189)})
    for tr,val in inner_splits(rows,2009):
        assert not np.any(tr&val)
        assert rows.loc[tr,'target_end'].max()<rows.loc[val,'origin'].min()
        assert rows.loc[val,'target_end'].max()<pd.Timestamp('2010-01-01')
    train=purged_mask(rows,'2010-01-01');x=np.arange(len(d),dtype=float)[:,None]
    y=np.sin(np.arange(len(d)));a,_=choose_alpha(x[train],y[train],['O_move'],rows.loc[train].reset_index(drop=True),3,2009)
    y[~train]=1e12
    b,_=choose_alpha(x[train],y[train],['O_move'],rows.loc[train].reset_index(drop=True),3,2009)
    assert a==b

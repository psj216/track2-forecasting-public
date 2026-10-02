"""## Executive summary (read this first)

Controls preserve training label sets and use strictly past wrong-date donors.
"""
import numpy as np
import pandas as pd
from backtesting.location01.negative_controls import permute_labels,past_feature_donors,wrong_date_features

def test_controls():
    d=pd.bdate_range('2001-01-02','2004-12-31')[::5]
    rows=pd.DataFrame([{'origin':str(t.date()),'asset':a,'horizon':5} for t in d for a in ('EUR','JPY')])
    y=np.arange(len(rows),dtype=float)
    for c in ('A_label_time','C_asset_label'):
        v=permute_labels(rows,y,c);np.testing.assert_array_equal(np.sort(v),y)
        assert not np.array_equal(v,y)
        np.testing.assert_array_equal(v,permute_labels(rows,y,c))
    donor=past_feature_donors(rows);valid=donor>=0
    assert (rows.origin.to_numpy()[donor[valid]]<rows.origin.to_numpy()[valid]).all()
    x=np.column_stack((y,y));xx,_=wrong_date_features(x,rows,['M_asset','O_move'])
    np.testing.assert_array_equal(xx[:,0],x[:,0])
    np.testing.assert_array_equal(xx[valid,1],x[donor[valid],1])

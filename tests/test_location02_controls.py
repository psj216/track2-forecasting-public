"""Executive summary: null controls preserve chronology and deterministic release blocks."""
import numpy as np
import pandas as pd
from backtesting.location02.evaluate import control_x,CONTROLS
from backtesting.location02.source_dataset import activation
from backtesting.location02.model import SEED


def test_gaussian_release_blocks_and_seed():
    rows=pd.DataFrame({'origin':['2019-01-02','2019-02-01','2019-03-01'],'round_id':['a','a','b']})
    x=np.ones((3,5))
    first=control_x(rows,x,'GAUSSIAN_FULL5',SEED,[])
    np.testing.assert_array_equal(first,control_x(rows,x,'GAUSSIAN_FULL5',SEED,[]))
    np.testing.assert_array_equal(first[0],first[1])
    assert first.shape==(3,5) and not np.array_equal(first[0],first[2])


def test_date_delays_do_not_activate_future():
    state=dict(round_id='2020Q1',publication_date='2020-01-24',available_at=activation('2020-01-24').isoformat(),
       eligible=True,HICP_NCY=2.,GDP_NCY=1.,HICP_NCY_REV_SAME_TARGET=.1,GDP_NCY_REV_SAME_TARGET=.2)
    rows=pd.DataFrame({'origin':['2020-01-02','2020-01-23']})
    out=control_x(rows,np.ones((2,5)),'RELEASE_DATE_PERMUTATION',SEED,[state])
    assert np.isnan(out).all()

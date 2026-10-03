"""Executive summary: future mutation uses the exact original input serialization."""
import copy
import numpy as np
import pandas as pd
from backtesting.location02.finalize import mutated_feature_rows
from backtesting.location02.source_dataset import activation


def test_unchanged_events_retain_csv_parsed_bits():
    state=dict(round_id='2020Q1',publication_date='2020-01-24',available_at=activation('2020-01-24').isoformat(),
       eligible=True,HICP_NCY=1.,GDP_NCY=2.,HICP_NCY_REV_SAME_TARGET=.19999999999999996,GDP_NCY_REV_SAME_TARGET=.1)
    future=copy.deepcopy(state);future.update(round_id='2020Q2',publication_date='2020-05-04',available_at=activation('2020-05-04').isoformat())
    states=[state,future];mutated=copy.deepcopy(states);mutated[1]['HICP_NCY']=999.
    rows=pd.DataFrame({'origin':['2020-02-03','2020-06-01']})
    original=np.array([[1.,2.,.1999999999999999,.1,5.],[1.,2.,.1999999999999999,.1,20.]])
    changed=mutated_feature_rows(rows,original,states,mutated)
    np.testing.assert_array_equal(changed[0],original[0])
    assert changed[1,0]==999.

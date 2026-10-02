"""## Executive summary (read this first)

Check that the supervised shift is truth-minus-median in baseline SD units.
"""
import numpy as np
from qfbench2_track_forecasting.location01.oracle_target import oracle_label

def test_oracle_target():
    x=np.array([-4.,-1.,0.,1.,7.]);m,s,d=oracle_label(x,2.)
    assert m==0 and np.isclose(d*s,2.) and s==np.std(x)
    assert oracle_label(np.ones(5),2)[2]==1e8

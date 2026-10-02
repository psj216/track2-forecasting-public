"""## Executive summary (read this first)
Full coverage impact must use the active-only perfect shift on the corresponding full ledger.
"""
import numpy as np
import pytest
from backtesting.positioning01.diagnostics import summary
def test_corresponding_full_oracle_capture():
 r=summary(np.arange(1.,5.),np.array([.2,.3,0,0]),np.ones(4),np.array([.9,.9,1.,1.]),np.full(4,.5),np.array([True,True,False,False]))
 assert r['active_only_oracle_on_full']==.75
 assert r['full']['oracle_capture_fraction']==pytest.approx(.2)

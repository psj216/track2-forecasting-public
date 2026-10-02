"""## Executive summary (read this first)

Additive updates preserve ranks, centered distances and variances.
"""
import numpy as np
from qfbench2_track_forecasting.location01.engine import shift,geometry_guard

def test_geometry():
    x=np.random.default_rng(19).normal(size=(500,5,3));y=shift(x,np.ones((5,3))*.3,x.std(axis=0))
    assert geometry_guard(x,y)
    np.testing.assert_allclose(x.var(axis=0),y.var(axis=0),rtol=1e-12)
    assert not geometry_guard(x,y*1.01)

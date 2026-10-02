"""## Executive summary (read this first)

Accept float64 translation ties; reject material geometry changes.
"""
import numpy as np
import pytest
from qfbench2_track_forecasting.location01.engine import geometry_guard

def tied_translation(scale=1.0):
    lo=np.float64(scale);hi=np.nextafter(lo,np.inf)
    x=np.array([hi,lo,np.nextafter(hi,np.inf),lo])[:,None]
    return x,x+lo

def test_normal_uniform_shift():
    x=np.random.default_rng(19).normal(size=(500,5,3))
    assert geometry_guard(x,x+np.arange(15).reshape(5,3)*.17)

def test_large_values_tiny_spacing_round_to_tie():
    x,y=tied_translation(1e16)
    assert np.any(np.diff(np.sort(x[:,0]))>0)
    assert geometry_guard(x,y)

def test_exact_argsort_false_negative():
    x,y=tied_translation()
    assert not np.array_equal(np.argsort(x,axis=0),np.argsort(y,axis=0))
    assert geometry_guard(x,y)

def test_strict_order_reversal_rejected():
    x=np.arange(10,dtype=float)[:,None];y=x.copy();y[[2,3]]=y[[3,2]]
    assert not geometry_guard(x,y)

def test_one_draw_different_shift_rejected():
    x=np.random.default_rng(19).normal(size=(200,3));y=x+.2;y[15,1]+=.001
    assert not geometry_guard(x,y)

def test_scale_change_rejected():
    x=np.random.default_rng(19).normal(size=(200,3))
    assert not geometry_guard(x,x*1.01+.2)

def test_variance_change_rejected():
    x=np.arange(20,dtype=float)[:,None];y=x.copy();y[-1]+=10
    assert np.var(x)!=np.var(y)
    assert not geometry_guard(x,y)

def test_draw_pairing_reorder_rejected():
    x=np.random.default_rng(19).normal(size=(200,3));y=x+.2;y[:,1]=y[::-1,1]
    assert not geometry_guard(x,y)

@pytest.mark.parametrize('bad',[np.nan,np.inf,-np.inf])
def test_nonfinite_rejected(bad):
    x=np.zeros((200,2));y=x.copy();y[1,1]=bad
    assert not geometry_guard(x,y)
    assert not geometry_guard(y,x)

def test_same_input_deterministic_and_unmodified():
    x,y=tied_translation();xx=x.copy();yy=y.copy()
    assert geometry_guard(x,y) is True
    assert all(geometry_guard(x,y) is True for _ in range(5))
    np.testing.assert_array_equal(x,xx);np.testing.assert_array_equal(y,yy)

def test_shape_and_empty_rejected():
    assert not geometry_guard(np.zeros((200,2)),np.zeros((200,1)))
    assert not geometry_guard(np.empty((0,2)),np.empty((0,2)))

def test_shape_one_cell_and_constant_draws():
    assert geometry_guard(np.ones(200),np.ones(200)+.25)
    assert geometry_guard(np.ones((200,2)),np.ones((200,2))+np.array([.25,-.5]))

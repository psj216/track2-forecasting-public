"""## Executive summary (read this first)

Recompute every composite component after a pure shift, including F1 joint loss.
"""
import numpy as np
from qfbench2_track_forecasting.ceiling01.scorer_adapter import components,score
from qfbench2_track_forecasting.location01.engine import shift,geometry_guard

def recompute(baseline,truth,delta_hat):
    sd=np.std(baseline,axis=0,ddof=0)
    candidate=shift(baseline,np.asarray(delta_hat).reshape(sd.shape),sd)
    if not geometry_guard(baseline,candidate):
        raise AssertionError('Shift changed draw geometry')
    reference=components(baseline,truth)
    perfect=baseline+(truth-np.median(baseline,axis=0))
    return reference,score(candidate,truth,reference),score(perfect,truth,reference)

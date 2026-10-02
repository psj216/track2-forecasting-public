"""## Executive summary (read this first)
Use active-only perfect shifts for the corresponding full-ledger capture denominator.
"""
import numpy as np
from backtesting.location01.diagnostics import metrics
from backtesting.expectation01.diagnostics import success
def summary(y,pred,base,candidate,oracle,active):
    if not len(y) or not active.any():return dict(status='NOT_ACTIVE',active_cells=0,full_cells=len(y),coverage_fraction=0.,active=None,full=None)
    a=metrics(y[active],pred[active],base[active],candidate[active],oracle[active]);full_oracle=np.where(active,oracle,base);f=metrics(y,pred,base,candidate,full_oracle)
    return dict(active=a,full=f,active_cells=int(active.sum()),full_cells=len(y),coverage_fraction=float(active.mean()),active_only_oracle_on_full=float(full_oracle.sum()/base.sum()),global_perfect_location_ratio=float(oracle.sum()/base.sum()))

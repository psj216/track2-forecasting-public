"""## Executive summary (read this first)

Report inherited prediction diagnostics and full-impact-aware frozen success gates.
"""
import numpy as np
from backtesting.location01.diagnostics import metrics

def summary(y,pred,base,candidate,oracle,active):
    a=metrics(y[active],pred[active],base[active],candidate[active],oracle[active]);f=metrics(y,pred,base,candidate,oracle)
    active_only_oracle=base.copy();active_only_oracle[active]=oracle[active]
    return dict(active=a,full=f,active_cells=int(active.sum()),full_cells=len(y),coverage_fraction=float(active.mean()),active_only_oracle_on_full=float(active_only_oracle.sum()/base.sum()))

def success(result,folds,clear,available):
    if available<3:return "INSUFFICIENT_TEMPORAL_COVERAGE"
    a,f=result["active"],result["full"]
    if not(a["ratio"]<=.97 and f["ratio"]<1 and sum(v<1 for v in folds)>=3 and a["oracle_capture_fraction"]>.05 and clear):return "NO"
    if a["ratio"]<=.80 and f["ratio"]<=.98 and a["oracle_capture_fraction"]>=.35:return "MOONSHOT"
    if a["ratio"]<=.90 and f["ratio"]<=.99 and a["oracle_capture_fraction"]>=.20:return "STRONG_YES"
    if a["ratio"]<=.95 and f["ratio"]<=.995 and a["oracle_capture_fraction"]>=.10:return "YES"
    return "WEAK_YES"

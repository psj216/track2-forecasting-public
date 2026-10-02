"""## Executive summary (read this first)

Resample whole calendar-year blocks, preserving all within-year cells.
"""
import numpy as np

REPLICATES=2000

def year_bootstrap(years,baseline,candidate,oracle=None,seed=1903):
    unique=np.unique(years)
    sums=np.array([[baseline[years==y].sum(),candidate[years==y].sum(),
                    0. if oracle is None else oracle[years==y].sum()] for y in unique])
    picked=np.random.default_rng(seed).integers(0,len(unique),(REPLICATES,len(unique)))
    totals=sums[picked].sum(axis=1); ratio=totals[:,1]/totals[:,0]
    out={'replicates':REPLICATES,'block':'calendar year; all asset/horizon cells together',
         'blocks':len(unique),'ratio_95_interval':np.quantile(ratio,[.025,.975]).tolist()}
    if oracle is not None:
        capture=(totals[:,0]-totals[:,1])/(totals[:,0]-totals[:,2])
        out['capture_95_interval']=np.quantile(capture,[.025,.975]).tolist()
    return out

"""## Executive summary (read this first)

Union overlapping events so no shared event is split across resampled origins.
"""
import numpy as np
from backtesting.location01.bootstrap import year_bootstrap

REPLICATES=2000

def event_blocks(origins,origin_events,event_dates):
    parent=list(range(len(origins)));owner={}
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    def union(i,j):parent[find(i)]=find(j)
    for i,d in enumerate(origins):
        for event in origin_events[d]:
            keys=(event,"DATE:"+event_dates[event])
            for key in keys:
                if key in owner:union(i,owner[key])
                else:owner[key]=i
    roots=[find(i) for i in range(len(origins))];mapping={r:j for j,r in enumerate(sorted(set(roots)))}
    return {d:mapping[r] for d,r in zip(origins,roots)}

def block_bootstrap(blocks,base,candidate,oracle=None,seed=1903):
    ids=np.unique(blocks);sums=np.array([[base[blocks==b].sum(),candidate[blocks==b].sum(),0. if oracle is None else oracle[blocks==b].sum()] for b in ids])
    if len(ids)<2:return dict(status="INSUFFICIENT_INDEPENDENT_EVENT_BLOCKS",blocks=len(ids),replicates=0)
    picked=np.random.default_rng(seed).integers(0,len(ids),(REPLICATES,len(ids)));totals=sums[picked].sum(axis=1);ratio=totals[:,1]/totals[:,0]
    out=dict(replicates=REPLICATES,blocks=len(ids),ratio_95_interval=np.quantile(ratio,[.025,.975]).tolist(),seed=seed)
    if oracle is not None:out["capture_95_interval"]=np.quantile((totals[:,0]-totals[:,1])/(totals[:,0]-totals[:,2]),[.025,.975]).tolist()
    return out

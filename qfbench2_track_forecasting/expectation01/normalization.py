"""## Executive summary (read this first)

Standardize surprise only using at least 24 strictly earlier family events.
"""
import numpy as np

def past_scale(events):
    past={};out=[]
    for event in sorted(events,key=lambda e:(e["release_date"],e["event_id"])):
        e=dict(event);eligible=[v for d,v in past.get(e["family"],[]) if d<e["release_date"]]
        sd=float(np.std(eligible,ddof=1)) if len(eligible)>=24 else None
        e["prior_events"]=len(eligible);e["past_scale"]=sd
        e["z"]=e["raw_surprise"]/sd if sd is not None and sd>1e-12 else None
        out.append(e);past.setdefault(e["family"],[]).append((e["release_date"],e["raw_surprise"]))
    return out

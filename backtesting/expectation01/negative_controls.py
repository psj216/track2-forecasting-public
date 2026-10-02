"""## Executive summary (read this first)

Construct historical controls before folds without introducing early realized information.
"""
import numpy as np
from qfbench2_track_forecasting.expectation01.event_alignment import scheduled_date_control
from qfbench2_track_forecasting.expectation01.normalization import past_scale

CONTROLS=("A_historical_surprise","B_sign_shuffle","C_older_snapshot","D_event_dates")

def controlled_events(events,name,snapshots):
    out=[dict(e) for e in events];rng=np.random.default_rng(1907)
    if name=="D_event_dates":return scheduled_date_control(out)
    for i,e in enumerate(out):
        if name=="A_historical_surprise":
            prior=[p for p in events if p["family"]==e["family"] and p["release_date"]<e["release_date"]]
            e["raw_surprise"]=prior[int(rng.integers(len(prior)))]["raw_surprise"] if prior else 0.
        elif name=="B_sign_shuffle":e["raw_surprise"]*=float(rng.choice([-1.,1.]))
        elif name=="C_older_snapshot":
            prior=[s for s in snapshots if s["family"]==e["family"] and s["target"]==e["target"] and s["publication_date"]<e["expectation_publication"]]
            e["raw_surprise"]=e["value"]-max(prior,key=lambda s:s["publication_date"])["value"] if prior else 0.
    # All controls keep the frozen genuine-event past scale and cold-start status.
    for e in out:e["z"]=None if e["past_scale"] is None else e["raw_surprise"]/e["past_scale"]
    return out

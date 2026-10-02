"""## Executive summary (read this first)

Calculate actual first-release surprise with fixed economic direction.
"""
import numpy as np
from .source_schema import WINDOWS
from .event_alignment import last_expectation,known_cutoff,business_age,assert_available
from .normalization import past_scale

def build_events(snapshots,actuals):
    events=[]
    for actual in actuals:
        s=last_expectation(snapshots,actual);e=dict(actual)
        e.update(expectation=s["value"],expectation_publication=s["publication_date"],raw_surprise=actual["value"]-s["value"],source_id=s["source_id"])
        events.append(e)
    return past_scale(events)

def surprise_at(events,origin):
    values=np.zeros(3);ids=[]
    for e in events:
        if e["z"] is None or e["release_date"]>str(known_cutoff(origin).date()):continue
        assert_available(e,origin);activation=e.get("activation_date",e["release_date"])
        if activation>str(known_cutoff(origin).date()):continue
        age=business_age(activation,origin)
        if 1<=age<=21:
            values+=e["z"]*np.array([age<=w for w in WINDOWS]);ids.append(e["event_id"])
    return values,ids

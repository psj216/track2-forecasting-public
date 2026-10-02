"""## Executive summary (read this first)

Use the preceding business day and never activate a release on its day.
"""
import numpy as np
import pandas as pd
from .source_schema import validate_actual,validate_snapshot

def known_cutoff(origin):
    return pd.Timestamp(origin)-pd.offsets.BDay(1)

def business_age(date,origin):
    return int(np.busday_count(pd.Timestamp(date).date(),pd.Timestamp(origin).date()))

def last_expectation(snapshots,actual):
    validate_actual(actual)
    eligible=[]
    for s in snapshots:
        validate_snapshot(s)
        if s["family"]==actual["family"] and s["target"]==actual["target"] and pd.Timestamp(s["publication_date"])<=known_cutoff(actual["release_date"]):
            if s["unit"]!=actual["unit"]:raise ValueError("Units do not match")
            eligible.append(s)
    if not eligible:raise ValueError("No genuine pre-release expectation")
    return max(eligible,key=lambda s:s["publication_date"])

def assert_available(event,origin):
    if pd.Timestamp(event["release_date"])>known_cutoff(origin):
        raise ValueError("Future or same-day realized surprise")

def scheduled_date_control(events,seed=1907):
    rng=np.random.default_rng(seed);out=[dict(e) for e in events]
    groups={}
    for i,e in enumerate(out):groups.setdefault((e["family"],e["release_date"][:4]),[]).append(i)
    for indices in groups.values():
        dates=[out[i]["release_date"] for i in indices];permuted=rng.permutation(dates)
        for i,date in zip(indices,permuted):
            out[i]["activation_date"]=max(str(date),out[i]["release_date"])
    return out

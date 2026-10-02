"""## Executive summary (read this first)

Expose only actual current/next-quarter snapshots during a fixed 21BD news window.
"""
import numpy as np
import pandas as pd
from .source_schema import FAMILIES
from .event_alignment import known_cutoff,business_age

E_NAMES=[f"E_{f}_{n}" for f in FAMILIES for n in ("current","next","slope","age","present")]
V_NAMES=[f"V_{f}_{n}" for f in FAMILIES for n in ("latest_previous","change5","change21","direction","magnitude")]

def expectation_at(snapshots,origin,older=False):
    cutoff=str(known_cutoff(origin).date());values=[];revisions=[];ids=[]
    for family in FAMILIES:
        dates=sorted({s["publication_date"] for s in snapshots if s["family"]==family and s["publication_date"]<=cutoff})
        if not dates:values.extend([0.]*5);revisions.extend([0.]*5);continue
        date=dates[-1];age=business_age(date,origin)
        current=[s for s in snapshots if s["family"]==family and s["publication_date"]==date];current.sort(key=lambda s:s["target"])
        if len(current)!=2:raise ValueError("Missing genuine current/next pair")
        target=current[0]["target"];previous=[s for s in snapshots if s["family"]==family and s["target"]==target and s["publication_date"]<date]
        previous=max(previous,key=lambda s:s["publication_date"]) if previous else None
        if not 1<=age<=21:values.extend([0.]*5);revisions.extend([0.]*5);continue
        cur,nxt=current[0]["value"],current[1]["value"]
        if older:
            # Exactly the immediately previous survey, matched on calendar target.
            if previous is None:values.extend([0.]*5);revisions.extend([0.]*5);continue
            olddate=previous["publication_date"];old=[s for s in snapshots if s["family"]==family and s["publication_date"]==olddate]
            cur=previous["value"];nxt=0. # Missing older next-target forecast is encoded absent.
            oldage=business_age(olddate,origin)
        else:oldage=age
        values.extend([cur,nxt,0. if older else nxt-cur,oldage/21.,1.]);ids.append("SPF_"+current[0]["survey_id"])
        rev=0. if previous is None or older else current[0]["value"]-previous["value"]
        revisions.extend([rev,rev if age<=5 else 0.,rev,np.sign(rev),abs(rev)])
    return np.array(values),np.array(revisions),sorted(set(ids))

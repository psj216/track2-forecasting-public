"""## Executive summary (read this first)
Use only releases published by the preceding business day; expire stale reports.
"""
import numpy as np
import pandas as pd
def cutoff(origin):return (pd.Timestamp(origin)-pd.offsets.BDay(1)).date().isoformat()
def age(date,origin):return int(np.busday_count(str(date)[:10],str(origin)[:10]))
def latest(releases,origin,max_age,older=False):
    limit=cutoff(origin)
    eligible=[r for r in releases if r['release_date']<limit or (r['release_date']==limit and r.get('publication_time_et','00:00')<='16:00')]
    if len(eligible)<(2 if older else 1):return None
    r=eligible[-2 if older else -1]
    if age(r['release_date'],origin)>max_age:return None
    return r

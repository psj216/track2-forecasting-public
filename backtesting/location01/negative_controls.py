"""## Executive summary (read this first)

Permute only eligible training labels. Wrong-date features come from the past.
"""
import hashlib
import numpy as np
import pandas as pd

CONTROLS=('A_label_time','B_wrong_feature_date','C_asset_label')

def permute_labels(rows,y,control,seed=1901):
    rng=np.random.default_rng(seed); out=np.asarray(y).copy()
    grouping=['asset','horizon'] if control=='A_label_time' else ['origin','horizon']
    if control not in ('A_label_time','C_asset_label'):
        return out
    for indices in rows.reset_index(drop=True).groupby(grouping,sort=True).indices.values():
        indices=np.asarray(indices)
        donor=rng.permutation(indices) if control=='A_label_time' else np.roll(indices,1)
        out[indices]=np.asarray(y)[donor]
    return out

def past_feature_donors(rows,seed=1902):
    out=np.full(len(rows),-1,dtype=int)
    dates=pd.to_datetime(rows.origin)
    for key,indices in rows.groupby(['asset','horizon'],sort=True).indices.items():
        indices=np.asarray(indices); years=dates.iloc[indices].dt.year.to_numpy()
        for year in sorted(set(years)):
            current=indices[years==year]; past=indices[years==year-1]
            if len(past)==0:
                continue
            code=int(hashlib.sha256(f'{seed}:{key}:{year}'.encode()).hexdigest()[:8],16)
            past=np.random.default_rng(code).permutation(past)
            out[current]=np.resize(past,len(current))
    valid=out>=0
    if np.any(dates.to_numpy()[out[valid]]>=dates.to_numpy()[valid]):
        raise AssertionError('Wrong-date donor reached future')
    return out

def wrong_date_features(x,rows,schema):
    donors=past_feature_donors(rows); out=np.asarray(x).copy()
    numeric=np.array([c[0]!='M' for c in schema])
    valid=donors>=0
    out[np.ix_(valid,numeric)]=x[np.ix_(donors[valid],numeric)]
    out[np.ix_(~valid,numeric)]=np.nan
    return out,donors

"""## Executive summary (read this first)

Build matched card features from as-of panel prefixes and frozen baseline draws.
No realized card value enters this function.
"""
import numpy as np
import pandas as pd
from qfbench2_track_forecasting.location01.engine import features

def card_features(card,baseline,state,cross,summaries,schema):
    origin=pd.Timestamp(card['origin'])
    if origin not in state['dates']:
        raise ValueError('Card origin absent from business calendar')
    rows=[]
    for hi,h in enumerate(card['horizons']):
        for ai,asset in enumerate(card['assets']):
            kind=state['kinds'][asset]
            prefix=state['raw'].loc[:origin,asset].dropna()
            anchor=float(prefix.iloc[-1]) if kind=='level' else 0.
            sigma=float(state['sigma'].loc[origin,asset])
            if not np.isfinite(sigma):
                raise ValueError('No as-of card sigma')
            values=features(state,cross,summaries,asset,kind,origin,h,
                            baseline[:,hi,ai],anchor,max(sigma,1e-8)*np.sqrt(h))
            rows.append([values[c] for c in schema])
    return np.asarray(rows,float)

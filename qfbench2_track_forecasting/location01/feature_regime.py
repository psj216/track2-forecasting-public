"""## Executive summary (read this first)

Summarize lag-safe peer states without adding macro observations.
"""
import numpy as np

def prepare_regime(state, cross):
    out = {}
    for w in (5,21,63):
        v = cross[w]
        out[f'R_mean_{w}'] = v.mean(axis=1)
        out[f'R_median_{w}'] = v.median(axis=1)
        out[f'R_dispersion_{w}'] = v.std(axis=1, ddof=0)
        out[f'R_abs_{w}'] = v.abs().mean(axis=1)
        out[f'R_positive_{w}'] = (v.gt(0).sum(axis=1) / v.notna().sum(axis=1))
    out['R_vol_ratio'] = state['own']['O_vol_ratio'].mean(axis=1).shift(1)
    return out

def regime(state, summaries, asset, origin):
    out = {k: float(v.loc[origin]) for k,v in summaries.items()}
    out['R_target_vol_percentile'] = float(state['own']['O_vol_percentile'].loc[origin,asset])
    return out

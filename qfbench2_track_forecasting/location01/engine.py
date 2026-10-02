"""## Executive summary (read this first)

Add one predicted center shift; preserve each draw's pairing and dispersion.
"""
import numpy as np
from .feature_metadata import metadata
from .feature_forecast_state import forecast_state
from .feature_own_history import own_history
from .feature_cross_market import cross_market, prepare_cross
from .feature_regime import regime, prepare_regime

def prepare(state):
    cross=prepare_cross(state)
    summaries=prepare_regime(state,cross)
    # Cache arrays for exact, repeated row lookups. This changes computation
    # cost only; it does not change a window, feature or eligible cell.
    state['_own_names']=list(state['own'])
    state['_own_values']=np.stack([f.to_numpy() for f in state['own'].values()],axis=2)
    state['_cross_values']=np.stack([cross[w].to_numpy() for w in cross],axis=2)
    state['_regime_names']=list(summaries)
    state['_regime_values']=np.column_stack([f.to_numpy() for f in summaries.values()])
    return cross,summaries

def features(state,cross,summaries,asset,kind,origin,horizon,draws,anchor,scale):
    out=metadata(asset,kind,horizon,state['assets'])
    out.update(forecast_state(draws,anchor,scale))
    if '_own_values' in state:
        row=state['dates'].get_loc(origin); ai=state['assets'].index(asset)
        out.update(zip(state['_own_names'],state['_own_values'][row,ai]))
        values=state['_cross_values'][row].copy(); values[ai]=0.
        out.update({f'X_{a}_{w}':values[i,j] for j,w in enumerate(cross)
                    for i,a in enumerate(state['assets'])})
        out.update(zip(state['_regime_names'],state['_regime_values'][row]))
        out['R_target_vol_percentile']=out['O_vol_percentile']
    else:
        out.update(own_history(state,asset,origin))
        out.update(cross_market(cross,asset,origin,state['assets']))
        out.update(regime(state,summaries,asset,origin))
    return out

def shift(draws,delta_hat,sd):
    delta=np.asarray(delta_hat,float)
    if not np.isfinite(delta).all():
        raise ValueError('Nonfinite shift')
    return np.asarray(draws,float)+np.clip(delta,-10.,10.)*np.asarray(sd,float)

def geometry_guard(before,after):
    from ..location01r.guard import numerical_geometry_guard
    return numerical_geometry_guard(before,after)

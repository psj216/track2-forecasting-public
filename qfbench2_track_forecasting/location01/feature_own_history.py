"""## Executive summary (read this first)

Compute trailing business-day features once. Every row is as-of safe.
"""
import numpy as np
import pandas as pd
from qfbench2_track_forecasting.thesis01.innovations import innovations
from qfbench2_track_forecasting.thesis01.scaling import scaled

WINDOWS = (1, 5, 21, 63, 126, 252)

def history_state(series, kinds):
    dates = pd.bdate_range(min(s.index.min() for s in series.values()),
                          max(s.index.max() for s in series.values()))
    # Diff the observed level series before calendar reindexing: holidays are
    # absent observations, rather than manufactured zero innovations.
    raw = pd.DataFrame({a: s[~s.index.duplicated(keep='last')].reindex(dates)
                        for a, s in series.items()}, index=dates)
    steps = pd.DataFrame({a: (s.diff() if kinds[a] == 'level' else s).reindex(dates)
                          for a, s in series.items()}, index=dates)
    z, sigma = scaled(steps)
    own = {}
    levels = raw.ffill()
    for w in WINDOWS:
        roll = steps.rolling(w, min_periods=max(1, w//2))
        moves = roll.sum()
        vol = roll.std(ddof=0)
        own[f'O_move_{w}'] = moves / (sigma * np.sqrt(w))
        own[f'O_daily_move_{w}'] = moves / (sigma * w)
        own[f'O_vol_{w}'] = vol / sigma
        own[f'O_trend_{w}'] = (levels - levels.shift(w)) / (sigma * max(w, 1))
        own[f'O_autocorr_{w}'] = steps.rolling(w, min_periods=max(2,w//2)).corr(steps.shift(1)) if w > 1 else raw*0 + np.nan
        distance = (levels - levels.rolling(w, min_periods=max(1,w//2)).mean()) / sigma
        drawdown = (levels - levels.rolling(w, min_periods=max(1,w//2)).max()) / (sigma * np.sqrt(w))
        for a in series:
            if kinds[a] != 'level':
                distance[a] = np.nan
                drawdown[a] = np.nan
                own[f'O_trend_{w}'][a] = moves[a] / (sigma[a] * max(w,1))
        own[f'O_level_distance_{w}'] = distance
        own[f'O_drawdown_{w}'] = drawdown
    short = steps.rolling(21, min_periods=10).std()
    long = steps.rolling(252, min_periods=200).std()
    own['O_vol_ratio'] = short / long.clip(lower=1e-8)
    own['O_vol_percentile'] = short.rolling(252, min_periods=200).rank(pct=True)
    return {'dates': dates, 'raw': raw, 'steps': steps, 'z': z, 'sigma': sigma,
            'own': own, 'kinds': kinds, 'assets': sorted(series)}

def own_history(state, asset, origin):
    return {name: float(frame.loc[origin, asset]) for name, frame in state['own'].items()}

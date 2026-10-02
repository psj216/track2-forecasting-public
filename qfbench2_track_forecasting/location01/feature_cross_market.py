"""## Executive summary (read this first)

Cross-market innovations stop at t-1. The target's entries are always zero.
"""
import numpy as np

WINDOWS = (1, 5, 21, 63)

def prepare_cross(state):
    return {w: state['z'].rolling(w, min_periods=max(1,w//2)).sum().shift(1) / np.sqrt(w)
            for w in WINDOWS}

def cross_market(cross, asset, origin, assets):
    return {f'X_{a}_{w}': (0.0 if a == asset else float(cross[w].loc[origin, a]))
            for w in WINDOWS for a in assets}

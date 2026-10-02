"""## Executive summary (read this first)

Describe the actual baseline draws in ex-ante innovation units.
"""
import numpy as np
from .oracle_target import EPSILON

def forecast_state(draws, anchor, scale):
    x = np.asarray(draws, float)
    scale = max(float(scale), EPSILON)
    q = np.quantile(x, [.05, .10, .25, .50, .75, .90, .95])
    sd = max(float(np.std(x)), EPSILON)
    lo, hi = q[3] - q[0], q[-1] - q[3]
    out = {f'F_q{v:02d}': float((z - anchor) / scale)
           for v, z in zip((5, 10, 25, 50, 75, 90, 95), q)}
    out.update(F_mean=(float(x.mean()) - anchor) / scale,
               F_median=(q[3] - anchor) / scale, F_sd=sd / scale,
               F_iqr=(q[4] - q[2]) / scale,
               F_skew=(q[4] + q[2] - 2*q[3]) / max(q[4] - q[2], EPSILON),
               F_tail_asymmetry=(hi - lo) / sd,
               F_iqr_sd=(q[4] - q[2]) / sd,
               F_upper_lower_width=hi / max(lo, EPSILON),
               F_outer_inner_width=(hi + lo) / max(q[4] - q[2], EPSILON))
    return out

"""## Executive summary (read this first)
Normalize with original same-report open interest and strictly earlier released values.
"""
import numpy as np
def shares(long,short,open_interest):
    if not np.isfinite([long,short,open_interest]).all() or min(long,short)<0 or open_interest<=0:raise ValueError('Invalid original same-report quantity')
    return (long-short)/open_interest,(long+short)/open_interest
def past_z(values,index,minimum=52):
    prior=np.asarray(values[:index],float)
    if len(prior)<minimum:return None
    sd=prior.std(ddof=1)
    return 0. if sd==0 else float((values[index]-prior.mean())/sd)

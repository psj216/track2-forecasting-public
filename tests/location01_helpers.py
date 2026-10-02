"""## Executive summary (read this first)

Supply synthetic dated panels, unrelated to any realized benchmark outcome.
"""
import numpy as np
import pandas as pd

def panel():
    dates=pd.bdate_range('2000-01-03',periods=900)
    rng=np.random.default_rng(19)
    series={'EUR':pd.Series(10+np.cumsum(rng.normal(0,.1,900)),index=dates),
            'UST_2Y':pd.Series(2+np.cumsum(rng.normal(0,.01,900)),index=dates),
            'MKT':pd.Series(rng.normal(0,.1,900),index=dates)}
    return series,{'EUR':'level','UST_2Y':'level','MKT':'log_return'},dates[600]

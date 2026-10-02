"""## Executive summary (read this first)
Keep future truth exclusively in residual training/evaluation targets.
"""
import numpy as np
def residual(draws,truth,epsilon=1e-12):
 x=np.asarray(draws,float);y=np.asarray(truth,float)
 return (y-np.median(x,axis=0))/np.maximum(np.std(x,axis=0,ddof=0),epsilon)

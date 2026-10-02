"""## Executive summary (read this first)
Reuse the existing capped pure translation and geometry guard for B_TEXT draws.
"""
import numpy as np
from ..location01.engine import shift,geometry_guard
def apply(draws,prediction):
 x=np.asarray(draws,float);p=np.asarray(prediction,float).reshape(x.shape[1:]);out=shift(x,p,np.std(x,axis=0,ddof=0))
 if not geometry_guard(x,out):raise ValueError('Context transformation changed draw geometry')
 return out

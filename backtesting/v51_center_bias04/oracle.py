"""Executive summary: future-informed location optimizer isolated from predictive bias."""
import numpy as np
def minimum_location(residual,sd,scale,n_draws):
 # Optimize weighted absolute-distance location only. Location leaves ensemble spread invariant.
 # Scores are always calculated separately with imported qfbench2-common, never here.
 lower=float(np.nanmin(residual));upper=float(np.nanmax(residual));w=np.asarray(sd)/np.asarray(scale)/np.asarray(n_draws);mass=float(np.dot(w,n_draws));steps=0
 for steps in range(80):
  mid=(lower+upper)/2;cdf=float(np.dot(np.sum(residual<=mid,axis=0),w))
  if cdf<mass/2:lower=mid
  else:upper=mid
  if upper-lower<=1e-10*max(1.,abs(mid)):break
 return (lower+upper)/2,{'iterations':steps+1,'width':upper-lower,'relative_tolerance':1e-10,'loss_evaluation':'Imported common scorer outside optimizer','predictive_use':False}

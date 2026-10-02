"""## Executive summary (read this first)
Resample whole exposed cards 5000 times; retain six cards per family in stratified sensitivity.
"""
import numpy as np
from qfbench2_track_forecasting.ceiling01.scorer_adapter import aggregate
REPLICATES=5000
SEED=1903
def bootstrap(values,components,single,families,stratified=False):
 values=np.asarray(values,float);components=np.asarray(components,float);single=np.asarray(single,bool);families=np.asarray(families);rng=np.random.default_rng(SEED);n=len(values);groups=[np.flatnonzero(families==f)for f in sorted(set(families))];ix=np.column_stack([rng.choice(g,(REPLICATES,len(g)),replace=True)for g in groups])if stratified else rng.integers(n,size=(REPLICATES,n))
 def geo(a,mask=None):
  z=np.log(np.maximum(a[ix],1e-12))
  if mask is None:return np.exp(z.mean(axis=1))
  m=mask[ix];count=m.sum(axis=1);valid=count>0;return np.exp((z*m).sum(axis=1)[valid]/count[valid])
 out={}
 for name,a,mask in [('composite',values,None),('marginal',components,None),('single',values,single),('multi',values,~single)]:
  samples=geo(a,mask);out[name+'_95_interval']=np.quantile(samples,[.025,.975]).tolist() if len(samples) else None
 out.update(replicates=REPLICATES,seed=SEED,blocks=n,method='Family-stratified six-card blocks per family'if stratified else'Whole-card blocks; all cells stay together',interpretation='Exposed sample resampling sensitivity; not formal generalization confidence interval')
 return out
def paired(candidate,control,families,stratified=False):
 values=np.asarray(candidate)/np.asarray(control);return bootstrap(values,values,np.zeros(len(values),bool),families,stratified)['composite_95_interval']

"""Executive summary: five frozen source inputs; separate asset/horizon Ridge, alpha one.

Weights give each source release total mass one. Model outputs translate frozen
V5.1 draws uniformly; no distribution scale, shape or rank parameter is fit.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr,spearmanr
from .source_dataset import FEATURES
ASSETS=('UST_2Y','UST_5Y','UST_7Y','UST_10Y','UST_20Y','UST_30Y')
HORIZONS=(5,21,63,126,189)
YEARS=tuple(range(2017,2025));MIN_RELEASES=12;SEED=2026100303
MODELS={'SLOOS_FULL5_RELEASE_BALANCED':(0,1,2,3,4),'LEVELS_ONLY':(0,1,4),'CHANGES_ONLY':(2,3,4),'STANDARDS_ONLY':(0,2,4),'DEMAND_ONLY':(1,3,4),'SLOOS_FULL5_UNWEIGHTED':(0,1,2,3,4)}

def release_weights(releases):
 keys,counts=np.unique(np.asarray(releases),return_counts=True);d=dict(zip(keys,counts))
 return np.array([1./d[r] for r in releases])

def train_mask(rows,year,test_cutoff,test_releases=None):
 origin=pd.to_datetime(rows.origin);maturity=pd.to_datetime(rows.target_end)
 c=pd.Timestamp(test_cutoff).tz_localize(None).normalize()
 unavailable=origin+pd.offsets.BDay(int(rows.horizon.iloc[0]))
 test_releases=set(rows.loc[origin.dt.year==year,'release_id']) if test_releases is None else set(test_releases)
 return ((origin.dt.year<year)&(origin.dt.year>=2013)&(maturity<c)&(unavailable<c)&~rows.release_id.isin(test_releases)).to_numpy()

def fit_ridge(x,y,releases,columns,balanced=True):
 weights=release_weights(releases) if balanced else np.ones(len(releases))
 scaler=StandardScaler();xx=scaler.fit_transform(np.asarray(x)[:,columns],sample_weight=weights)
 model=Ridge(alpha=1.0,fit_intercept=True,solver='svd');model.fit(xx,np.asarray(y),sample_weight=weights)
 return scaler,model

def predict(fit,x,columns):return fit[1].predict(fit[0].transform(np.asarray(x)[:,columns]))
def shift(draws,delta,sd):return np.asarray(draws)+np.asarray(delta)*np.asarray(sd)

def batch_ridge(x,y,weights,xt):
 """Solve identical weighted standardized Ridge for independent null replicates.

 x: replicate x train row x 5; xt: replicate x test row x 5.
 Verified against fixed sklearn SVD Ridge on synthetic examples before PRE.
 """
 x=np.asarray(x,float);xt=np.asarray(xt,float);w=np.asarray(weights,float);w=w/w.sum();n_eff=np.asarray(weights).sum()
 mu=np.einsum('bnp,n->bp',x,w);center=x-mu[:,None,:];var=np.einsum('bnp,bnp,n->bp',center,center,w)
 scale=np.sqrt(var);scale[scale<=np.finfo(float).eps]=1.
 z=center/scale[:,None,:];ym=np.sum(w*y);yc=y-ym
 a=np.einsum('bni,bnj,n->bij',z,z,w)*n_eff+np.eye(x.shape[-1])[None]
 b=np.einsum('bnp,n,n->bp',z,w,yc)*n_eff
 coef=np.linalg.solve(a,b[...,None])[...,0]
 return np.einsum('bnp,bp->bn',(xt-mu[:,None,:])/scale[:,None,:],coef)+ym

def metrics(y,p,base,loss,oracle):
 y=np.asarray(y);p=np.asarray(p);ratio=float(sum(loss)/sum(base));orr=float(sum(oracle)/sum(base));mse=float(np.mean((y-p)**2))
 meaningful=len(y)>2 and np.ptp(y)>0 and np.ptp(p)>0
 return dict(cells=len(y),crps_ratio=ratio,oracle_capture=(1-ratio)/(1-orr),delta_mse=mse,r2=1-mse/np.var(y) if np.var(y)>0 else None,
 pearson=float(pearsonr(y,p).statistic) if meaningful else None,spearman=float(spearmanr(y,p).statistic) if meaningful else None,
 sign_accuracy=float(np.mean(np.sign(y)==np.sign(p))),calibration_slope=float(np.cov(p,y,ddof=0)[0,1]/np.var(p)) if np.var(p)>0 else None,
 mean_abs_predicted_delta=float(np.mean(abs(p))),median_abs_predicted_delta=float(np.median(abs(p))),actual_mean_abs_delta=float(np.mean(abs(y))))

def verdict(primary,annual,controls,bootstrap,concentrated):
 ratio=primary['crps_ratio'];capture=primary['oracle_capture'];n=len(annual);improve=sum(s['crps_ratio']<1 for s in annual)
 inferior=all(s.get('median_ratio',s.get('crps_ratio',-1))>ratio for s in controls.values() if isinstance(s,dict) and ('median_ratio' in s or 'crps_ratio' in s))
 clear=all(s.get('fraction_at_least_as_good',1)<.05 for s in controls.values() if 'fraction_at_least_as_good' in s)
 support=bootstrap['crps_ratio_95ci'][1]<1
 if ratio>=1.02 or capture<=0 or not inferior:return 'NO'
 if ratio<=.9 and capture>=.2 and improve/n>=.75 and clear and support and not concentrated:return 'STRONG_YES'
 if ratio<=.95 and capture>=.1 and improve/n>=.6 and inferior and not concentrated:return 'YES'
 if ratio<=.98 and capture>.05 and improve>n-improve and inferior and not concentrated:return 'WEAK_YES'
 return 'INCONCLUSIVE'

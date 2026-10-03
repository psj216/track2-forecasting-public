"""Executive summary: fixed, release-balanced Ridge and pure location shifts.

The five primary inputs are immutable. Chronological maturity and the parent
maximum-horizon purge are applied before train-only preprocessing.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr, spearmanr
from .source_dataset import FEATURES

HORIZONS=(5,21,63,126,189)
MODELS={'ECB_RIDGE_FULL5':tuple(range(5)), 'LEVELS_ONLY':(0,1,4),
        'REVISIONS_ONLY':(2,3,4), 'HICP_ONLY':(0,2,4), 'GDP_ONLY':(1,3,4)}
SEED=20261003


def train_mask(rows, year, cutoff):
    origins=pd.to_datetime(rows.origin)
    maturity=pd.to_datetime(rows.target_end)
    maximum=origins+pd.offsets.BDay(189)
    cutoff_date=pd.Timestamp(cutoff).tz_localize(None).normalize()
    test_release=set(rows.loc[origins.dt.year==year,'round_id'])
    return ((origins.dt.year<year)&(origins.dt.year>=2015)&(maturity<cutoff_date)&
            (maximum<cutoff_date)&(~rows.round_id.isin(test_release))).to_numpy()


def release_weights(releases):
    releases=np.asarray(releases)
    keys,counts=np.unique(releases,return_counts=True)
    lookup=dict(zip(keys,counts))
    return np.asarray([1./lookup[r] for r in releases])


def fit_ridge(x, y, releases, columns):
    weights=release_weights(releases)
    scaler=StandardScaler()
    xx=scaler.fit_transform(np.asarray(x)[:,columns],sample_weight=weights)
    model=Ridge(alpha=1.0,fit_intercept=True,solver='svd')
    model.fit(xx,np.asarray(y),sample_weight=weights)
    return scaler,model


def predict(fit, x, columns):
    scaler,model=fit
    return model.predict(scaler.transform(np.asarray(x)[:,columns]))


def shift(draws,delta,sd):
    return np.asarray(draws)+np.asarray(delta)*np.asarray(sd)


def metrics(y,p,base,loss,oracle):
    y=np.asarray(y);p=np.asarray(p);n=len(y)
    ratio=float(np.sum(loss)/np.sum(base))
    oracle_ratio=float(np.sum(oracle)/np.sum(base))
    pearson=float(pearsonr(y,p).statistic) if n>2 and np.ptp(p)>0 and np.ptp(y)>0 else None
    spearman=float(spearmanr(y,p).statistic) if pearson is not None else None
    slope=float(np.cov(p,y,ddof=0)[0,1]/np.var(p)) if np.var(p)>0 else None
    mse=float(np.mean((y-p)**2))
    return dict(cells=n,crps_ratio=ratio,oracle_capture=(1.-ratio)/(1.-oracle_ratio),
          delta_mse=mse,r2=1.-mse/float(np.var(y)) if np.var(y)>0 else None,
          pearson=pearson,spearman=spearman,sign_accuracy=float(np.mean(np.sign(y)==np.sign(p))),
          calibration_slope=slope,mean_abs_predicted_delta=float(np.mean(np.abs(p))),
          actual_mean_abs_delta=float(np.mean(np.abs(y))),mean_predicted_delta=float(np.mean(p)))


def bootstrap(rows,base,loss,oracle,y,p,group,n=5000):
    keys=np.unique(np.asarray(rows[group]).astype(str))
    groups=[np.flatnonzero(np.asarray(rows[group]).astype(str)==key) for key in keys]
    sums=np.array([[base[ii].sum(),loss[ii].sum(),oracle[ii].sum()] for ii in groups])
    rng=np.random.default_rng(SEED+(1 if group=='round_id' else 2))
    out=[];corr=[]
    for replicate in range(n):
        chosen=rng.integers(0,len(keys),len(keys));b,c,o=sums[chosen].sum(axis=0)
        out.append([c/b,c/b-1,(b-c)/(b-o)])
        ii=np.concatenate([groups[k] for k in chosen]); yy=y[ii];pp=p[ii]
        if np.ptp(yy)>0 and np.ptp(pp)>0:
            corr.append([pearsonr(yy,pp).statistic,spearmanr(yy,pp).statistic])
    ci=np.quantile(out,[.025,.975],axis=0)
    cc=np.quantile(corr,[.025,.975],axis=0) if corr else None
    return dict(block=group,blocks=len(keys),replicates=n,crps_ratio_95ci=ci[:,0].tolist(),
                delta_vs_v51_95ci=ci[:,1].tolist(),oracle_capture_95ci=ci[:,2].tolist(),
                pearson_95ci=cc[:,0].tolist() if cc is not None else None,
                spearman_95ci=cc[:,1].tolist() if cc is not None else None)


def verdict(primary,annual,controls,boot,concentration):
    ratio=primary['crps_ratio'];capture=primary['oracle_capture']
    improving=sum(v['crps_ratio']<1 for v in annual)
    controls_inferior=all(c.get('median_ratio',c.get('crps_ratio',0))>ratio for c in controls.values())
    clear=all(c.get('fraction_at_least_as_good',1)<.05 for c in controls.values() if 'fraction_at_least_as_good' in c)
    evidence=boot['crps_ratio_95ci'][1]<1
    broad=not concentration['dominated_by_one_release_or_year']
    if ratio>=1.02 or capture<=0 or not controls_inferior: return 'NO'
    if ratio<=.90 and capture>=.20 and improving>=4 and clear and evidence and broad: return 'STRONG_YES'
    if ratio<=.95 and capture>=.10 and improving>=3 and controls_inferior and broad: return 'YES'
    if ratio<=.98 and capture>.05 and improving>len(annual)/2 and controls_inferior: return 'WEAK_YES'
    return 'INCONCLUSIVE'

"""## Executive summary (read this first)

Fit zero-safe Ridge with chronological delta-MSE selection; use one fixed tree diagnostic.
"""
import numpy as np
from scipy.linalg import solve
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import HistGradientBoostingRegressor
from ..location01.model import ALPHAS,FOLDS,purged_mask,inner_splits,HGB_PARAMS

def columns(schema,model):
    return [i for i,s in enumerate(schema) if s["stage"]<=model]

class ExpectationModel:
    def __init__(self,model,nonlinear=False):self.model=model;self.nonlinear=nonlinear
    def fit(self,x,y,schema,alpha=100.):
        self.idx=columns(schema,self.model);self.alpha=alpha
        if not self.idx:self.estimator=None;return self
        xx=np.asarray(x[:,self.idx],float);active=np.any(xx!=0,axis=1)
        if not active.any():self.estimator=None;return self
        self.scaler=StandardScaler(with_mean=False).fit(xx[active]);xx=self.scaler.transform(xx[active])
        self.estimator=HistGradientBoostingRegressor(**HGB_PARAMS) if self.nonlinear else Ridge(alpha=alpha,fit_intercept=False,solver="cholesky")
        self.estimator.fit(xx,np.asarray(y)[active]);return self
    def predict_raw(self,x):
        out=np.zeros(len(x))
        if self.estimator is None:return out
        xx=np.asarray(x[:,self.idx],float);active=np.any(xx!=0,axis=1)
        if active.any():out[active]=self.estimator.predict(self.scaler.transform(xx[active]))
        if not np.isfinite(out).all():raise ValueError("Nonfinite shift")
        return out
    def predict(self,x):return np.clip(self.predict_raw(x),-10.,10.)

def choose_alpha(x,y,schema,rows,model,cutoff_year):
    idx=columns(schema,model);splits=inner_splits(rows,cutoff_year);totals=np.zeros(len(ALPHAS));count=0
    audit=[]
    for train,val in splits:
        xt=np.asarray(x[train][:,idx],float);xv=np.asarray(x[val][:,idx],float);a=np.any(xt!=0,axis=1);v=np.any(xv!=0,axis=1)
        if not a.any() or not v.any():continue
        scaler=StandardScaler(with_mean=False).fit(xt[a]);xt=scaler.transform(xt[a]);xv=scaler.transform(xv[v]);yt=np.asarray(y)[train][a];yv=np.asarray(y)[val][v]
        gram=xt.T@xt;rhs=xt.T@yt
        for j,alpha in enumerate(ALPHAS):
            regular=gram.copy();regular.flat[::len(regular)+1]+=alpha
            coef=solve(regular,rhs,assume_a="pos");totals[j]+=float(np.sum((yv-xv@coef)**2))
        count+=len(yv);audit.append(dict(train_active=int(a.sum()),validation_active=int(v.sum()),train_max_origin=str(rows.loc[train,"origin"].max()),validation_min_origin=str(rows.loc[val,"origin"].min())))
    if not count:return 100.,dict(status="COLD_START_ALPHA_100",inner_folds=0)
    losses=totals/count;best=int(np.argmin(losses))
    return ALPHAS[best],dict(grid=list(ALPHAS),delta_mse=losses.tolist(),inner_folds=len(audit),splits=audit)

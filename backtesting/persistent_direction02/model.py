"""Executive summary: one fixed pooled directional logistic, no magnitude fitting."""
import numpy as np,pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from .source import AMPLITUDE
def fit(x,y):
 x=np.asarray(x,float);y=np.asarray(y,int)
 if not np.isfinite(x).all() or set(np.unique(y))!={0,1}:raise ValueError('Both classes and finite train-only features required')
 scaler=StandardScaler().fit(x)
 model=LogisticRegression(C=1.,penalty='l2',fit_intercept=True,class_weight=None,solver='lbfgs',max_iter=2000,tol=1e-8,random_state=31802)
 model.fit(scaler.transform(x),y)
 return scaler,model
def probability(fit,x):return fit[1].predict_proba(fit[0].transform(np.asarray(x,float)))[:,1]
def direction(p):return np.sign(np.asarray(p,float)-.5)
def shift(sd,d):return AMPLITUDE*np.asarray(sd,float)*np.asarray(d,float)
def translate(draws,shifts):return np.asarray(draws,float)+np.asarray(shifts,float)
def training_mask(rows,year,first_cutoff,test_releases=()):
 d=pd.Timestamp(first_cutoff).tz_localize(None).normalize()
 return ((pd.to_datetime(rows.origin).dt.year>=2016)&(pd.to_datetime(rows.origin).dt.year<year)&(pd.to_datetime(rows.target_end)<d)&((pd.to_datetime(rows.origin)+rows.horizon.map(lambda h:pd.offsets.BDay(int(h))))<d)&~rows.release_id.isin(test_releases)).to_numpy()

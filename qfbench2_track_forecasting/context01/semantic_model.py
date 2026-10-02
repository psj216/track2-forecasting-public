"""## Executive summary (read this first)
Use card-blocked delta-MSE alpha selection with training-only scaling and no intercept.
"""
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from ..location01.model import ALPHAS
def card_splits(ids):
 ids=np.asarray(ids);return [(ids!=c,ids==c)for c in sorted(set(ids))]
def fit_predict(x,y,test,alpha):
 scaler=StandardScaler(with_mean=False).fit(x);est=Ridge(alpha=alpha,fit_intercept=False,solver='cholesky').fit(scaler.transform(x),y)
 return est.predict(scaler.transform(test)),(scaler,est)
def select_alpha(x,y,ids):
 totals=np.zeros(len(ALPHAS));count=0
 for train,val in card_splits(ids):
  if not train.any():continue
  scaler=StandardScaler(with_mean=False).fit(x[train]);xt=scaler.transform(x[train]);xv=scaler.transform(x[val])
  for j,a in enumerate(ALPHAS):
   est=Ridge(alpha=a,fit_intercept=False,solver='cholesky').fit(xt,y[train]);totals[j]+=float(np.mean((y[val]-est.predict(xv))**2))
  count+=1
 if not count:return 100.,dict(status='COLD_START_ALPHA_100',inner_cards=0)
 losses=totals/count;return ALPHAS[int(np.argmin(losses))],dict(grid=list(ALPHAS),card_average_delta_mse=losses.tolist(),inner_cards=count)
def fit_fold(x,y,ids,train,test):
 ids=np.asarray(ids)
 if set(ids[train])&set(ids[test]):raise ValueError('Same card in training and held-out fold')
 alpha,cv=select_alpha(x[train],y[train],ids[train]);raw,fit=fit_predict(x[train],y[train],x[test],alpha)
 return raw,fit,alpha,cv

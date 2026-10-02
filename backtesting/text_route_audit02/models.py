"""## Executive summary (read this first)
Fit fixed L2 logistic C1 or gain Ridge alpha1 with training-only scaling and whole-card folds.
"""
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression,Ridge
MODELS={'S0_LOG':('S0','logistic'),'T0_LOG':('T0','logistic'),'ST0_LOG':('ST0','logistic'),'STF0_LOG':('STF0','logistic'),'LENGTH_LOG':('LENGTH','logistic'),'ST_NO_FAMILY_LOG':('ST_NO_FAMILY','logistic'),'S0_RIDGE':('S0','ridge'),'T0_RIDGE':('T0','ridge'),'ST0_RIDGE':('ST0','ridge')}
def predict(x,y,g,train,test,kind='logistic'):
 train=np.asarray(train,int);test=np.asarray(test,int);assert not(set(train)&set(test));scaler=StandardScaler().fit(x[train]);a=scaler.transform(x[train]);b=scaler.transform(x[test])
 if kind=='logistic':
  if len(set(y[train]))<2:return np.repeat(float(y[train][0]),len(test)),None,(scaler,None)
  fit=LogisticRegression(C=1.,solver='lbfgs',class_weight=None,max_iter=1000,tol=1e-8,random_state=2202).fit(a,y[train]);p=fit.predict_proba(b)[:,1];gain=None
 else:
  fit=Ridge(alpha=1.,fit_intercept=True,solver='cholesky').fit(a,g[train]);gain=fit.predict(b);p=(gain<0).astype(float)
 return p,gain,(scaler,fit)
def route(p,kind='logistic'):return np.asarray(p)>=.5

def folds(cards,mode):
 n=len(cards);allids=np.arange(n)
 if mode=='loco':return [(str(i),allids[allids!=i],np.array([i]))for i in allids]
 return [('T2-F'+str(f),np.array([i for i,c in enumerate(cards)if c['family']!='T2-F'+str(f)]),np.array([i for i,c in enumerate(cards)if c['family']=='T2-F'+str(f)]))for f in range(1,5)]

def training_shuffle(y,g,train,rng):
 perm=rng.permutation(train);yy=y.copy();gg=g.copy();yy[train]=y[perm];gg[train]=g[perm];return yy,gg

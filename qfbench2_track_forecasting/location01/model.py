"""## Executive summary (read this first)

Ridge alpha is selected with purged chronological inner delta-MSE only.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

ALPHAS = (.01, .1, 1., 10., 100.)
CHANNELS = ('', 'M', 'MF', 'MFO', 'MFOX', 'MFOXR')
FOLDS = ((2009,2010,2013),(2013,2014,2017),(2017,2018,2020),(2020,2021,2024))
HGB_PARAMS = dict(max_depth=3, learning_rate=.05, max_iter=200,
                  l2_regularization=1., random_state=19, early_stopping=False,
                  categorical_features=None)

def columns(schema, model):
    return [i for i,c in enumerate(schema) if c[0] in CHANNELS[model]]

def purged_mask(rows, boundary):
    boundary = pd.Timestamp(boundary)
    # One explicit maximum-horizon embargo, not a second 189-day embargo.
    return ((pd.to_datetime(rows.origin) < boundary - pd.offsets.BDay(189)) &
            (pd.to_datetime(rows.target_end) < boundary)).to_numpy()

def inner_splits(rows, cutoff_year):
    dates = pd.to_datetime(rows.origin)
    ends = pd.to_datetime(rows.target_end)
    out=[]
    for start in (cutoff_year-3, cutoff_year-1):
        boundary = pd.Timestamp(f'{start}-01-01')
        train = purged_mask(rows, boundary)
        validation = ((dates >= boundary) & (dates < pd.Timestamp(f'{start+2}-01-01')) &
                      (ends < pd.Timestamp(f'{cutoff_year+1}-01-01'))).to_numpy()
        if train.sum() >= 100 and validation.sum() >= 100:
            out.append((train,validation))
    return out

class LocationModel:
    def __init__(self, model, nonlinear=False):
        self.model = model
        self.nonlinear = nonlinear

    def _prepare_fit(self, x, schema):
        self.idx = columns(schema,self.model)
        self.numeric = np.array([schema[i][0] != 'M' for i in self.idx])
        xx=np.asarray(x[:,self.idx],float).copy()
        # Training-only median imputation; wholly absent columns have zero.
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning)
            self.fill=np.nanmedian(np.where(np.isfinite(xx),xx,np.nan),axis=0)
        self.fill=np.nan_to_num(self.fill)
        xx=np.where(np.isfinite(xx),xx,self.fill)
        self.scaler=StandardScaler().fit(xx[:,self.numeric]) if self.numeric.any() else None
        if self.scaler is not None:
            xx[:,self.numeric]=self.scaler.transform(xx[:,self.numeric])
        return xx

    def fit(self,x,y,schema,alpha=1.):
        self.alpha=float(alpha)
        if self.model==0:
            return self
        xx=self._prepare_fit(x,schema)
        self.estimator=(HistGradientBoostingRegressor(**HGB_PARAMS) if self.nonlinear
                        else Ridge(alpha=alpha,solver='cholesky'))
        self.estimator.fit(xx,y)
        return self

    def predict_raw(self,x):
        if self.model==0:
            return np.zeros(len(x))
        xx=np.asarray(x[:,self.idx],float).copy()
        xx=np.where(np.isfinite(xx),xx,self.fill)
        if self.scaler is not None:
            xx[:,self.numeric]=self.scaler.transform(xx[:,self.numeric])
        return self.estimator.predict(xx)

    def predict(self,x):
        raw=self.predict_raw(x)
        if not np.isfinite(raw).all():
            raise ValueError('Nonfinite prediction')
        return np.clip(raw,-10.,10.), int(np.sum(np.abs(raw)>10))

def choose_alpha(x,y,schema,rows,model,cutoff_year,label_transform=None):
    splits=inner_splits(rows,cutoff_year)
    if not splits:
        # Fixed cold-start fallback; never inspect an outer or card outcome.
        return 100., {'status':'COLD_START_ALPHA_100','inner_folds':0}
    totals=np.zeros(len(ALPHAS));count=0
    for train,val in splits:
        fitted=LocationModel(model)
        xx=fitted._prepare_fit(x[train],schema)
        yy=(y[train] if label_transform is None else
            label_transform(rows.loc[train].reset_index(drop=True),y[train]))
        # Preprocessing is identical across alpha values and fitted once per
        # inner training split. Permutation donors cannot cross this boundary.
        for i,alpha in enumerate(ALPHAS):
            fitted.estimator=Ridge(alpha=alpha,solver='cholesky').fit(xx,yy)
            prediction=fitted.predict_raw(x[val])
            totals[i]+=float(np.sum((y[val]-prediction)**2))
        count+=int(val.sum())
    losses=(totals/count).tolist()
    best=int(np.argmin(losses))
    return ALPHAS[best], {'grid':list(ALPHAS),'delta_mse':losses,'inner_folds':len(splits)}

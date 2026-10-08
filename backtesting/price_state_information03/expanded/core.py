"""Executive summary: fixed price features, historical folds and target-blind nulls."""
from pathlib import Path
import json, os, hashlib, subprocess, warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from backtesting.new_information_search02.analyze import price_states
from backtesting.new_information_search02.core import origin_cutoff, available_eod
from qfbench2_track_forecasting.location01.model import FOLDS, purged_mask

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parents[1]/'results'/'expanded_20261008'
PRIOR='0f5c938eeb4054518b0bde81e4de1503890fd684'
PARENT='929ca23e0a57a0529cc64d8a14d5a78b791892e6'
MAIN='e1b5cf3b3a87966e902332ef3cc5c0ed2dbffee8'
SEED=31803; AMPLITUDE=.05; NULL_REPS=2000; RANDOM_REPS=5000; BOOTSTRAP_REPS=5000
NAMES=tuple(f'DGS{k}_{s}' for k in (2,5,10) for s in ('level','5BD','21BD','63BD'))+('2s5s','2s10s')
HORIZONS=(5,21,63,126,189)
CONFIDENCE_EDGES=(0,.05,.10,.20,.50)

def private():return Path(os.environ['PRICE03_EXPANDED_PRIVATE'])
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def clean(v):
 if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
 if isinstance(v,(list,tuple)):return [clean(x) for x in v]
 if isinstance(v,np.ndarray):return clean(v.tolist())
 if isinstance(v,(np.bool_,bool)):return bool(v)
 if isinstance(v,(np.integer,int)):return int(v)
 if isinstance(v,(np.floating,float)):return float(v) if np.isfinite(v) else None
 if isinstance(v,(pd.Timestamp,Path)):return str(v)
 return v
def save(path,v):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(clean(v),indent=2,allow_nan=False)+'\n');temp.replace(path)
def atomic_npz(path,**arrays):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp')
 with tmp.open('wb') as stream:np.savez_compressed(stream,**arrays)
 tmp.replace(path)
def status(stage,artifact='',**extra):
 path=OUT.parent.parent/'expanded_STATUS.json';v=json.loads(path.read_text()) if path.exists() else {}
 done=v.get('completed_stages',[])
 if stage not in done:done.append(stage)
 v.update(executive_summary='Separate expanded protocol; all original study files protected.',branch='track2/price-state-information-audit-03',HEAD_SHA=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),current_stage=stage,completed_stages=done,last_successful_artifact=str(artifact),last_update=pd.Timestamp.now(tz='UTC').isoformat(),**extra);save(path,v)
def verify_pre():
 p=private();r=json.loads((p/'expanded_pre_receipt.json').read_text())
 assert r['remote_verified'] and r['PRE_RESULT_PRICE_STATE_INFO03_EXPANDED_SHA']
 for path,sha in r['frozen_hashes'].items():assert digest(ROOT/path)==sha,path
 for path,sha in r['private_input_hashes'].items():assert digest(p/path)==sha,path
 assert subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip()==MAIN
 return r
def source_frame():
 f,_=price_states(private()/'source');assert tuple(f.columns)==NAMES
 assert f.index.is_monotonic_increasing and f.index.is_unique
 return f
def asof_prices(origins,frame):
 availability=pd.DatetimeIndex([available_eod(d+pd.offsets.BDay(1)) for d in frame.index])
 cutoffs=pd.DatetimeIndex([origin_cutoff(d) for d in origins]);j=availability.searchsorted(cutoffs,side='right')-1
 x=np.full((len(origins),14),np.nan);dates=np.full(len(origins),np.datetime64('NaT'),dtype='datetime64[ns]')
 valid=j>=0;x[valid]=frame.iloc[j[valid]].to_numpy(float);dates[valid]=frame.index[j[valid]].to_numpy()
 assert (availability[j[valid]]<=cutoffs[valid]).all()
 return x,dates,j
def structure(rows,assets):
 return np.column_stack([rows.asset.eq(a).to_numpy(float) for a in assets[1:]]+[np.log(rows.horizon.to_numpy(float))])
def numeric_fit(x,y):
 x=np.asarray(x,float);y=np.asarray(y,int)
 assert len(x)>0 and np.isfinite(x).all()
 sc=StandardScaler().fit(x)
 if len(np.unique(y))==1:return sc,None,float(y[0])
 model=LogisticRegression(C=1.,penalty='l2',fit_intercept=True,class_weight=None,solver='lbfgs',max_iter=2000,tol=1e-8,random_state=SEED)
 with warnings.catch_warnings():
  warnings.simplefilter('ignore',FutureWarning);model.fit(sc.transform(x),y)
 assert model.n_iter_.max()<2000,'Convergence failure is not silently admitted'
 return sc,model,None
def predict(f,x):return np.full(len(x),f[2]) if f[1] is None else f[1].predict_proba(f[0].transform(x))[:,1]
def direction(p):return np.sign(np.asarray(p)-.5).astype(int)
def weights(groups):
 _,ii,n=np.unique(np.asarray(groups),return_inverse=True,return_counts=True);return 1/n[ii]
def rank(v,w):
 _,ii=np.unique(v,return_inverse=True);mass=np.bincount(ii,weights=w);return (np.cumsum(mass)-mass/2)[ii]
def corr(a,b,w):
 w=w/w.sum();a=a-np.sum(w*a);b=b-np.sum(w*b);den=np.sqrt(np.sum(w*a*a)*np.sum(w*b*b));return float(np.sum(w*a*b)/den) if den>1e-30 else np.nan
def information(prob,y,delta,w=None):
 p=np.asarray(prob,float);y=np.asarray(y,int);d=direction(p);w=np.ones(len(y)) if w is None else np.asarray(w,float)
 valid=y!=0;p=p[valid];d=d[valid];yy=y[valid]>0;dd=np.asarray(delta)[valid];w=w[valid]
 balanced=np.mean([np.average(d[yy]==1,weights=w[yy]),np.average(d[~yy]==-1,weights=w[~yy])]) if yy.any() and (~yy).any() else np.nan
 auc=roc_auc_score(yy,p,sample_weight=w) if yy.any() and (~yy).any() else np.nan
 return dict(Balanced_Accuracy=balanced,Direction_Accuracy=np.average(d==np.where(yy,1,-1),weights=w),AUC=auc,Spearman=corr(rank(p,w),rank(dd,w),w),Spearman_direction=corr(rank(p,w),rank(yy,w),w),Pearson=corr(p,dd,w),Brier=np.average((p-yy)**2,weights=w))
def metrics(prob,rows,table,w=None):
 w=np.ones(len(rows)) if w is None else np.asarray(w,float)
 out=information(prob,rows.y.to_numpy(),rows.delta.to_numpy(),w)
 loss=table[direction(prob)+1,np.arange(len(rows))];base=table[1]
 out.update(FIXED005_CRPS=float(np.sum(w*loss)/np.sum(w*base)),mean_CRPS_delta=float(np.average(loss-base,weights=w)),fraction_improved_cells=float(np.average(loss<base,weights=w)),cells=len(rows),origins=rows.origin.nunique(),truth_ties=int(rows.y.eq(0).sum()))
 return clean(out)
def null_labels(rows,y,kind,rep,fold):
 y=np.asarray(y).copy();rng=np.random.default_rng(np.random.SeedSequence([SEED,10,rep,fold,{'N1':1,'N2':2,'N3':3}[kind]]))
 if kind in ('N1','N2'):
  groups=np.asarray(rows.year if kind=='N1' else rows.asset)
  for g in np.unique(groups):
   ii=np.flatnonzero(groups==g);y[ii]=rng.permutation(y[ii])
 else:
  # Whole quarter label sequences are reordered within TRAIN asset/horizon.
  # Donors are known and matured by fold cutoff. This is a training null, not a tradable synthetic path.
  keys=rows.asset.astype(str)+'/'+rows.horizon.astype(str)
  for key in sorted(set(keys)):
   ii=np.flatnonzero(np.asarray(keys)==key);quarters=rows.iloc[ii].year.astype(str)+'Q'+pd.to_datetime(rows.iloc[ii].origin).dt.quarter.astype(str)
   chunks=[ii[np.asarray(quarters)==q] for q in sorted(set(quarters))]
   y[ii]=np.concatenate([y[chunks[j]].copy() for j in rng.permutation(len(chunks))])
 return y
def historical_donors(indices,rep,fold):
 rng=np.random.default_rng(np.random.SeedSequence([SEED,14,rep,fold]));indices=np.asarray(indices,int)
 # An earliest state maps to itself; every other state draws strictly earlier.
 donors=np.array([rng.integers(0,i) if i>0 else 0 for i in indices]);assert (donors<=indices).all();return donors
def impute_training(train,test):
 with warnings.catch_warnings():
  warnings.simplefilter('ignore',RuntimeWarning);fill=np.nanmedian(np.where(np.isfinite(train),train,np.nan),axis=0)
 fill=np.nan_to_num(fill);return np.where(np.isfinite(train),train,fill),np.where(np.isfinite(test),test,fill),fill

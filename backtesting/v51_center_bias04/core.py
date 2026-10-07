"""Executive summary: frozen definitions, train-only bias and protected original bytes."""
from pathlib import Path
import os,json,hashlib,subprocess
import numpy as np,pandas as pd
from qfbench2_track_forecasting.location01.model import FOLDS,purged_mask

ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent/'results'
PARENT='0f5c938eeb4054518b0bde81e4de1503890fd684';PARENT_PRE='b1681d58ecc75e16760904086e672490d3cc20c6';MAIN='e1b5cf3b3a87966e902332ef3cc5c0ed2dbffee8';BRANCH='track2/v51-center-bias-audit-04'
SEED=31804;AMPLITUDE=.05;WINDOWS=(1,3,5);HORIZONS=(5,21,63,126,189)
PREDICTIVE=('GLOBAL_BIAS_SIGN005','ASSET_BIAS_SIGN005','HORIZON_BIAS_SIGN005','GLOBAL_MEDIAN_SHIFT')
ORACLES=('GLOBAL_ORACLE_BIAS','YEAR_ORACLE_BIAS','ASSET_ORACLE_BIAS','HORIZON_ORACLE_BIAS','ASSET_HORIZON_ORACLE_BIAS')
def private():return Path(os.environ['BIAS04_PRIVATE'])
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clean(x):
 if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
 if isinstance(x,(list,tuple,np.ndarray)):return [clean(v) for v in x]
 if isinstance(x,(bool,np.bool_)):return bool(x)
 if isinstance(x,(int,np.integer)):return int(x)
 if isinstance(x,(float,np.floating)):return float(x) if np.isfinite(x) else None
 return x
def save(path,obj):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(clean(obj),indent=2,allow_nan=False)+'\n')
def csv(name,items):pd.DataFrame(items).to_csv(OUT/name,index=False)
def status(stage,artifact='',**kw):
 f=OUT.parent/'STATUS.json';a=json.loads(f.read_text()) if f.exists() else {};done=a.get('completed_stages',[])
 if stage not in done:done.append(stage)
 a.update(executive_summary='Restartable original-baseline audit. All corrections diagnostic only.',branch=BRANCH,HEAD_SHA=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),current_stage=stage,completed_stages=done,last_successful_artifact=artifact,last_update=pd.Timestamp.now(tz='UTC').isoformat(),**kw);save(f,a)
def protect():
 files=subprocess.check_output(['git','ls-tree','-rz','--name-only',PARENT],cwd=ROOT).decode().rstrip('\0').split('\0');m={f:digest(ROOT/f) for f in files};save(private()/'protected_parent_hashes.json',m);return m
def protected():
 m=json.loads((private()/'protected_parent_hashes.json').read_text());assert all(digest(ROOT/f)==h for f,h in m.items());assert subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip()==MAIN;assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()==BRANCH
def verify():
 r=json.loads((private()/'pre_receipt.json').read_text());assert r['remote_verified'] and r['PRE_RESULT_V51_BIAS04_SHA'];protected()
 for f,h in r['implementation_hashes'].items():assert digest(ROOT/f)==h,f
 assert digest(private()/'canonical/ledger.parquet')==r['ledger_SHA256'];return r
def era(year):return '<=2016' if year<=2016 else '2017-2019' if year<=2019 else '2020-2021' if year<=2021 else '2022-2024'
def weights(groups):
 groups=np.asarray(groups);u,inv,c=np.unique(groups,return_inverse=True,return_counts=True);return 1./c[inv]
def weighted_median(a,w):
 a=np.asarray(a);w=np.asarray(w);valid=w>0;a=a[valid];w=w[valid];i=np.argsort(a,kind='stable');c=np.cumsum(w[i]);half=c[-1]/2;k=np.searchsorted(c,half,side='left');return float((a[i[k]]+a[i[k+1]])/2 if k+1<len(i) and np.isclose(c[k],half,rtol=1e-14,atol=0) else a[i[k]])
def bias(frame,w=None):
 w=np.ones(len(frame)) if w is None else np.asarray(w,float);raw=frame.raw_center_error.to_numpy();std=frame.standardized_center_error.to_numpy();sg=frame.direction.to_numpy()
 return dict(cells=len(frame),origins=int(frame.origin.nunique()),assets=int(frame.asset.nunique()),years=int(frame.year.nunique()),positive_fraction=float(np.average(sg>0,weights=w)),negative_fraction=float(np.average(sg<0,weights=w)),zero_fraction=float(np.average(sg==0,weights=w)),mean_raw_error=float(np.average(raw,weights=w)),median_raw_error=weighted_median(raw,w),mean_standardized_error=float(np.average(std,weights=w)),median_standardized_error=weighted_median(std,w))
def partitions(rows):
 for fold,(_,start,end) in enumerate(FOLDS,1):
  boundary=f'{start}-01-01';train=np.flatnonzero(purged_mask(rows,boundary));test=np.flatnonzero((rows.origin>=boundary)&(rows.origin<=f'{end}-12-31'))
  yield fold,train,test,boundary
def train_bias(rows,indices):
 tr=rows.iloc[indices];assert len(tr)
 glob=float(np.sign(tr.raw_center_error.median()));mean=float(np.sign(tr.raw_center_error.mean()));requested=float(tr.standardized_center_error.median())
 return {'global_sign':glob,'global_mean_sign':mean,'median_requested':requested,'median_capped':float(np.clip(requested,-1,1)),'asset_sign':tr.groupby('asset').raw_center_error.median().map(np.sign).to_dict(),'horizon_sign':tr.groupby('horizon').raw_center_error.median().map(np.sign).to_dict(),'year_sign':tr.groupby('year').raw_center_error.median().map(np.sign).to_dict()}
def predicted_shifts(rows,test,params):
 te=rows.iloc[test]
 return {'GLOBAL_BIAS_SIGN005':np.full(len(te),AMPLITUDE*params['global_sign']),'ASSET_BIAS_SIGN005':AMPLITUDE*np.array([params['asset_sign'].get(a,0.) for a in te.asset]),'HORIZON_BIAS_SIGN005':AMPLITUDE*np.array([params['horizon_sign'].get(h,0.) for h in te.horizon]),'GLOBAL_MEDIAN_SHIFT':np.full(len(te),params['median_capped'])}
def random_directions(rows,folds_params,signs,kind,rep):
 # No test targets are accepted; the rows argument must be an outcome-free identity view.
 allowed={'origin','asset','horizon','year','fold'};assert set(rows)<=allowed
 rng=np.random.default_rng(np.random.SeedSequence([SEED,1,kind,rep]));out=np.array(signs,copy=True)
 if kind==0:return rng.permutation(out)
 for fold,p in folds_params.items():
  ii=np.flatnonzero(rows.fold.to_numpy()==int(fold));te=rows.iloc[ii]
  if kind==1:
   historical=np.array(list(p['year_sign'].values()));out[ii]=rng.permutation(historical)[-1]
  else:
   key='asset_sign' if kind==2 else 'horizon_sign';field='asset' if kind==2 else 'horizon';keys=sorted(p[key],key=str);values=rng.permutation([p[key][k] for k in keys]);mapping=dict(zip(keys,values));out[ii]=[mapping.get(v,0.) for v in te[field]]
 return out
def ratio(loss,base,w=None):
 w=np.ones(len(base)) if w is None else w;return float(np.sum(w*loss)/np.sum(w*base))
def capture(r,oracle):return (1-r)/(1-oracle)

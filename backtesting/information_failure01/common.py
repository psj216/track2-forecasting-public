"""Executive summary: deterministic descriptive aggregation of frozen predictions only."""
import json,hashlib,datetime
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'backtesting/information_failure01/results'
PARENT='ca9b467d48b2fc145faa5bfe549975206c8a811f'
LAMBDA_GRID=(0.,.02,.05,.10,.20,.30,.50,.75,1.)
DIRECTION_CONSTANTS=(.02,.05,.10,.20)
SEED=2026100601
BOOTSTRAP_REPLICATES=5000
POSTHOC='POST_HOC_DIAGNOSTIC_ONLY'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def array_digest(a):return hashlib.sha256(np.ascontiguousarray(a,dtype=np.float64).tobytes()).hexdigest()
def clean(x):
 if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [clean(v) for v in x]
 if isinstance(x,np.ndarray):return clean(x.tolist())
 if isinstance(x,np.integer):return int(x)
 if isinstance(x,(float,np.floating)):return float(x) if np.isfinite(x) else None
 if isinstance(x,np.bool_):return bool(x)
 return x
def save(path,d):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 if 'executive_summary' not in d:d={'executive_summary':'Exposed frozen-prediction failure diagnosis; no new model or confirmatory candidate.',**d}
 path.write_text(json.dumps(clean(d),indent=2,allow_nan=False)+'\n')
def csv(path,rows):
 df=rows.copy() if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows)
 if 'executive_summary' not in df:df.insert(0,'executive_summary','Frozen-prediction descriptive diagnostic; never a new candidate')
 df.to_csv(path,index=False)
def status(stage,source=None,**kw):
 path=ROOT/'backtesting/information_failure01/STATUS.json';d=json.loads(path.read_text());d.update(current_stage=stage,last_update=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw);d['stages'][stage+(':'+source if source else '')]='complete';d['last_successful_artifact']=stage+(':'+source if source else '');save(path,d)
def group_weights(groups):
 _,ii,n=np.unique(np.asarray(groups).astype(str),return_inverse=True,return_counts=True)
 return 1./n[ii]
def weights(rows,balance='cell'):
 if balance=='cell':return np.ones(len(rows))
 return group_weights(rows[{'origin':'origin_date','release':'release_id','year':'year'}[balance]])
def weighted_mean(x,w):return float(np.dot(np.asarray(x,float),w)/np.sum(w))
def weighted_pearson(x,y,w):
 x=np.asarray(x,float);y=np.asarray(y,float);w=np.asarray(w,float);xm=weighted_mean(x,w);ym=weighted_mean(y,w);xx=x-xm;yy=y-ym;den=np.sqrt(np.dot(w,xx*xx)*np.dot(w,yy*yy));return float(np.dot(w,xx*yy)/den) if den>0 else None
def weighted_rank(x,w):
 _,ii=np.unique(np.asarray(x),return_inverse=True);s=np.bincount(ii,weights=w);rank=np.cumsum(s)-.5*s;return rank[ii]
def weighted_spearman(x,y,w):return weighted_pearson(weighted_rank(x,w),weighted_rank(y,w),w)
def sign_partition(y,p):
 y=np.asarray(y);p=np.asarray(p);return np.where((y==0)|(p==0),'ZERO_TIE',np.where(np.sign(y)==np.sign(p),'SIGN_CORRECT','SIGN_WRONG'))
def direction_metrics(y,p,w):
 y=np.asarray(y);p=np.asarray(p);pos=y>0;neg=y<0
 recalls=[weighted_mean(p[pos]>0,w[pos]) if pos.any() and w[pos].sum()>0 else None,weighted_mean(p[neg]<0,w[neg]) if neg.any() and w[neg].sum()>0 else None]
 return dict(sign_accuracy=weighted_mean(np.sign(y)==np.sign(p),w),balanced_sign_accuracy=float(np.mean(recalls)) if all(v is not None for v in recalls) else None,positive_truth_fraction=weighted_mean(pos,w),zero_or_tie_fraction=weighted_mean((y==0)|(p==0),w),pearson=weighted_pearson(y,p,w),spearman=weighted_spearman(y,p,w))
def calibration(y,p,w):
 y=np.asarray(y,float);p=np.asarray(p,float);ym=weighted_mean(y,w);pm=weighted_mean(p,w);v=weighted_mean((p-pm)**2,w);s=weighted_mean((p-pm)*(y-ym),w)/v if v>0 else None;i=ym-s*pm if s is not None else None;vy=weighted_mean((y-ym)**2,w)
 return dict(label=POSTHOC,intercept=i,slope=s,r2=1-weighted_mean((y-i-s*p)**2,w)/vy if s is not None and vy>0 else None,applied_to_candidate=False)
def aggregate(rows,balance='cell'):
 w=weights(rows,balance);y=rows.true_delta.to_numpy();p=rows.predicted_delta.to_numpy();b=rows.baseline_cell_CRPS.to_numpy();c=rows.candidate_cell_CRPS.to_numpy()
 return dict(cells=len(rows),origins=int(rows.origin_date.nunique()),releases=int(rows.release_id.nunique()),years=int(rows.year.nunique()),balance=balance,crps_ratio=float(np.dot(w,c)/np.dot(w,b)),mean_CRPS_delta=weighted_mean(c-b,w),**direction_metrics(y,p,w),calibration=calibration(y,p,w),mean_abs_predicted_delta=weighted_mean(abs(p),w),mean_abs_true_delta=weighted_mean(abs(y),w),mean_predicted_delta=weighted_mean(p,w),mean_predicted_raw_shift=weighted_mean(rows.predicted_raw_shift,w),mean_raw_center_error=weighted_mean(rows.raw_center_error,w))
def private_out(private):return Path(private)/'backtesting/information_failure01/results'
def verify_inputs(private):
 d=json.loads((Path(private)/'input_hash_manifest.json').read_text())
 for name,h in d['files'].items():
  if digest(Path(private)/name)!=h:raise ValueError('Frozen input changed: '+name)
 return d
def verify_pre(private):
 r=json.loads((Path(private)/'PRE-receipt.json').read_text())
 if not r['remote_verified']:raise ValueError('Remote PRE verification required')
 for name,h in r['frozen_implementation_hashes'].items():
  if digest(ROOT/name)!=h:raise ValueError('Frozen diagnosis implementation changed: '+name)
 verify_inputs(private);return r['PRE_RESULT_INFO_FAILURE_SHA']

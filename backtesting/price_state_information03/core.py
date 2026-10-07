"""Executive summary: target-blind controls and exact inherited forecast preservation."""
from pathlib import Path
import hashlib,json,os,subprocess,warnings
import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.stats import rankdata
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from backtesting.persistent_direction02.evaluate import folds,features
from backtesting.persistent_direction02.model import direction
from backtesting.new_information_search02.analyze import price_states

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'results'
PARENT='929ca23e0a57a0529cc64d8a14d5a78b791892e6'
PARENT_PRE='2bdc6722fd5705887bee5f0695a09fe2319bf431'
MAIN='e1b5cf3b3a87966e902332ef3cc5c0ed2dbffee8'
BRANCH='track2/price-state-information-audit-03'
SEED=31803
AMPLITUDE=.05
YEARS=(2020,2021,2022,2023,2024)
HORIZONS=(5,21,63,126,189)
LAGS=(5,21,63)
PRICE_NAMES=tuple(f'DGS{k}_{s}' for k in (2,5,10) for s in ('level','5BD','21BD','63BD'))+('2s5s','2s10s')
GROUPS={'P_LEVEL':(0,4,8),'P_CHANGE':(1,2,3,5,6,7,9,10,11),'P_CURVE':(12,13)}

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def array_hash(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def clean(x):
 if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [clean(v) for v in x]
 if isinstance(x,np.ndarray):return clean(x.tolist())
 if isinstance(x,(float,np.floating)):return float(x) if np.isfinite(x) else None
 if isinstance(x,(bool,np.bool_)):return bool(x)
 if isinstance(x,(int,np.integer)):return int(x)
 return x
def save(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(clean(data),indent=2,allow_nan=False)+'\n')
def csv(name,rows):
 OUT.mkdir(exist_ok=True);pd.DataFrame(rows).to_csv(OUT/name,index=False)
def status(stage,artifact='',**kw):
 path=OUT.parent/'STATUS.json';old=json.loads(path.read_text()) if path.exists() else {}
 done=old.get('completed_stages',[])
 if stage not in done:done.append(stage)
 old.update(executive_summary='Restartable frozen-price audit. No candidate tuning or submission.',branch=BRANCH,current_stage=stage,completed_stages=done,last_successful_artifact=artifact,last_update=pd.Timestamp.now(tz='UTC').isoformat(),**kw)
 save(path,old)
def private():return Path(os.environ['PRICE03_PRIVATE'])
def parent_private():return Path(os.environ['PRICE03_PARENT_PRIVATE'])
def protect():
 p=private();files=subprocess.check_output(['git','ls-tree','-rz','--name-only',PARENT],cwd=ROOT).decode().rstrip('\0').split('\0')
 hashes={f:digest(ROOT/f) for f in files}
 save(p/'protected_parent_hashes.json',hashes)
 return hashes
def assert_protected():
 hashes=json.loads((private()/'protected_parent_hashes.json').read_text())
 assert all(digest(ROOT/f)==h for f,h in hashes.items())
 assert subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip()==MAIN
 assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()==BRANCH
def load():
 p=parent_private();return pd.read_parquet(p/'evaluation_ledger.parquet'),pd.read_parquet(p/'scored_rows.parquet'),np.load(p/'scores.npz')
def verify_pre():
 receipt=json.loads((private()/'pre_receipt.json').read_text());assert receipt['remote_verified'] and receipt['PRE_RESULT_PRICE_STATE03_SHA']
 for f,h in receipt['implementation_hashes'].items():assert digest(ROOT/f)==h,f
 for f,h in receipt['parent_input_hashes'].items():assert digest(parent_private()/f)==h,f
 assert_protected();return receipt

def structure(rows):return np.column_stack([rows.asset.eq('UST_5Y').astype(float),np.log(rows.horizon)])
def fit_control(x,y):
 x=np.asarray(x,float);y=np.asarray(y,int)
 assert np.isfinite(x).all() and set(np.unique(y))=={0,1}
 scaler=StandardScaler().fit(x)
 model=LogisticRegression(C=1.,penalty='l2',fit_intercept=True,class_weight=None,solver='lbfgs',max_iter=2000,tol=1e-8,random_state=SEED)
 with warnings.catch_warnings():
  warnings.simplefilter('ignore',FutureWarning);model.fit(scaler.transform(x),y)
 return scaler,model
def predict(f,x):return f[1].predict_proba(f[0].transform(x))[:,1]
def prior_probability(y):return float(np.mean(np.asarray(y,int)))
def majority_probability(y):
 p=prior_probability(y);return .5 if p==.5 else float(p>.5)
def group_prior(train_group,train_y,test_group):
 default=majority_probability(train_y)
 lookup={g:majority_probability(np.asarray(train_y)[np.asarray(train_group)==g]) for g in set(train_group)}
 return np.array([lookup.get(g,default) for g in test_group])
def lag_price(rows,lag,frame):
 dates=pd.to_datetime(rows.price_observation_date)-pd.offsets.BDay(lag)
 indices=frame.index.searchsorted(dates,side='right')-1
 assert (indices>=0).all()
 chosen=frame.index[indices];assert (chosen<=dates).all()
 x=frame.iloc[indices].to_numpy(float)
 assert np.isfinite(x).all(),'No outcome-driven missing-state replacement is allowed'
 return np.column_stack([x,structure(rows)]),chosen
def permuted_train_price(x,origins,rep,year):
 # Every donor is an admitted, matured TRAIN origin at this fold cutoff.
 # A whole 14-vector is moved together and broadcast to all its asset/horizon cells.
 origins=np.asarray(origins);unique=np.unique(origins)
 states=np.array([x[np.flatnonzero(origins==o)[0],:14] for o in unique])
 rng=np.random.default_rng(np.random.SeedSequence([SEED,1,rep,year]));donors=rng.permutation(len(unique))
 out=x.copy();out[:,:14]=states[donors[np.searchsorted(unique,origins)]]
 return out,unique[donors]
def random_signs(signs,groups,rep,kind):
 # Signature contains no truth, target or score. Exact sign counts, including ties.
 signs=np.asarray(signs);groups=np.asarray(groups)
 out=signs.copy();rng=np.random.default_rng(np.random.SeedSequence([SEED,2,rep,kind]))
 for group in np.unique(groups):
  ii=np.flatnonzero(groups==group);out[ii]=rng.permutation(signs[ii])
 return out
def loss_for(prob,table):return table[direction(prob).astype(int)+1,np.arange(table.shape[1])]
def balanced_weights(groups):
 groups=np.asarray(groups);_,counts=np.unique(groups,return_counts=True)
 lookup=dict(zip(np.unique(groups),counts));return np.array([1./lookup[g] for g in groups])
def correlation(a,b,w):
 a=np.asarray(a,float);b=np.asarray(b,float);w=np.asarray(w,float);w=w/w.sum()
 da=a-np.sum(w*a);db=b-np.sum(w*b);den=np.sqrt(np.sum(w*da*da)*np.sum(w*db*db))
 return float(np.sum(w*da*db)/den) if den>1e-30 else np.nan
def weighted_rank(a,w):
 values,inv=np.unique(a,return_inverse=True);mass=np.bincount(inv,weights=w);mid=np.cumsum(mass)-mass/2
 return mid[inv]
def metrics(prob,loss,rows,base,weights=None):
 w=np.ones(len(rows)) if weights is None else np.asarray(weights,float)
 y=rows.y.to_numpy();valid=y!=0;wv=w[valid];yy=y[valid];pp=np.asarray(prob)[valid];sg=direction(pp)
 positive=yy>0;negative=yy<0
 balanced=(np.average(sg[positive]==1,weights=wv[positive])+np.average(sg[negative]==-1,weights=wv[negative]))/2 if wv[positive].sum()>0 and wv[negative].sum()>0 else np.nan
 return {'CRPS_ratio':float(np.sum(w*loss)/np.sum(w*base)),'sign_accuracy':float(np.average(sg==yy,weights=wv)),
 'balanced_accuracy':float(balanced),'Brier':float(np.average((pp-positive)**2,weights=wv)),
 'Pearson':correlation(pp,positive,wv),'Spearman':correlation(weighted_rank(pp,wv),weighted_rank(positive,wv),wv),
 'fraction_improved_cells':float(np.average(loss<base,weights=w)),'mean_CRPS_delta':float(np.average(loss-base,weights=w)),
 'cells':len(rows),'origins':int(rows.origin.nunique()),'prediction_ties':int((direction(prob)==0).sum())}
def exact_parent_reproduction():
 from qfbench2_common.scoring.crps import crps_ensemble
 rows,evalrows,data=load();p=parent_private();draws=np.load(p/'evaluation_draws.npz')['draws'][:,rows.year.isin(YEARS)]
 assert evalrows[['origin','asset','horizon']].equals(rows.loc[rows.year.isin(YEARS),['origin','asset','horizon']].reset_index(drop=True))
 truth=evalrows.truth.to_numpy();scale=evalrows.scale.to_numpy();sd=evalrows.sd.to_numpy()
 assert np.allclose(np.median(draws,axis=0),evalrows['median'],rtol=0,atol=1e-14)
 assert np.allclose(draws.std(axis=0),sd,rtol=1e-13,atol=1e-14)
 published=json.loads((ROOT/'backtesting/persistent_direction02/results/primary_score_summary.json').read_text())['models']
 record=[];base=crps_ensemble(draws,truth)/scale
 assert np.array_equal(base,data['base'])
 for name in data['names']:
  name=str(name)
  if name=='V5.1':prob=np.full(len(evalrows),.5);loss=base
  elif name=='PERFECT_LOCATION':prob=(evalrows.y.to_numpy()+1)/2;loss=crps_ensemble(draws+evalrows.raw_center_error.to_numpy(),truth)/scale
  else:
   prob=data['prob_'+name];loss=crps_ensemble(draws+AMPLITUDE*sd*direction(prob),truth)/scale
  stored=published[name]['CRPS_ratio'];ratio=float(loss.sum()/base.sum())
  assert abs(ratio-stored)<1e-14,(name,ratio,stored)
  assert np.array_equal(loss,data['losses'][list(data['names']).index(name)])
  record.append(dict(model=name,stored_ratio=stored,reproduced_ratio=ratio,difference=ratio-stored,prediction_SHA256=array_hash(prob),cells=len(evalrows),origins=int(evalrows.origin.nunique())))
 # Recover saved fold parameters; no call to fit. Saved probabilities remain the primary bytes.
 xx=features(rows,price=True);model_checks=[]
 for year,tr,te,c in folds(rows):
  saved=np.load(p/'folds'/f'{year}.npz');assert np.array_equal(saved['indices'],te)
  m=next(a for a in json.loads((p/'folds'/f'{year}.json').read_text()) if a['model']=='PRICE_LOGISTIC')
  reconstructed=expit(((xx[te]-m['scaler_mean'])/m['scaler_scale'])@np.asarray(m['coefficients'])[0]+m['intercept'][0])
  error=float(np.max(abs(reconstructed-saved['PRICE_LOGISTIC'])));assert error<1e-14
  model_checks.append(dict(year=year,max_probability_difference=error,refit=False))
 hashes={f:digest(p/f) for f in ['evaluation_ledger.parquet','evaluation_draws.npz','scored_rows.parquet','scores.npz','design_calendar.parquet']+[f'folds/{y}.{ext}' for y in YEARS for ext in ['json','npz']]}
 save(private()/'parent_input_hashes.json',hashes)
 save(OUT/'parent_price_reproduction.json',{'executive_summary':'Imported common scorer exactly reproduces every saved prior loss array; saved PRICE_FULL probabilities never refitted.','models':record,'fold_parameter_reconstruction':model_checks,'tolerance':1e-14,'loss_arrays_bitwise_equal':True,'PRICE_FULL_refitted':False,'parent_input_hashes':hashes})
 status('PARENT_REPRODUCTION','parent_price_reproduction.json')

"""Executive summary: bounded diagnostic controls, private labels, immutable PRICE_FULL."""
import argparse,time
from .core import *

def controls():
 verify_pre();p=private();dest=p/'audit_predictions.npz'
 if dest.exists():print('resume completed controls',dest,flush=True);return
 rows,ev,data=load();x=features(rows,price=True);ss=structure(rows);mask=rows.year.isin(YEARS).to_numpy()
 probs={n:np.full(len(rows),.5) for n in ['TRAINING_MAJORITY','INTERCEPT_ONLY','STRUCTURE_ONLY','ASSET_PRIOR','HORIZON_PRIOR','P_LEVEL','P_CHANGE','P_CURVE']+[f'PRICE_LAG_{lag}BD' for lag in LAGS]}
 frame,_=price_states(parent_private()/'parent-extracted/private')
 lagged={lag:lag_price(rows,lag,frame)[0] for lag in LAGS}
 folds_audit=[]
 for year,tr,te,c in folds(rows):
  y=(rows.y.to_numpy()[tr]>0).astype(int)
  probs['TRAINING_MAJORITY'][te]=majority_probability(y)
  # Intercept-only maximum likelihood logistic: expit(logit(train frequency)).
  # Intercept is unpenalized in inherited lbfgs; closed form avoids dummy-feature fitting.
  probs['INTERCEPT_ONLY'][te]=prior_probability(y)
  probs['ASSET_PRIOR'][te]=group_prior(rows.asset.to_numpy()[tr],y,rows.asset.to_numpy()[te])
  probs['HORIZON_PRIOR'][te]=group_prior(rows.horizon.to_numpy()[tr],y,rows.horizon.to_numpy()[te])
  for name,xx in [('STRUCTURE_ONLY',ss)]+[(n,np.column_stack([x[:,idx],ss])) for n,idx in GROUPS.items()]+[(f'PRICE_LAG_{lag}BD',lagged[lag]) for lag in LAGS]:
   f=fit_control(xx[tr],y);probs[name][te]=predict(f,xx[te])
  folds_audit.append(dict(year=year,train_cells=len(tr),test_cells=len(te),first_cutoff=c.isoformat(),max_train_target_end=rows.iloc[tr].target_end.max(),train_origins=int(rows.iloc[tr].origin.nunique()),test_origins=int(rows.iloc[te].origin.nunique()),train_indices_SHA256=array_hash(tr),test_indices_SHA256=array_hash(te)))
  np.savez_compressed(p/f'diagnostic_fold_{year}.npz',indices=te,**{n:a[te] for n,a in probs.items()})
  print('diagnostic fold',year,'5 folds; output',p/f'diagnostic_fold_{year}.npz',flush=True)
 probs={n:a[mask] for n,a in probs.items()}
 for old,new in [('PRICE_LOGISTIC','PRICE_FULL'),('PRICE_21BD','PRICE_21BD'),('MATCHED_RANDOM','MATCHED_RANDOM'),('PERSISTENCE','PERSISTENCE'),('SEP_DIRECTION_FIXED005','SEP')]:probs[new]=data['prob_'+old]
 probs['V5.1']=np.full(len(ev),.5);probs['CONSTANT_UP']=np.ones(len(ev));probs['CONSTANT_DOWN']=np.zeros(len(ev));probs['PERFECT_LOCATION']=(ev.y.to_numpy()+1)/2
 names=list(probs);loss=np.array([data['oracle'] if n=='PERFECT_LOCATION' else loss_for(probs[n],data['table']) for n in names])
 np.savez_compressed(dest,names=names,probabilities=np.array(list(probs.values())),losses=loss,base=data['base'],oracle=data['oracle'])
 csv('fold_manifest.csv',folds_audit)
 public=ev[['origin','asset','horizon','year']].copy()
 for n,a in probs.items():
  if n!='PERFECT_LOCATION':public[n+'_probability']=a
 public.to_csv(OUT/'diagnostic_predictions.csv',index=False)
 status('CONTROL_MODELS','diagnostic_predictions.csv')

def permutation(start,stop):
 verify_pre();p=private();folder=p/'feature_permutation';folder.mkdir(exist_ok=True);dest=folder/f'{start:04d}-{stop:04d}.npz'
 if dest.exists():print('resume completed permutation',dest,flush=True);return
 rows,ev,data=load();xx=features(rows,price=True);groups=list(folds(rows));mask=rows.year.isin(YEARS).to_numpy();ys=(rows.y.to_numpy()>0).astype(int)
 stats=[];begun=time.monotonic()
 for rep in range(start,stop):
  prob=np.full(len(rows),.5)
  for year,tr,te,c in groups:
   xp,donors=permuted_train_price(xx[tr],rows.origin.to_numpy()[tr],rep,year)
   assert set(donors)<=set(rows.origin.to_numpy()[tr]);assert max(donors)<str(c.date())
   prob[te]=predict(fit_control(xp,ys[tr]),xx[te])
  pp=prob[mask];m=metrics(pp,loss_for(pp,data['table']),ev,data['base']);stats.append([m['CRPS_ratio'],m['balanced_accuracy'],m['Spearman']])
  if (rep-start+1)%25==0:print('feature permutation',rep+1,'/2000 elapsed',round(time.monotonic()-begun,1),'output',dest,flush=True)
 np.savez_compressed(dest,statistics=stats);status('FEATURE_PERMUTATION_CHUNK',str(dest),permutation_completed_to=stop)

def random_chunk(kind,start,stop):
 verify_pre();p=private();folder=p/'random_sign';folder.mkdir(exist_ok=True);dest=folder/f'{kind}-{start:04d}-{stop:04d}.npz'
 if dest.exists():return
 _,ev,data=load();sg=direction(data['prob_PRICE_LOGISTIC']);groups=np.ones(len(ev)) if kind=='A' else ev[{'B':'asset','C':'horizon','D':'year'}[kind]].to_numpy()
 losses=[];statistics=[]
 for rep in range(start,stop):
  d=random_signs(sg,groups,rep,'ABCD'.index(kind));pp=(d+1)/2;loss=loss_for(pp,data['table']);m=metrics(pp,loss,ev,data['base']);losses.append(loss);statistics.append([m['CRPS_ratio'],m['balanced_accuracy']])
 np.savez_compressed(dest,statistics=statistics,losses=losses)
 print('random sign',kind,start,stop,'/5000 output',dest,flush=True);status('RANDOM_'+kind+'_CHUNK',str(dest),random_completed_to=stop)

def bootstrap(block,start,stop):
 verify_pre();p=private();folder=p/'bootstrap';folder.mkdir(exist_ok=True);dest=folder/f'{block}-{start:04d}-{stop:04d}.npz'
 if dest.exists():return
 _,rows,_=load();data=np.load(p/'audit_predictions.npz');names=list(data['names']);loss=data['losses'];base=data['base'];prob=data['probabilities'][names.index('PRICE_FULL')]
 keys=rows.origin if block=='origin' else rows.year if block=='year' else pd.to_datetime(rows.origin).dt.to_period('Q').astype(str)
 unique=np.unique(keys);indices=[np.flatnonzero(np.asarray(keys)==g) for g in unique]
 matrix=np.array([loss[:,ii].sum(axis=1) for ii in indices]);oracle=np.array([data['oracle'][ii].sum() for ii in indices])
 random_losses=np.concatenate([np.load(f)['losses'] for f in sorted((p/'random_sign').glob('A-*.npz'))]);assert len(random_losses)==5000
 random_matrix=np.array([random_losses[:,ii].sum(axis=1) for ii in indices]).T
 counts=[];weights=[]
 for rep in range(start,stop):
  rng=np.random.default_rng(np.random.SeedSequence([SEED,3,{'origin':0,'year':1,'quarter':2}[block],rep]));ct=np.bincount(rng.integers(len(indices),size=len(indices)),minlength=len(indices));counts.append(ct)
 counts=np.array(counts);totals=counts@matrix;den=totals[:,names.index('V5.1')];ratios=totals/den[:,None]
 nullmedian=np.median((counts@random_matrix.T)/den[:,None],axis=1)
 results=[]
 for j,ct in enumerate(counts):
  w=np.zeros(len(rows))
  for k,ii in enumerate(indices):w[ii]=ct[k]
  m=metrics(prob,loss[names.index('PRICE_FULL')],rows,base,w);rr=ratios[j,names.index('PRICE_FULL')];ro=float(counts[j]@oracle/den[j])
  results.append([rr,rr-1,rr-ratios[j,names.index('INTERCEPT_ONLY')],rr-ratios[j,names.index('STRUCTURE_ONLY')],rr-nullmedian[j],rr-ratios[j,names.index('TRAINING_MAJORITY')],m['balanced_accuracy'],m['Spearman'],(1-rr)/(1-ro)])
 np.savez_compressed(dest,statistics=results)
 print('bootstrap',block,start,stop,'/5000 output',dest,flush=True);status('BOOTSTRAP_'+block+'_CHUNK',str(dest),bootstrap_completed_to=stop)

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('stage',choices=['controls','permutation','random','bootstrap']);a.add_argument('--start',type=int,default=0);a.add_argument('--stop',type=int,default=100);a.add_argument('--kind');q=a.parse_args()
 if q.stage=='controls':controls()
 elif q.stage=='permutation':permutation(q.start,q.stop)
 elif q.stage=='random':random_chunk(q.kind,q.start,q.stop)
 else:bootstrap(q.kind,q.start,q.stop)

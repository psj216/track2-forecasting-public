"""Executive summary: fixed-seed release-block nulls, same chronological fitting and weights.

2000 replicates per stochastic control, written in chunks. Date controls only
permute nonnegative activation delays, never publishing information early.
"""
import argparse,json,time
from pathlib import Path
import numpy as np,pandas as pd
from .evaluate import ROOT,OUT,CONTROLS,verify_pre,folds,status
from .model import SEED,MODELS,MIN_RELEASES,YEARS,ASSETS,PRIMARY_ASSETS,HORIZONS,release_weights,batch_ridge,metrics,shift
from .source_dataset import FEATURES,save,asof_features,cutoff,activation
from qfbench2_common.scoring.crps import crps_ensemble


def altered_calendar(rows,kind,seed,states):
 dates=rows.origin.to_numpy();origins=sorted(set(dates));rng=np.random.default_rng(seed)
 if kind=='RELEASE_DATE_PERMUTATION':
  delays=rng.permutation(np.resize(np.arange(21),len(states)))
  dates_pub=np.busday_offset(np.array([s['publication_date'] for s in states],dtype='datetime64[D]'),delays,roll='forward')
  # Zero delay must preserve the exact date even if an unusual release occurs on a weekend.
  for i,d in enumerate(delays):
   if d==0:dates_pub[i]=np.datetime64(states[i]['publication_date'])
  available=np.array([activation(str(d)).tz_convert('UTC').to_datetime64() for d in dates_pub]);cut=np.array([cutoff(d).tz_convert('UTC').to_datetime64() for d in origins])
 else:
  available=np.array([pd.Timestamp(s['available_at']).tz_convert('UTC').to_datetime64() for s in states]);dates_pub=np.array([s['publication_date'] for s in states],dtype='datetime64[D]');cut=np.array([cutoff(pd.Timestamp(d) if kind=='ONE_RELEASE_LAG' else pd.Timestamp(d)-pd.DateOffset(years=1)).tz_convert('UTC').to_datetime64() for d in origins])
 order=np.argsort(available);choice=np.searchsorted(available[order],cut,side='right')-1
 mapping={};release={}
 for d,k in zip(origins,choice):
  if k<0 or (kind=='ONE_RELEASE_LAG' and k==0):mapping[d]=[np.nan]*5;release[d]=None;continue
  j=order[max(0,k-1)] if kind=='ONE_RELEASE_LAG' and k>0 else order[k];s=states[j];query=pd.Timestamp(d) if kind=='RELEASE_DATE_PERMUTATION' else pd.Timestamp(d) if kind=='ONE_RELEASE_LAG' else pd.Timestamp(d)-pd.DateOffset(years=1);age=int(np.busday_count(dates_pub[j],np.datetime64(str(cutoff(query).date()))))
  f=[s[FEATURES[i]] for i in range(4)]+[age]
  mapping[d]=f if age<=70 and s['full5_usable_at_release'] and None not in f else [np.nan]*5;release[d]=s['release_id'] if np.isfinite(np.array(mapping[d],float)).all() else None
 return np.array([mapping[d] for d in dates],float),np.array([release[d] for d in dates],object)


def predictions(rows,x,kind,start,stop,states):
 count=stop-start;pp=np.full((count,len(rows)),np.nan);y=rows.delta.to_numpy();rel=rows.release_id.to_numpy();cols=tuple(range(5))
 if kind in ('RELEASE_DATE_PERMUTATION','FEATURE_YEAR_SHIFT','ONE_RELEASE_LAG'):
  for b,rep in enumerate(range(start,stop)):
   xx,rr=altered_calendar(rows,kind,SEED+rep,states);pp[b,pd.to_datetime(rows.origin).dt.year.ge(2017)]=0.
   for asset,horizon,year,train,test,c,valid in folds(rows,xx,rr,assets=PRIMARY_ASSETS):
    if not valid:continue
    active=test[np.isfinite(xx[test]).all(axis=1)]
    if not len(active):continue
    w=release_weights(rr[train]);pp[b,active]=batch_ridge(xx[None,train,:],y[train],w,xx[None,active,:])[0]
  return pp
 for asset,horizon,year,train,test,c,valid in folds(rows,x,assets=PRIMARY_ASSETS):
  if not valid:continue
  releases=sorted(set(rel[train]));vectors=np.array([x[train[np.flatnonzero(rel[train]==r)[0]],:4] for r in releases]);lookup={r:i for i,r in enumerate(releases)};ri=np.array([lookup[r] for r in rel[train]]);xt=np.repeat(x[train][None],count,axis=0);xx=np.repeat(x[test][None],count,axis=0)
  for b,rep in enumerate(range(start,stop)):
   rng=np.random.default_rng(SEED+rep+year*100+HORIZONS.index(horizon))
   if kind=='RELEASE_VALUE_SHUFFLE':xt[b,:,:4]=vectors[rng.permutation(len(releases))][ri]
   elif kind in ('POLICY_REVISION_SIGN_SHUFFLE','POLICY_PATH_ORIENTATION_SHUFFLE'):
    signs=rng.permutation(np.resize(np.array([-1.,1.]),len(releases)))[ri];columns=(3,) if kind=='POLICY_REVISION_SIGN_SHUFFLE' else (0,1,2,3)
    for col in columns:
     if kind=='POLICY_REVISION_SIGN_SHUFFLE':xt[b,:,col]=vectors[rng.permutation(len(releases)),col][ri]
     xt[b,:,col]*=signs
   elif kind=='GAUSSIAN_FULL5':
    # Per-release Gaussian vectors are reproducible across assets/horizons/folds.
    allr=sorted(set(rel));rng=np.random.default_rng(SEED+rep);v=dict(zip(allr,rng.normal(size=(len(allr),5))));xt[b]=np.array([v[r] for r in rel[train]]);xx[b]=np.array([v[r] for r in rel[test]])
  pp[:,test]=batch_ridge(xt,y[train],release_weights(rel[train]),xx)
 return pp


def run(private,kind,start,stop):
 verify_pre(private);folder=private/'controls';folder.mkdir(exist_ok=True);path=folder/f'{kind}-{start:04d}-{stop:04d}.npz'
 if path.exists():print('REUSE',path,flush=True);return
 rows=pd.read_parquet(private/'evaluation_ledger.parquet');x=rows[list(FEATURES)].to_numpy();states=json.loads((OUT/'source_states.json').read_text())['states'];pred=np.load(private/'predictions.npz');test=pred['eval_mask'];rr=rows.loc[test];samples=np.load(private/'evaluation_draws.npz')['draws'][:,test];truth=rr.truth.to_numpy();sd=rr.sd.to_numpy();scale=rr.scale.to_numpy();base=np.load(private/'losses.npz')['baseline'];starttime=time.monotonic();pp=predictions(rows,x,kind,start,stop,states)[:,test]
 if not np.isfinite(pp).all():raise ValueError('Control missing common evaluated cells')
 ratios=[]
 for p in pp:ratios.append(float((crps_ensemble(shift(samples,p,sd),truth)/scale).sum()/base.sum()))
 np.savez_compressed(path,ratios=ratios,replicate_start=start,replicate_stop=stop)
 print(f'CONTROL {kind} completed={stop}/2000 elapsed={time.monotonic()-starttime:.1f}s output={path}',flush=True)


def mutation(private):
 verify_pre(private);states=json.loads((OUT/'source_states.json').read_text())['states'];calendar=pd.read_csv(OUT/'source_calendar.csv',float_precision='round_trip');passed=True;smp_passed=True
 for origin in calendar.origin:
  mutated=[dict(s) for s in states]
  for s in mutated:
   if pd.Timestamp(s['available_at'])>cutoff(origin):
    for f in FEATURES[:4]:s[f]=123456.789
  before=asof_features(states,origin);after=asof_features(mutated,origin);passed&=before==after
  smp=[dict(s,panel='SMP',POLICY_NEAR=987654.) for s in states];smp_passed &= before==asof_features(states+smp,origin)
 # Predictive claim: fixed fitted model + exact unchanged earlier features yields bitwise predictions.
 rows=pd.read_parquet(private/'evaluation_ledger.parquet');x=rows[list(FEATURES)].to_numpy();invariance=True
 from .model import fit_ridge,predict
 for a,h,y,tr,te,c,valid in folds(rows,x,assets=PRIMARY_ASSETS):
  if not valid:continue
  f=fit_ridge(x[tr],rows.delta.to_numpy()[tr],rows.release_id.to_numpy()[tr],tuple(range(5)))
  original=predict(f,x[te],tuple(range(5)));altered=[]
  for i in te:
   origin=rows.iloc[i].origin;m=[dict(s) for s in states]
   for s in m:
    if pd.Timestamp(s['available_at'])>cutoff(origin):
     for feature in FEATURES[:4]:s[feature]=-98765.4
   state=asof_features(m,origin);altered.append([state[feature] for feature in FEATURES])
  modified=predict(f,np.array(altered),tuple(range(5)));invariance&=np.array_equal(original,modified)
 # Outcome-side copy changes no source construction or feature array; no refitting assertion.
 changed=rows.copy();changed['truth']=np.arange(len(rows));changed['delta']=-1234.
 outcome=np.array_equal(x,changed[list(FEATURES)].to_numpy())
 save(OUT/'mutation_audit.json',{'SMP_contamination_features_predictions_invariant':bool(smp_passed),'future_source_features_bitwise_unchanged':bool(passed),'future_source_predictions_bitwise_unchanged':bool(invariance),'outcome_mutation_features_unchanged':bool(outcome),'outcome_mutation_scope':'Features invariant; training-label changes are not claimed to leave refitted models invariant'})
 if not (passed and invariance and outcome and smp_passed):raise ValueError('Mutation invariance failed')


def summarize(private):
 primary=json.loads((OUT/'primary_score_summary.json').read_text())['models'][next(iter(MODELS))]['crps_ratio'];out={}
 for kind in (*CONTROLS,'FEATURE_YEAR_SHIFT','ONE_RELEASE_LAG'):
  paths=sorted((private/'controls').glob(kind+'-*.npz'));ratios=np.concatenate([np.load(p)['ratios'] for p in paths])
  expected=1 if kind in ('FEATURE_YEAR_SHIFT','ONE_RELEASE_LAG') else 2000
  if len(ratios)!=expected:raise ValueError('Incomplete control '+kind)
  out[kind]=dict(replicates=len(ratios),median_ratio=float(np.median(ratios)),ratio_95_range=np.quantile(ratios,[.025,.975]).tolist(),fraction_at_least_as_good=float(np.mean(ratios<=primary)))
 save(OUT/'negative_controls.json',{'controls':out,'seed':SEED,'replicates_per_stochastic_control':2000,'date_permutation':'Permuted 0..20 business-day nonnegative activation delays; no early publication; missing test state gives zero shift on fixed common ledger','value_shuffle':'Four economic values shuffled across training releases only, test values unchanged; age retained','sign_shuffle':'Balanced training-release sign: revision only, or entire four-coordinate policy path jointly. Test source values unchanged.','SMP_contamination':'Strict SPD-only eligibility; tested synthetic and actual source rows; no SMP fallback','mutation':json.loads((OUT/'mutation_audit.json').read_text()),'independent_OOS':False});status('controls')

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--private',type=Path,required=True);ap.add_argument('--kind',choices=(*CONTROLS,'FEATURE_YEAR_SHIFT','ONE_RELEASE_LAG','MUTATION','SUMMARY'),required=True);ap.add_argument('--start',type=int,default=0);ap.add_argument('--stop',type=int,default=25);a=ap.parse_args()
 if a.kind=='MUTATION':mutation(a.private)
 elif a.kind=='SUMMARY':summarize(a.private)
 else:run(a.private,a.kind,a.start,a.stop)

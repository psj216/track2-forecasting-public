"""Executive summary: complete exposed audit, fixed gates, no model repair or favorable subset."""
from .core import *
from .evaluate import metrics
import argparse

def distribution(universe,kind,observed):
 p=private();files=sorted((p/'nulls'/universe).glob(kind+'-*.npz'));arrays=[];reps=[]
 for f in files:
  with np.load(f) as d:arrays.append(d['metrics']);reps.extend(d['replicates'].tolist());keys=d['keys'].tolist()
 expected=RANDOM_REPS if kind in ['N0','FOLD_RANDOM','BALANCED_RANDOM'] or kind.startswith('FAMILY_') else NULL_REPS
 assert sorted(reps)==list(range(expected)),(universe,kind,len(reps),expected)
 values=np.vstack(arrays);summary={}
 for j,key in enumerate(keys):
  v=values[:,j];v=v[np.isfinite(v)];obs=observed.get(key)
  lower=key in ('Brier','FIXED005_CRPS')
  pvalue=(1+np.sum(v<=obs if lower else v>=obs))/(len(v)+1) if obs is not None and len(v) else None
  summary[key]=dict(mean=np.mean(v) if len(v) else None,q05=np.quantile(v,.05) if len(v) else None,q50=np.quantile(v,.5) if len(v) else None,q95=np.quantile(v,.95) if len(v) else None,Monte_Carlo_p=pvalue,observed_percentile=float(np.mean(v<=obs)) if obs is not None and len(v) else None)
 return clean(dict(replicates=expected,statistics=summary,conditional_frozen_ledger=True,exchangeability='NOT_EXACT: historical resampling' if kind=='N4' else 'Diagnostic null; dependence/stationarity assumptions disclosed'))

def bootstrap_summary(universe):
 out={}
 for block in ['origin','year','quarter','asset']:
  arrays=[]
  for f in sorted((private()/'bootstrap'/universe).glob(block+'-*.npz')):
   d=np.load(f);arrays.append(d['values']);keys=d['keys'].tolist()
  v=np.vstack(arrays);assert len(v)==BOOTSTRAP_REPS
  out[block]=dict(replicates=len(v),intervals={k:np.nanquantile(v[:,j],[.025,.975]).tolist() for j,k in enumerate(keys)},fixed_crossfit_predictions=True,no_IID_cells=True)
 return out

def concentration(rows,prob,table):
 gain=table[1]-table[direction(prob)+1,np.arange(len(rows))];out={}
 for key in ['year','asset','horizon','origin']:
  s=pd.Series(gain).groupby(rows[key].reset_index(drop=True)).sum();positive=s.clip(lower=0);total=positive.sum()
  out[key]=dict(largest_positive_group=str(positive.idxmax()) if total>0 else None,largest_share=float(positive.max()/total) if total>0 else None,positive_gain_sum=float(total),net_gain_sum=float(s.sum()),all_group_gains={str(k):float(v) for k,v in s.items()})
 return out

def aggregate():
 receipt=verify_pre();p=private();summaries={};nulls={};bootstrap={};year_results=[];asset_results=[];horizon_results=[];families=[];bins=[];confidence=[];concentrations={};calibration={};perturbations={};primary_observed={}
 for universe in ['u0','u1']:
  rows=pd.read_parquet(p/f'{universe}_eval.parquet');data=np.load(p/f'{universe}_table.npz');table=data['table'];pred=np.load(p/f'{universe}_predictions.npz');prob=pred['PRICE_LOGISTIC'];base=table[1]
  obs=metrics(prob,rows,table);primary_observed[universe]=obs
  model_summary={name:metrics(pred[name],rows,table) for name in pred.files}
  # V5.1 has no directional classifier; p=.5 information statistics are descriptive zero-information baseline only.
  model_summary['V5.1_NO_ACTION']=dict(FIXED005_CRPS=1.,Balanced_Accuracy=None,Direction_Accuracy=None,AUC=.5,Spearman=None,Brier=.25)
  balances={}
  for name,key in [('cell',None),('origin','origin'),('year','year'),('asset','asset')]+([('release','release_id')] if universe=='u0' else []):
   balances[name]=metrics(prob,rows,table,None if key is None else weights(rows[key]))
  summaries[universe]=dict(executive_summary='Frozen price-direction audit, same ledger for all comparators.',models=model_summary,weightings=balances,cells=len(rows),origins=rows.origin.nunique(),assets=sorted(rows.asset.unique()),years=sorted(rows.year.unique()),evaluation_folds=sorted(rows.fold.unique()),price_PIT='C',independent_OOS=False)
  save(OUT/f'{universe}_metrics.json',summaries[universe])
  nulls[universe]={kind:distribution(universe,kind,obs) for kind in ['N0','N1','N2','N3','N4','N5','FOLD_RANDOM','BALANCED_RANDOM']}
  bootstrap[universe]=bootstrap_summary(universe);concentrations[universe]=concentration(rows,prob,table)
  for key,target in [('year',year_results),('asset',asset_results),('horizon',horizon_results)]:
   for group in sorted(rows[key].unique()):
    ii=np.flatnonzero(rows[key].eq(group));a=rows.iloc[ii].reset_index(drop=True);t=table[:,ii]
    for name in ['PRICE_LOGISTIC','MAJORITY','ZERO']:
     m=metrics(pred[name][ii],a,t);m.update(universe=universe,group=str(group),model=name,actual_positive_prevalence=float(a.y.gt(0).mean()),predicted_positive_prevalence=float((direction(pred[name][ii])>0).mean()))
     target.append(m)
  for name in pred.files:
   if universe=='u1' and name not in ['PRICE_LOGISTIC','MAJORITY','STRUCTURE_ONLY','ZERO']:
    fm=metrics(pred[name],rows,table);dn=distribution(universe,'FAMILY_'+name,fm)
    families.append(dict(universe=universe,family=name,diagnostic_only=True,features=len(json.loads((OUT/'frozen_feature_spec.json').read_text())['secondary_groups'][name]),**fm,null_balanced_p=dn['statistics']['Balanced_Accuracy']['Monte_Carlo_p'],null_CRPS_p=dn['statistics']['FIXED005_CRPS']['Monte_Carlo_p'],null_CRPS_q05=dn['statistics']['FIXED005_CRPS']['q05']))
  for lo,hi in zip(CONFIDENCE_EDGES[:-1],CONFIDENCE_EDGES[1:]):
   distance=np.abs(prob-.5);mask=(distance>=lo)&(distance<hi if hi<.5 else distance<=hi)
   ii=np.flatnonzero(mask)
   if len(ii):confidence.append(dict(universe=universe,low=lo,high=hi,**metrics(prob[ii],rows.iloc[ii].reset_index(drop=True),table[:,ii]),mean_realized_standardized_error=float(rows.iloc[ii].delta.mean())))
  loss=table[direction(prob)+1,np.arange(len(rows))];sign=direction(prob);true=rows.y.to_numpy()
  for label,mask in [('CORRECT',(sign==true)&(true!=0)),('WRONG',(sign!=true)&(true!=0)&(sign!=0)),('ZERO_TIE',(true==0)|(sign==0))]:
   if mask.any():confidence.append(dict(universe=universe,partition=label,cells=int(mask.sum()),fraction=float(mask.mean()),CRPS_ratio=float(loss[mask].sum()/base[mask].sum()),mean_CRPS_delta=float((loss[mask]-base[mask]).mean())))
  calibration[universe]=dict(mean_probability=float(prob.mean()),positive_frequency=float(rows.y.gt(0).mean()),Brier=obs['Brier'],extreme_probability_fraction=float(((prob<.05)|(prob>.95)).mean()),no_recalibration=True)
  for lo in np.arange(0,1,.1):
   ii=np.flatnonzero((prob>=lo)&(prob<lo+.1 if lo<.9 else prob<=1))
   if len(ii):bins.append(dict(universe=universe,low=float(lo),high=float(lo+.1),cells=len(ii),mean_probability=float(prob[ii].mean()),realized_positive_frequency=float(rows.iloc[ii].y.gt(0).mean())))
  symmetric=(table[0]+table[2])/2
  assert np.min(symmetric-base)>-1e-11,'Shared-CRPS convexity diagnostic failed'
  prevalence=float((direction(prob)>0).mean());expected=(1-prevalence)*table[0]+prevalence*table[2]
  perturbations[universe]=dict(ZERO=1.,PLUS=float(table[2].sum()/base.sum()),MINUS=float(table[0].sum()/base.sum()),balanced_random_expected_ratio=float(symmetric.sum()/base.sum()),prevalence_matched_expected_ratio=float(expected.sum()/base.sum()),matched_positive_prevalence=prevalence,balanced_random_distribution=nulls[universe]['BALANCED_RANDOM'],matched_distribution=nulls[universe]['N0'],fold_matched_distribution=nulls[universe]['FOLD_RANDOM'],symmetric_convexity_min_difference=float((symmetric-base).min()))
 for name,values in [('year_results.csv',year_results),('asset_results.csv',asset_results),('horizon_results.csv',horizon_results),('family_ablation.csv',families),('confidence_bin_summary.csv',confidence),('calibration_bins.csv',bins)]:pd.DataFrame(values).to_csv(OUT/name,index=False)
 save(OUT/'primary_direction_metrics.json',dict(executive_summary='Balanced direction accuracy principal; rank target and weighting disclosed.',U0=summaries['u0']['weightings'],U1=summaries['u1']['weightings'],principal_statistic='Cell balanced direction accuracy',U1_original_canonical_fold_count=4,U1_evaluable_fold_count=len(summaries['u1']['evaluation_folds'])))
 save(OUT/'primary_fixed005_score.json',dict(executive_summary='Fixed .05SD secondary diagnostic; no submission candidate.',U0=primary_observed['u0'],U1=primary_observed['u1'],amplitude_SD=.05))
 save(OUT/'null_summary.json',dict(executive_summary='Full null distributions, plus-one Monte Carlo correction; not IID independent evidence.',universes=nulls,N6='Training majority in models',N7='p=.5 zero-information in models',N8='NOT_AVAILABLE',seed=SEED));save(OUT/'null_distributions_summary.json',nulls)
 save(OUT/'baseline_perturbation_audit.json',dict(executive_summary='Fixed signs and matched prevalence; exact symmetric expectation obeys CRPS convexity.',universes=perturbations,no_amplitude_search=True))
 save(OUT/'bootstrap_summary.json',dict(executive_summary='Paired block inference conditional on frozen models; only source-covered evaluation years exist.',universes=bootstrap,replicates=5000,cell_IID=False,overlapping_horizon_dependence_remaining=True))
 save(OUT/'calibration_summary.json',dict(executive_summary='Descriptive bins only, no Platt/isotonic repair.',universes=calibration))
 save(OUT/'concentration_summary.json',dict(executive_summary='All years/assets/horizons retained; no positive subset promoted.',universes=concentrations))
 save(OUT/'pit_sensitivity.json',dict(executive_summary='Exact fixed14 only has current-vintage C; stronger vintage comparison cannot be computed.',PIT_LIMITATION_UNRESOLVED=True,stronger_fixed14_history='NOT_AVAILABLE',feature_revision_invariance='NOT_ESTABLISHED',conclusion_confidence_cap='INCONCLUSIVE',new_numeric_source=False))
 fm=pd.DataFrame(families);fm.loc[fm.family.isin(['SELF_PRICE','RATE_LEVEL','RATE_CURVE'])].to_csv(OUT/'self_vs_global_price_state.csv',index=False)
 oracle={u:dict(perfect_location_ratio=float(np.load(p/f'{u}_table.npz')['oracle'].sum()/np.load(p/f'{u}_table.npz')['table'][1].sum()),candidate_ratio=primary_observed[u]['FIXED005_CRPS']) for u in ['u0','u1']}
 for u,v in oracle.items():v['oracle_capture']=(1-v['candidate_ratio'])/(1-v['perfect_location_ratio'])
 save(OUT/'oracle_summary.json',dict(executive_summary='Future-informed diagnostic headroom, not predictability evidence.',universes=oracle))
 # Provenance decision was frozen before labels. Descriptive gains cannot override it.
 classification='PIT_BLOCKED';next_axis='PRICE-PIT-RECOVERY-04'
 save(OUT/'information_classification.json',dict(executive_summary='Historical fixed14 price provenance prevents a defensible alpha claim; C sensitivity diagnostics remain valid research.',classification=classification,PIT='C',revision_invariance=False,primary_U1=primary_observed['u1'],null_principal_p={k:v['statistics']['Balanced_Accuracy']['Monte_Carlo_p'] for k,v in nulls['u1'].items()},concentration=concentrations['u1'],all_other_gates_reported_without_claim=True))
 save(OUT/'next_axis_decision.json',dict(executive_summary='Exactly one future axis; not executed.',NEXT=next_axis,reason='Only C fixed14 history; recover original-vintage provenance before assigning predictive information confidence',next_experiment_executed=False))
 save(OUT/'final_decision.json',dict(executive_summary='Separate extension of original inconclusive audit; no tuning, alpha claim, submission or next experiment.',PRICE_STATE_INFO03_EXPANDED_RESULT=classification,NEXT=next_axis,PRE_RESULT_PRICE_STATE_INFO03_SHA=receipt['PRE_RESULT_PRICE_STATE_INFO03_EXPANDED_SHA'],PRIOR_RESULT_SHA=PRIOR,PARENT_RESULT_SHA=PARENT,PRIMARY_U1=primary_observed['u1'],PRICE_DATA_READY=True,PIT='C',INDEPENDENT_OOS=False,original_result_unchanged=True,submission=False))
 status('AGGREGATION_COMPLETE',OUT/'final_decision.json');print('FINAL',classification,next_axis,primary_observed,flush=True)

if __name__=='__main__':aggregate()

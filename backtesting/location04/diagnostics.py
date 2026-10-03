"""Executive summary: paired release/year block inference and concentration, never model tuning."""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import pearsonr,spearmanr
from .evaluate import OUT,verify_pre,status
from .model import MODELS,SEED,verdict
from .source_dataset import FEATURES,save,write_csv

def bootstrap(rows,base,loss,oracle,y,p,field,n=5000):
 keys=sorted(set(rows[field]));indices=[np.flatnonzero(rows[field]==k) for k in keys];sums=np.array([[base[i].sum(),loss[i].sum(),oracle[i].sum()] for i in indices]);rng=np.random.default_rng(SEED+(1 if field=='release_id' else 2));values=[];corr=[]
 for rep in range(n):
  chosen=rng.integers(len(keys),size=len(keys));b,c,o=sums[chosen].sum(axis=0);values.append([c/b,c/b-1,(b-c)/(b-o)]);ii=np.concatenate([indices[k] for k in chosen]);yy=y[ii];pp=p[ii]
  if np.ptp(yy)>0 and np.ptp(pp)>0:corr.append([pearsonr(yy,pp).statistic,spearmanr(yy,pp).statistic])
  if (rep+1)%1000==0:print(f'BOOTSTRAP {field} {rep+1}/{n}',flush=True)
 ci=np.quantile(values,[.025,.975],axis=0);cc=np.quantile(corr,[.025,.975],axis=0)
 return dict(block=field,blocks=len(keys),replicates=n,crps_ratio_95ci=ci[:,0].tolist(),delta_vs_v51_95ci=ci[:,1].tolist(),oracle_capture_95ci=ci[:,2].tolist(),pearson_95ci=cc[:,0].tolist(),spearman_95ci=cc[:,1].tolist(),paired=True,refit=False)

def run_bootstrap(private,field):
 verify_pre(private);path=private/('bootstrap-'+field+'.json')
 if path.exists():print('REUSE',path);return
 rows=pd.read_parquet(private/'scored_rows.parquet');loss=np.load(private/'losses.npz');pred=np.load(private/'predictions.npz');p=pred[next(iter(MODELS))][pred['eval_mask']];b=bootstrap(rows,loss['baseline'],loss[next(iter(MODELS))],loss['oracle'],rows.delta.to_numpy(),p,field);save(path,b)
 if all((private/('bootstrap-'+f+'.json')).exists() for f in ['release_id','year']):save(OUT/'bootstrap_summary.json',{'release_block':json.loads((private/'bootstrap-release_id.json').read_text()),'year_block':json.loads((private/'bootstrap-year.json').read_text()),'IID_cell_bootstrap_not_used':True,'independent_OOS':False});status('bootstrap')

def finalize(private):
 pre=verify_pre(private);rows=pd.read_parquet(private/'scored_rows.parquet');losses=np.load(private/'losses.npz');base=losses['baseline'];loss=losses[next(iter(MODELS))];gain=base-loss;grouped={};overall=float(loss.sum()/base.sum());net=float(gain.sum())
 for field in ['release_id','year']:
  entries=[]
  for key,g in rows.groupby(field):
   ii=g.index.to_numpy();keep=np.ones(len(rows),bool);keep[ii]=False;entries.append(dict(block=str(key),cells=len(ii),gain=float(gain[ii].sum()),ratio_without_block=float(loss[keep].sum()/base[keep].sum())))
  positive=sum(max(0,x['gain']) for x in entries);rank=sorted(entries,key=lambda x:x['gain'],reverse=True)
  grouped[field]=dict(blocks=entries,total_net_gain=net,total_positive_gain=positive,top1_positive_gain_share=max(0,rank[0]['gain'])/positive if positive>0 else None,top3_positive_gain_share=sum(max(0,x['gain']) for x in rank[:3])/positive if positive>0 else None,removing_one_block_flips_improvement=overall<1 and any(x['ratio_without_block']>=1 for x in entries),removing_one_block_erases_majority_net_gain=net>0 and any(x['gain']>net/2 for x in entries))
 concentrated=any(d['removing_one_block_flips_improvement'] or d['removing_one_block_erases_majority_net_gain'] for d in grouped.values())
 save(OUT/'concentration_audit.json',{'overall_CRPS_ratio':overall,'gain_definition':'sum paired baseline normalized CRPS minus candidate normalized CRPS','groups':grouped,'CONCENTRATED':concentrated,'retraining_or_subset_selection':False})
 pred=np.load(private/'predictions.npz');p=pred[next(iter(MODELS))][pred['eval_mask']];economic=[]
 for f in FEATURES[:4]:economic.append(dict(feature=f,pearson_descriptive=float(pearsonr(rows[f],rows.delta).statistic),spearman_descriptive=float(spearmanr(rows[f],rows.delta).statistic),causal_claim=False))
 save(OUT/'economic_direction_diagnostics.json',{'descriptive_only':True,'correlations':economic,'coefficients_not_causal':True})
 score=json.loads((OUT/'primary_score_summary.json').read_text());primary=score['models'][next(iter(MODELS))];annual=pd.read_csv(OUT/'year_summary.csv');annual=annual.loc[annual.model==next(iter(MODELS))].to_dict('records');controls=json.loads((OUT/'negative_controls.json').read_text())['controls'];boot=json.loads((OUT/'bootstrap_summary.json').read_text())['release_block'];result=verdict(primary,annual,controls,boot,concentrated)
 nxt={'STRONG_YES':'SPD-TRANSFER-05','YES':'SPD-TRANSFER-05','WEAK_YES':'SPD-ROBUSTNESS-05','NO':'INFORMATION-FAILURE-REASSESSMENT-01','INCONCLUSIVE':'Assess attainable independent release count; no model-complexity increase'}[result]
 save(OUT/'final_decision.json',{'LOCATION04_RESULT':result,'DATASET_READY':True,'primary_model':next(iter(MODELS)),'primary_crps_ratio':primary['crps_ratio'],'oracle_capture':primary['oracle_capture'],'PRE_RESULT_LOCATION04_SHA':pre,'parent_result_sha':'938abb88db0dc985d8468950e169098b88ed50b9','improving_annual_folds':sum(x['crps_ratio']<1 for x in annual),'annual_folds_evaluated':len(annual),'CONCENTRATED':concentrated,'NEXT':nxt,'SPD_CLOSED':result=='NO','ECB_CLOSED':True,'SLOOS_CLOSED':True,'independent_OOS':False,'official_submission':False,'independent_alpha_validated':False,'research_signal':result in ['YES','STRONG_YES'],'secondary_ablations_do_not_rescue_primary':True})
 status('diagnostics',final_verdict=result)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--private',type=Path,required=True);ap.add_argument('--stage',choices=['release_id','year','final'],required=True);a=ap.parse_args()
 if a.stage=='final':finalize(a.private)
 else:run_bootstrap(a.private,a.stage)

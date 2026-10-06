"""Executive summary: post-hoc diagnosis of immutable crossfit predictions, without refitting."""
import argparse,json,time,math
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import theilslopes
from qfbench2_common.scoring.crps import crps_ensemble
from .common import *

def inputs(private,source):
 verify_pre(private);q=Path(private)/'diagnostic_inputs'/source;rows=pd.read_parquet(q/'ledger.parquet');data=np.load(q/'draws.npz',allow_pickle=False);return rows,data,q
def part(private,source,stage):return Path(private)/'partials'/source/(stage+'.json')
def emit(private,source,stage,d):
 save(part(private,source,stage),d);status(stage,source=source);print(f'DIAGNOSIS source={source} stage={stage} cells={d.get("cells","")} output={part(private,source,stage)}',flush=True)
def percentile(a):return {str(q):float(np.quantile(abs(a),q)) for q in [.5,.75,.9,.95,.99]}
def partition_table(rows,source,dimension='all',group='all'):
 labels=sign_partition(rows.true_delta,rows.predicted_delta);out=[]
 for balance in ['cell','release']:
  w=weights(rows,balance);b=rows.baseline_cell_CRPS.to_numpy();c=rows.candidate_cell_CRPS.to_numpy();total=np.dot(w,c-b)
  for label in ['SIGN_CORRECT','SIGN_WRONG','ZERO_TIE']:
   take=labels==label;ww=w[take];n=int(take.sum());rel=int(rows.loc[take,'release_id'].nunique());delta=c[take]-b[take]
   out.append(dict(source=source,dimension=dimension,group=group,balance=balance,partition=label,cells=n,fraction_cells=n/len(rows),fraction_weight=float(ww.sum()/w.sum()),releases_with_partition=rel,fraction_releases_nonexclusive=rel/rows.release_id.nunique(),baseline_CRPS_weighted_sum=float(np.dot(ww,b[take])),candidate_CRPS_weighted_sum=float(np.dot(ww,c[take])),crps_ratio=float(np.dot(ww,c[take])/np.dot(ww,b[take])) if n else None,mean_CRPS_change=weighted_mean(delta,ww) if n else None,total_score_damage=float(np.dot(ww,delta)),fraction_total_net_damage=float(np.dot(ww,delta)/total) if abs(total)>1e-12 else None,harmed_fraction=weighted_mean(delta>1e-12,ww) if n else None,overshoot_fraction=weighted_mean(rows.loc[take,'abs_pred_delta']>rows.loc[take,'abs_true_delta'],ww) if n else None))
 return out
def metrics_stage(private,source):
 r,data,q=inputs(private,source);balanced={b:aggregate(r,b) for b in ['cell','origin','release','year']};years=[];horizons=[];ages=[];partitions=partition_table(r,source)
 for field,out in [('year',years),('horizon',horizons)]:
  for key,g in r.groupby(field):
   for balance in ['cell','release']:
    a=aggregate(g,balance);out.append(dict(source=source,group=int(key),**a,calibration_slope=a['calibration']['slope'],calibration_intercept=a['calibration']['intercept']))
   partitions+=partition_table(g,source,field,int(key))
 for lo,hi,label in [(0,20,'0-20'),(21,40,'21-40'),(41,60,'41-60'),(61,90,'61-90'),(91,np.inf,'>90')]:
  g=r.loc[(r.source_age>=lo)&(r.source_age<=hi)]
  for balance in ['cell','release']:
   a=aggregate(g,balance) if len(g) else dict(cells=0,origins=0,releases=0,balance=balance)
   ages.append(dict(source=source,age_bin=label,**a))
 y=r.true_delta.to_numpy();p=r.predicted_delta.to_numpy();magnitude=dict(label=POSTHOC,median_abs_true=float(np.median(abs(y))),median_abs_predicted=float(np.median(abs(p))),mean_abs_true=float(np.mean(abs(y))),mean_abs_predicted=float(np.mean(abs(p))),pred_true_mean_abs_ratio=float(np.mean(abs(p))/np.mean(abs(y))),true_quantiles=percentile(y),predicted_quantiles=percentile(p),raw_center_error_quantiles=percentile(r.raw_center_error),raw_shift_quantiles=percentile(r.predicted_raw_shift),calibrations={k:v['calibration'] for k,v in balanced.items()},robust_Theil_Sen={'slope':float(theilslopes(y,p).slope),'method':'scipy.stats.theilslopes; unweighted descriptive median pair slope; never applied'} if np.ptp(p)>0 else None,fold_calibration_slopes=[{'year':s['group'],'balance':s['balance'],'slope':s['calibration_slope']} for s in years],calibration_applied=False)
 order=np.argsort(-abs(p),kind='stable');damage=r.cell_CRPS_delta.to_numpy();positive=np.maximum(damage,0).sum();net=damage.sum();extreme=[]
 for fraction in [.01,.05,.10,.20]:
  n=max(1,math.ceil(len(r)*fraction));take=order[:n];extreme.append(dict(source=source,top_fraction=fraction,cells=n,actual_fraction=n/len(r),threshold_abs_predicted_delta=float(abs(p)[take[-1]]),signed_net_damage=float(damage[take].sum()),share_total_net_damage=float(damage[take].sum()/net) if abs(net)>1e-12 else None,share_gross_positive_damage=float(np.maximum(damage[take],0).sum()/positive) if positive>0 else None,tie_rule='Exact ceil(N*fraction), stable original frozen row order; no row dropped'))
 maxima={}
 for field in ['abs_pred_delta','predicted_raw_shift']:
  ii=int(np.argmax(abs(r[field].to_numpy())));v=r.iloc[ii];maxima[field]={k:v[k] for k in ['source','asset','origin_date','year','horizon','release_id','V5.1_SD','predicted_delta','predicted_raw_shift']}
 byrelease=r.groupby('release_id').agg(cells=('asset','size'),origins=('origin_date','nunique'));repeat_ids=byrelease.index[byrelease.origins>1];economic=data['feature_values'][:,:4]
 dependence=dict(cells=len(r),origins=int(r.origin_date.nunique()),unique_releases=int(len(byrelease)),distinct_economic_feature_vectors=int(len(np.unique(economic,axis=0))),independent_release_count_upper_bound=int(len(byrelease)),cell_count_Kish_block_concentration=float(len(r)**2/np.sum(byrelease.cells.to_numpy()**2)),Kish_is_not_inference_effective_N=True,percentage_cells_in_releases_shared_by_multiple_origins=float(100*r.release_id.isin(repeat_ids).mean()),percentage_extra_origins_beyond_one_per_release=float(100*(r.origin_date.nunique()-len(byrelease))/r.origin_date.nunique()),origins_per_release=byrelease.origins.describe().to_dict(),cells_per_release=byrelease.cells.describe().to_dict(),cell_minus_release_sign_accuracy=balanced['cell']['sign_accuracy']-balanced['release']['sign_accuracy'],cell_minus_release_spearman=balanced['cell']['spearman']-balanced['release']['spearman'],release_blocks_are_not_proven_independent=True)
 nonover=(sign_partition(y,p)=='SIGN_CORRECT')&(abs(p)<=abs(y));convex=dict(sign_correct_nonovershoot_cells=int(nonover.sum()),sign_correct_nonovershoot_harmed_cells=int(((damage>1e-12)&nonover).sum()),explanation='Pure translations have constant CRPS spread term and convex absolute-error term, minimized by moving the sample median to truth. Moving toward truth without overshooting cannot worsen CRPS beyond numerical tolerance.')
 emit(private,source,'metrics',dict(cells=len(r),balanced=balanced,years=years,horizons=horizons,ages=ages,magnitude=magnitude,partitions=partitions,extreme=extreme,maxima=maxima,dependence=dependence,convexity=convex))

def fixed_transform(pred,kind,value):
 if kind=='shrinkage':return np.asarray(pred)*value
 if kind=='direction_only':return np.sign(pred)*value
 raise ValueError('Unknown diagnostic transform')
def loss_curve(draws,r,kind,value):
 pp=fixed_transform(r.predicted_delta.to_numpy(),kind,value)
 return crps_ensemble(draws+pp*r['V5.1_SD'].to_numpy(),r.truth.to_numpy(),fair=True)/r.normalization_scale.to_numpy()
def block_sensitivity(rows,baseline,loss):
 result={};gain=baseline-loss;overall=float(loss.sum()/baseline.sum())
 for field in ['release_id','year']:
  out=[]
  for key,g in rows.groupby(field):
   i=g.index.to_numpy();b=baseline.sum()-baseline[i].sum();c=loss.sum()-loss[i].sum();out.append(dict(block=str(key),gain=float(gain[i].sum()),ratio_without_block=float(c/b)))
  positive=sum(max(v['gain'],0) for v in out);rank=sorted(out,key=lambda v:v['gain'],reverse=True)
  result[field]=dict(blocks=out,largest_positive_gain_share=max(rank[0]['gain'],0)/positive if positive>0 else None,top3_positive_gain_share=sum(max(v['gain'],0) for v in rank[:3])/positive if positive>0 else None,all_leave_one_block_ratios_below_one=overall<1 and all(v['ratio_without_block']<1 for v in out))
 return result
def curves_stage(private,source):
 r,data,q=inputs(private,source);b=r.baseline_cell_CRPS.to_numpy();curve=[];losses=[];arrays={};oracle=float(data['oracle_loss'].sum()/b.sum());labels=sign_partition(r.true_delta,r.predicted_delta)
 for kind,grid in [('shrinkage',LAMBDA_GRID),('direction_only',DIRECTION_CONSTANTS)]:
  for v in grid:
   c=loss_curve(data['draws'],r,kind,v);assert np.isfinite(c).all()
   if kind=='shrinkage' and v==0.:assert np.allclose(c,b,atol=1e-12,rtol=1e-12)
   if kind=='shrinkage' and v==1.:assert np.allclose(c,r.candidate_cell_CRPS,atol=1e-12,rtol=1e-12)
   ratio=float(c.sum()/b.sum());correct=labels=='SIGN_CORRECT';sensitivity=block_sensitivity(r,b,c);robust=ratio<1 and all(x['all_leave_one_block_ratios_below_one'] and x['largest_positive_gain_share'] is not None and x['largest_positive_gain_share']<=.5 for x in sensitivity.values())
   rec=dict(source=source,kind=kind,value=v,crps_ratio=ratio,oracle_capture=(1-ratio)/(1-oracle),label=POSTHOC if kind=='shrinkage' else 'POST_HOC_DIRECTION_ONLY_DIAGNOSTIC',INVALID_FOR_CONFIRMATORY_USE=True,frozen_predictions_only=True,sign_correct_crps_ratio=float(c[correct].sum()/b[correct].sum()) if correct.any() else None,sign_wrong_crps_ratio=float(c[labels=='SIGN_WRONG'].sum()/b[labels=='SIGN_WRONG'].sum()) if (labels=='SIGN_WRONG').any() else None,robust_to_one_year_and_release=robust,primary_universe_unchanged=True)
   curve.append(rec);losses.append(c);arrays[kind+':'+str(v)]=sensitivity;print(f'CURVE {source} {kind} {v} completed={len(curve)}/13',flush=True)
  best=min([s for s in curve if s['kind']==kind],key=lambda x:x['crps_ratio']);arrays['minimum_'+kind]={'ratio':best['crps_ratio'],'argmin_grid':best['value'],'INVALID_FOR_CONFIRMATORY_USE':True}
 np.savez_compressed(q/'diagnostic_losses.npz',losses=np.asarray(losses));emit(private,source,'curves',dict(cells=len(r),curve=curve,sensitivity=arrays,oracle_ratio=oracle,selected_candidate=None,all_results_diagnostic_only=True))

def geometry_stage(private,source):
 r,data,q=inputs(private,source);r=r.copy();sd=r['V5.1_SD'];r['SD_quintile']=r.groupby(['asset','horizon'])['V5.1_SD'].rank(method='first',pct=True).mul(5).apply(np.ceil).clip(1,5).astype(int);damage=r.cell_CRPS_delta;positive=np.maximum(damage,0).sum();net=damage.sum();groups=[]
 for quintile,g in r.groupby('SD_quintile'):
  a=aggregate(g,'release');groups.append(dict(quintile=int(quintile),cells=len(g),origins=int(g.origin_date.nunique()),releases=int(g.release_id.nunique()),crps_ratio=float(g.candidate_cell_CRPS.sum()/g.baseline_cell_CRPS.sum()),release_balanced_crps_ratio=a['crps_ratio'],mean_abs_true_delta=float(g.abs_true_delta.mean()),mean_abs_pred_delta=float(g.abs_pred_delta.mean()),mean_SD=float(g['V5.1_SD'].mean()),median_SD=float(g['V5.1_SD'].median()),mean_abs_raw_error=float(abs(g.raw_center_error).mean()),mean_abs_raw_shift=float(abs(g.predicted_raw_shift).mean()),raw_CRPS_delta_sum=float(np.dot(g.cell_CRPS_delta,g.normalization_scale)),normalized_CRPS_delta_sum=float(g.cell_CRPS_delta.sum()),gross_positive_damage_share=float(np.maximum(g.cell_CRPS_delta,0).sum()/positive) if positive>0 else None,signed_net_damage_share=float(g.cell_CRPS_delta.sum()/net) if abs(net)>1e-12 else None))
 w=weights(r,'release');standard=direction_metrics(r.true_delta,r.predicted_delta,w);raw=direction_metrics(r.raw_center_error,r.predicted_raw_shift,w);rank=r.groupby(['asset','horizon'])['V5.1_SD'].rank(method='average',pct=True);relationships={field:weighted_spearman(rank,abs(r[field]),w) for field in ['true_delta','predicted_delta','raw_center_error','predicted_raw_shift','cell_CRPS_delta']}
 if not np.array_equal(np.sign(r.true_delta),np.sign(r.raw_center_error)) or not np.array_equal(np.sign(r.predicted_delta),np.sign(r.predicted_raw_shift)):raise ValueError('Positive-SD sign invariance failed')
 emit(private,source,'geometry',dict(cells=len(r),SD_quintile_method='Within each asset/horizon, rank original V5.1 SD in the full frozen evaluation set into five equal-count bins; no outcome-defined bins or dropped rows',SD_distribution=r['V5.1_SD'].describe(percentiles=[.05,.25,.5,.75,.95]).to_dict(),by_quintile=groups,release_balanced_standardized=standard,release_balanced_raw=raw,within_asset_horizon_SD_rank_spearman=relationships,positive_SD_sign_invariance=True,mechanical_identity='raw shift = frozen predicted delta * positive V5.1 SD. Smaller SD suppresses a given standardized shift; inverse-SD target normalization can affect the original training labels, but does not mechanically amplify a fixed raw shift.',normalization_scale_separate_from_V51_SD=True,target_unchanged=True))

def cosine(a,b):
 den=np.linalg.norm(a)*np.linalg.norm(b);return float(np.dot(a,b)/den) if den>0 else None
def coefficients_stage(private,source):
 r,data,q=inputs(private,source);models=json.loads((q/'models.json').read_text());by={};summaries=[]
 for m in models['models']:
  key=(m.get('asset','EUR'),m.get('horizon','POOLED'));by.setdefault(str(key),[]).append(m)
 for key,items in by.items():
  items=sorted(items,key=lambda v:v['year']);co=np.array([m['coefficient'] for m in items]);raw=np.array([m['raw_feature_coefficient'] for m in items]);sign=np.sign(co);consistency=np.maximum((sign>0).sum(axis=0),(sign<0).sum(axis=0))/len(items);pair=[cosine(a,b) for a,b in zip(co[:-1],co[1:])];rp=[cosine(a,b) for a,b in zip(raw[:-1],raw[1:])]
  summaries.append(dict(scope=key,years=[m['year'] for m in items],standardized_sign_consistency=consistency.tolist(),standardized_adjacent_cosines=pair,raw_feature_adjacent_cosines=rp,coefficient_dispersion=np.std(co,axis=0).tolist(),raw_feature_coefficient_dispersion=np.std(raw,axis=0).tolist(),original_models=items))
 years=[]
 for year,g in r.groupby('year'):
  a=aggregate(g,'release');ii=g.index.to_numpy();z=g.heldout_max_abs_train_z.to_numpy();comp=data['prediction_components'][ii];p=g.predicted_delta.to_numpy();labels=sign_partition(g.true_delta,p);damage=g.cell_CRPS_delta.to_numpy();correct=labels=='SIGN_CORRECT'
  years.append(dict(year=int(year),cells=len(g),release_balanced_metrics=a,mean_max_abs_train_z=float(np.nanmean(z)),p95_max_abs_train_z=float(np.nanquantile(z,.95)),max_train_z=float(np.nanmax(z)),fraction_heldout_cells_max_z_gt3=float(np.mean(z>3)),fraction_heldout_cells_max_z_gt5=float(np.mean(z>5)),mean_squared_train_standardized_distance=float(np.nanmean(g.heldout_mean_squared_train_z)),mean_abs_prediction_component_by_feature=np.nanmean(abs(comp),axis=0).tolist(),sign_correct_harmed_fraction=float(np.mean(damage[correct]>1e-12)) if correct.any() else None,sign_correct_overshoot_fraction=float(np.mean(abs(p[correct])>g.abs_true_delta.to_numpy()[correct])) if correct.any() else None,mean_SD=float(g['V5.1_SD'].mean()),median_SD=float(g['V5.1_SD'].median()),mean_abs_raw_shift=float(abs(g.predicted_raw_shift).mean()),median_abs_raw_shift=float(np.median(abs(g.predicted_raw_shift))),mean_abs_raw_error=float(abs(g.raw_center_error).mean()),net_damage=float(g.cell_CRPS_delta.sum()),gross_positive_damage=float(np.maximum(g.cell_CRPS_delta,0).sum()),gross_improvement=float(np.maximum(-g.cell_CRPS_delta,0).sum())))
 finite=[v for s in summaries for v in s['standardized_adjacent_cosines'] if v is not None];rf=[v for s in summaries for v in s['raw_feature_adjacent_cosines'] if v is not None];total=float(r.cell_CRPS_delta.sum());damaging=[max(y['net_damage'],0) for y in years];worst=max(years,key=lambda y:y['net_damage'])
 emit(private,source,'coefficients',dict(cells=len(r),features=models['features'],scope='Only preserved original scaler/linear coefficients; no model fit or calibration applied',coefficient_scopes=summaries,mean_standardized_adjacent_cosine=float(np.mean(finite)) if finite else None,mean_raw_feature_adjacent_cosine=float(np.mean(rf)) if rf else None,missing_model_state_cells=models['missing_model_state_cells'],years=years,worst_year=int(worst['year']),worst_year_net_damage=worst['net_damage'],worst_year_share_of_positive_annual_damage=worst['net_damage']/sum(damaging) if sum(damaging)>0 else None,worst_year_share_of_net_total_damage=worst['net_damage']/total if total>0 else None,preexisting_regime_variables_available=False,annual_labels_only=True,no_2023_exclusion=True))

def bootstrap_chunk(private,source,block,start,stop):
 r,data,q=inputs(private,source);curves=json.loads(part(private,source,'curves').read_text())['curve'];curve_losses=np.load(q/'diagnostic_losses.npz')['losses'];folder=q/'bootstrap';folder.mkdir(exist_ok=True);dest=folder/f'{block}-{start:04d}-{stop:04d}.npz'
 if dest.exists():print('REUSE',dest,flush=True);return
 field='release_id' if block=='release' else 'year';keys,ids=np.unique(r[field].astype(str),return_inverse=True);wr=weights(r,'release');y=r.true_delta.to_numpy();p=r.predicted_delta.to_numpy();b=r.baseline_cell_CRPS.to_numpy();primary=r.candidate_cell_CRPS.to_numpy();directions=[];ratios=[];source_index=['ECB','SLOOS','SPD'].index(source)
 for rep in range(start,stop):
  rng=np.random.default_rng(SEED+source_index*100000+(10000 if block=='year' else 0)+rep);counts=np.bincount(rng.integers(len(keys),size=len(keys)),minlength=len(keys));w=counts[ids].astype(float);metric=[]
  for balance in [w,w*wr]:
   d=direction_metrics(y,p,balance);metric += [d['sign_accuracy'],d['balanced_sign_accuracy'],d['pearson'],d['spearman']]
  directions.append([np.nan if v is None else v for v in metric]);den=np.dot(w,b);ratios.append(np.r_[np.dot(w,primary)/den,curve_losses@w/den])
 np.savez_compressed(dest,directions=directions,ratios=ratios);print(f'BOOTSTRAP source={source} block={block} completed={stop}/{BOOTSTRAP_REPLICATES} output={dest}',flush=True)
def bootstrap_summary(private,source):
 r,data,q=inputs(private,source);curves=json.loads(part(private,source,'curves').read_text())['curve'];out={}
 for block in ['release','year']:
  files=sorted((q/'bootstrap').glob(block+'-*.npz'));d=np.concatenate([np.load(f)['directions'] for f in files]);rat=np.concatenate([np.load(f)['ratios'] for f in files]);assert len(d)==BOOTSTRAP_REPLICATES
  names=['cell_sign_accuracy','cell_balanced_sign_accuracy','cell_pearson','cell_spearman','release_sign_accuracy','release_balanced_sign_accuracy','release_pearson','release_spearman'];ci=np.nanquantile(d,[.025,.975],axis=0)
  out[block]=dict(blocks=int(r.release_id.nunique() if block=='release' else r.year.nunique()),replicates=len(d),direction_95ci={n:ci[:,i].tolist() for i,n in enumerate(names)},primary_CRPS_ratio_95ci=np.quantile(rat[:,0],[.025,.975]).tolist(),diagnostic_curve_95ci=[dict(kind=s['kind'],value=s['value'],crps_ratio_95ci=np.quantile(rat[:,i+1],[.025,.975]).tolist(),label=POSTHOC,INVALID_FOR_CONFIRMATORY_USE=True) for i,s in enumerate(curves)],IID_cell_bootstrap=False,refit=False)
 emit(private,source,'bootstrap',dict(cells=len(r),blocks=out,seed=SEED,exposed_research_only=True))

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--private',type=Path,required=True);ap.add_argument('--source',choices=['ECB','SLOOS','SPD'],required=True);ap.add_argument('--stage',choices=['metrics','curves','geometry','coefficients','bootstrap','bootstrap_summary'],required=True);ap.add_argument('--block',choices=['release','year'],default='release');ap.add_argument('--start',type=int,default=0);ap.add_argument('--stop',type=int,default=1000);a=ap.parse_args()
 if a.stage=='bootstrap':bootstrap_chunk(a.private,a.source,a.block,a.start,a.stop)
 elif a.stage=='bootstrap_summary':bootstrap_summary(a.private,a.source)
 else:globals()[a.stage+'_stage'](a.private,a.source)

"""Executive summary: complete-ledger diagnostics and frozen decision gates; no candidate."""
import json
import numpy as np,pandas as pd
from scipy.stats import pearsonr,spearmanr
from .core import *
from .run import load

def interval(v):return np.nanquantile(v,[.025,.975]).tolist()
def asset_classification(f):
 b=bias(f);annual=f.groupby('year').direction.apply(lambda x:np.mean(x>0));count=f.groupby('year').size().to_numpy();positive=f.groupby('year').direction.apply(lambda x:np.sum(x>0)).to_numpy();rng=np.random.default_rng(SEED);ix=rng.integers(len(count),size=(5000,len(count)));ci=interval(positive[ix].sum(axis=1)/count[ix].sum(axis=1));cons=float(np.mean(annual>.5));negcons=float(np.mean(annual<.5));cl='INSUFFICIENT'if len(f)<200 or len(annual)<3 else 'POSITIVE_BIAS'if b['positive_fraction']>=.55 and ci[0]>.5 and cons>=.7 else 'NEGATIVE_BIAS'if b['positive_fraction']<=.45 and ci[1]<.5 and negcons>=.7 else 'UNSTABLE'
 return dict(classification=cl,annual_positive_consistency=cons,annual_negative_consistency=negcons,year_block_positive_CI_lower=ci[0],year_block_positive_CI_upper=ci[1])

def concentration(rows,gain):
 out={}
 for key in ['year','origin','asset','horizon','era']:
  f=pd.DataFrame({'key':rows[key].to_numpy(),'net':gain,'gross':np.maximum(gain,0)}).groupby('key').sum();gross=f.gross.sum();shares=f.gross/gross if gross>0 else f.gross*np.nan
  out[key]={'largest_gross_share':float(shares.max()),'largest_group':str(shares.idxmax())if gross>0 else None,'total_net_gain':float(f.net.sum()),'total_gross_gain':float(gross),'groups':[dict(group=str(a),gross_share=float(shares.loc[a]),net_gain=float(v.net),gross_gain=float(v.gross))for a,v in f.iterrows()]}
 out['YEAR_CONCENTRATED']=out['year']['largest_gross_share']>.5;out['ERA_CONCENTRATED']=out['era']['largest_gross_share']>.7;return out

def decide(e):
 # Numeric interpretation of the prompt's qualitative gates, fixed before broader labels.
 if all(e['global_gates'].values()):return 'PERSISTENT_GLOBAL_BIAS','V5.1-GLOBAL-BIAS-CALIBRATION-05'
 if e['global_weak'] and (all(e['asset_gates'].values())or all(e['horizon_gates'].values())):return 'STRUCTURED_BIAS','V5.1-STRUCTURED-BIAS-CALIBRATION-05'
 if all(e['episode_gates'].values()):return 'EPISODIC_REGIME_BIAS','REGIME-BIAS-IDENTIFICATION-05'
 if all(e['no_stable_gates'].values()):return 'NO_STABLE_CENTER_BIAS','ALPHA-STRATEGY-RESET-05'
 return 'INCONCLUSIVE','ALPHA-STRATEGY-RESET-05'

def aggregate():
 verify();rows=load();base=np.load(private()/'base_losses.npz');cc=np.load(private()/'chronological.npz');ev=cc['fold']>0;te=rows[ev];folds=pd.read_csv(OUT/'chronological_bias_persistence.csv');label='RESEARCH_EXPOSED / RESEARCH_DIAGNOSTIC_ONLY'
 weighted={'Cell-weighted':bias(rows),'Origin-balanced':bias(rows,weights(rows.origin)),'Year-balanced':bias(rows,weights(rows.year)),'Asset-balanced':bias(rows,weights(rows.asset)),'Asset-horizon-balanced':bias(rows,weights(rows.asset+'|'+rows.horizon.astype(str)))}
 save(OUT/'global_bias_summary.json',dict(executive_summary=label,**weighted['Cell-weighted'],raw_unit_warning='Raw pooled errors mix FX levels, rate levels and factor accumulated log returns. Units differ; standardized statistics are primary.'))
 save(OUT/'balance_weighting_summary.json',dict(executive_summary=label,group_rule='Each block receives equal total weight; all cells retained. Weighted median averages boundary values at exact half mass.',summaries=weighted))
 tables={}
 for key,name in [('year','year_bias_summary.csv'),('era','era_bias_summary.csv'),('asset','asset_bias_summary.csv'),('asset_group','asset_group_bias_summary.csv'),('horizon','horizon_bias_summary.csv')]:
  table=[]
  for group,f in rows.groupby(key,sort=True):
   entry={key:group,**bias(f)}
   if key in ['asset','horizon']:entry.update(asset_classification(f));entry['asset_positive_consistency']=float(np.mean(f.groupby('asset').direction.apply(lambda x:np.mean(x>0))>.5))
   table.append(entry)
  csv(name,table);tables[key]=pd.DataFrame(table)
 csv('asset_horizon_bias_matrix.csv',[dict(asset=a,horizon=h,**bias(f))for(a,h),f in rows.groupby(['asset','horizon'])])
 save(OUT/'year_persistence_summary.json',dict(executive_summary=label,adjacent_majority_same_fraction=float(np.mean(np.sign(tables['year'].positive_fraction.to_numpy()[1:]-.5)==np.sign(tables['year'].positive_fraction.to_numpy()[:-1]-.5))),positive_mean_year_fraction=float(np.mean(tables['year'].mean_raw_error>0)),positive_median_year_fraction=float(np.mean(tables['year'].median_raw_error>0)),positive_majority_year_fraction=float(np.mean(tables['year'].positive_fraction>.5))))
 oro={};head={}
 for universe,mask in [('full',np.ones(len(rows),bool)),('eval',ev)]:
  perfect=ratio(base['perfect'][mask],base['baseline'][mask]);items={}
  for k in ORACLES:
   loss=np.load(private()/f'oracle_{universe}_{k}.npy');v=ratio(loss[mask],base['baseline'][mask]);items[k]=dict(ratio=v,perfect_headroom_capture=capture(v,perfect),future_informed=True)
  oro[universe]=dict(cells=int(mask.sum()),origins=int(rows[mask].origin.nunique()),PERFECT_CELL_LOCATION_ORACLE=dict(ratio=perfect,perfect_headroom_capture=1.),**items)
  head[universe]=dict(perfect_headroom=1-perfect,low_dimensional_bias_headroom={k:1-v['ratio']for k,v in items.items()},low_dimensional_capture={k:v['perfect_headroom_capture']for k,v in items.items()})
 save(OUT/'bias_oracle_summary.json',dict(executive_summary='FUTURE_INFORMED_MATHEMATICAL_DIAGNOSTIC_ONLY. Normalized common CRPS loss minimization; no optimizer values enter predictive pipeline.',universes=oro))
 head['crossfit_predictable_bias_headroom']={k:1-ratio(cc[k][ev],base['baseline'][ev])for k in PREDICTIVE};head['interpretation']='Perfect-cell headroom is mathematical, never evidence of predictability.';save(OUT/'headroom_decomposition.json',head)
 conc={k:concentration(te,base['baseline'][ev]-cc[k][ev])for k in PREDICTIVE};conc['FULL_CONSTANT_UP']=concentration(rows,base['baseline']-base['up']);save(OUT/'episode_concentration.json',dict(executive_summary=label,models=conc))
 loyo=[]
 for y in sorted(rows.year.unique()):
  m=rows.year!=y;loyo.append(dict(excluded_year=int(y),**bias(rows[m]),constant_up_ratio=ratio(base['up'][m],base['baseline'][m]),constant_down_ratio=ratio(base['down'][m],base['baseline'][m])))
 csv('leave_one_year_out.csv',loyo)
 rolling=[];dates=pd.to_datetime(rows.origin);ends=pd.to_datetime(rows.target_end)
 for window in WINDOWS:
  rec=[]
  for stamp,f in rows.groupby('origin',sort=True):
   t=pd.Timestamp(stamp);m=(dates>=t-pd.DateOffset(years=window))&(dates<t-pd.offsets.BDay(189))&(ends<t)
   if not m.any():continue
   past=bias(rows[m]);future=bias(f);rec.append(dict(origin=stamp,window_years=window,history_cells=int(m.sum()),historical_positive=past['positive_fraction'],historical_mean=past['mean_standardized_error'],historical_median=past['median_standardized_error'],future_positive=future['positive_fraction'],future_mean=future['mean_standardized_error'],future_median=future['median_standardized_error']))
  pd.DataFrame(rec).to_parquet(private()/f'rolling_{window}.parquet',index=False);r=pd.DataFrame(rec)
  for metric in ['positive','mean','median']:
   a=r['historical_'+metric];b=r['future_'+metric];rolling.append(dict(window_years=window,metric=metric,origins=len(r),pearson=float(pearsonr(a,b).statistic),spearman=float(spearmanr(a,b).statistic)))
  print('rolling',window,'years complete',flush=True)
 csv('rolling_bias_summary.csv',rolling)
 narrow=pd.read_parquet(private()/'persistent-recovery/private/scored_rows.parquet');narrow=narrow.copy();narrow['raw_center_error']=narrow['truth']-narrow['median'];narrow['standardized_center_error']=narrow.raw_center_error/narrow.sd;narrow['direction']=np.sign(narrow.raw_center_error);narrow['year']=pd.to_datetime(narrow.origin).dt.year
 recent={'parent_exact':bias(narrow),'full_universe':bias(rows),'full_rates':bias(rows[rows.asset_group=='Rates']),'full_UST_2Y_5Y':bias(rows[rows.asset.isin(['UST_2Y','UST_5Y'])]),'full_2020_2024':bias(rows[rows.year>=2020]),'UST_2Y_5Y_2020_2024':bias(rows[(rows.year>=2020)&rows.asset.isin(['UST_2Y','UST_5Y'])])};save(OUT/'recent_rates_comparison.json',dict(executive_summary=label,summaries=recent))
 controls={};actual=ratio(cc['GLOBAL_BIAS_SIGN005'][ev],base['baseline'][ev])
 for kind,name in enumerate(['MATCHED_RANDOM_SIGN','HISTORICAL_YEAR_SIGN_SHUFFLE','HISTORICAL_ASSET_SIGN_SHUFFLE','HISTORICAL_HORIZON_SIGN_SHUFFLE']):
  vv=[];reps=[]
  for f in sorted((private()/'controls'/str(kind)).glob('*.npz')):z=np.load(f);vv.extend(z['ratios']);reps.extend(z['rep'])
  assert sorted(reps)==list(range(2000));v=np.asarray(vv);controls[name]=dict(replicates=len(v),median_ratio=float(np.median(v)),interval_95=interval(v),fraction_equal_or_better=float(np.mean(v<=actual+1e-14)),monte_carlo_p=float((1+np.sum(v<=actual+1e-14))/(1+len(v))),degenerate=bool(np.ptp(v)<1e-13))
 save(OUT/'negative_controls.json',dict(executive_summary='Target-blind random assignments of matured training signs; not IID significance tests.',seed=SEED,primary_ratio=actual,controls=controls,year_shuffle_clarification='Permute train-only annual signs within each fold and use the last shuffled historical sign for entire held-out fold. Never reassign future-fold fits backward.'))
 bm=['positive_fraction','mean_standardized_error','global_sign005_ratio','global_median_ratio','global_oracle_headroom_capture','global_predictive_headroom_capture','asset_sign005_ratio','horizon_sign005_ratio'];boots={}
 for kind in ['origin','year','asset']:
  vv=[];reps=[]
  for f in sorted((private()/'bootstrap'/kind).glob('*.npz')):z=np.load(f);vv.extend(z['values']);reps.extend(z['rep'])
  assert sorted(reps)==list(range(5000));v=np.asarray(vv);boots[kind]=dict(block_count=int(rows[kind].nunique()),replicates=len(v),metrics={k:dict(interval_95=interval(v[:,j]),finite_replicates=int(np.isfinite(v[:,j]).sum()))for j,k in enumerate(bm)})
 save(OUT/'bootstrap_summary.json',dict(executive_summary='Block bootstrap only. Full-ledger bias statistics; all score/capture intervals use matched 2010–2024 evaluation ledger. Fixed forecasts/oracles are resampled, not refitted.',seed=SEED,blocks=boots))
 p=weighted['Cell-weighted']['positive_fraction'];direction=np.sign(p-.5);ciO=boots['origin']['metrics']['positive_fraction']['interval_95'];ciY=boots['year']['metrics']['positive_fraction']['interval_95'];ci_support=lambda ci:(ci[0]>.5 if direction>0 else ci[1]<.5)
 global_gates=dict(material_bias=abs(p-.5)>=.05,origin_and_year_support=ci_support(ciO)and ci_support(ciY),era_consistency=int(np.sum(np.sign(tables['era'].positive_fraction-.5)==direction))>=3,heldout_improvement=actual<1,fold_majority=int(np.sum(folds.GLOBAL_BIAS_SIGN005<1))>=3,no_year_dominance=not conc['GLOBAL_BIAS_SIGN005']['YEAR_CONCENTRATED'],no_era_dominance=not conc['GLOBAL_BIAS_SIGN005']['ERA_CONCENTRATED'],controls_inferior=all(v['monte_carlo_p']<=.05 and not v['degenerate']for v in controls.values()))
 structured={}
 for key,k in [('asset','ASSET_BIAS_SIGN005'),('horizon','HORIZON_BIAS_SIGN005')]:structured[key]=dict(multiple_stable=int(tables[key].classification.isin(['POSITIVE_BIAS','NEGATIVE_BIAS']).sum())>=2,heldout_improvement=ratio(cc[k][ev],base['baseline'][ev])<1,fold_majority=int(np.sum(folds[k]<1))>=3,no_era_dominance=not conc[k]['ERA_CONCENTRATED'])
 global_weak=not(global_gates['material_bias']and global_gates['origin_and_year_support']);lowmax=max(v['perfect_headroom_capture']for k,v in oro['full'].items()if isinstance(v,dict)and k!='PERFECT_CELL_LOCATION_ORACLE');era_reverse=(tables['era'].positive_fraction.min()<.5<tables['era'].positive_fraction.max())
 e=dict(global_gates=global_gates,global_weak=global_weak,asset_gates=structured['asset'],horizon_gates=structured['horizon'],episode_gates=dict(concentration=conc['FULL_CONSTANT_UP']['ERA_CONCENTRATED']or conc['FULL_CONSTANT_UP']['YEAR_CONCENTRATED'],era_reversal=bool(era_reverse),global_history_fails=actual>=1,recent_bias=recent['parent_exact']['positive_fraction']>=.55),no_stable_gates=dict(approximately_centered=abs(p-.5)<.05 and ciO[0]<=.5<=ciO[1]and ciY[0]<=.5<=ciY[1],historical_sign_fails=actual>=1,low_dimensional_capture_small=lowmax<.1,recent_sample_bias=recent['parent_exact']['positive_fraction']-recent['full_UST_2Y_5Y']['positive_fraction']>=.05))
 verdict,nxt=decide(e);save(OUT/'final_decision.json',dict(executive_summary='Frozen baseline forensic audit. No new production candidate.',V51_BIAS04_RESULT=verdict,gate_evidence=e,independent_OOS=False,submission_readiness=False,official_reference_score=.9541,official_score_reestimated=False));save(OUT/'next_axis_decision.json',dict(executive_summary='Exactly one hypothesis for a separately frozen future study; not executed here.',NEXT=nxt,reason='Frozen gate evidence in final_decision.json; no favorable subsets or post-result redesign.'))
 status('diagnostic_aggregation','final_decision.json')

if __name__=='__main__':aggregate()

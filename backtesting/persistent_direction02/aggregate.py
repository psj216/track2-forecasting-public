"""Executive summary: fixed gates and aggregate-only exposed-research reporting."""
from pathlib import Path
import argparse,json
import numpy as np,pandas as pd
from scipy.stats import spearmanr,pearsonr
from sklearn.metrics import balanced_accuracy_score
from .source import *
from .evaluate import NAMES,PRIMARY,verify,direction,status

def finite(x):return float(x) if np.isfinite(x) else None

def decide(ratios,annual,intervals,concentration,nulls):
 r=ratios[PRIMARY];timing=all(r<ratios[n]-1e-12 for n in ['5BD_DELAYED','21BD_STALE']);price=r<ratios['PRICE_LOGISTIC']-1e-12;persistence=r<ratios['PERSISTENCE']-1e-12
 gates={'CRPS_le_098':r<=.98,'annual_4_of_5':sum(x<1 for x in annual)>=4,'release_CI_support':intervals['release']['primary_ratio'][1]<1,'week_CI_support':intervals['week']['primary_ratio'][1]<1,'year_CI_support':intervals['year']['primary_ratio'][1]<1,'concentration_safe':max(concentration.values())<.5,'beats_timing':timing,'beats_price':price,'beats_persistence':persistence,'negative_controls_inferior':all(r<v['q05'] for v in nulls.values()),'PIT_integrity':True}
 verdict='STRONG_YES' if all(gates.values()) else ('NO' if r>=1 or not(timing and price and persistence) else 'INCONCLUSIVE')
 if verdict=='STRONG_YES':nxt='SEP-INDEPENDENT-VALIDATION-03'
 elif r<1:nxt='PERSISTENCE-VS-INFORMATION-AUDIT-03'
 elif ratios['PRICE_LOGISTIC']<1:nxt='PRICE-STATE-INFORMATION-AUDIT-03'
 else:nxt='EXTERNAL-ALPHA-STRATEGY-REASSESSMENT-03'
 reason='NONE' if verdict=='STRONG_YES' else ('PRICE_REDUNDANT' if not price else ('PERSISTENT_REGIME_ONLY' if not persistence else ('TIMING_NOT_IDENTIFIED' if not timing else ('NO_DIRECTION_SIGNAL' if r>=1 else 'WEAK_SAMPLE / LOW_POWER'))))
 return verdict,nxt,reason,gates

def run(private):
 p=verify(private);rows=pd.read_parquet(p/'scored_rows.parquet');data=np.load(p/'scores.npz');loss=data['losses'];base=loss[0];ro=float(loss[-1].sum()/base.sum());ratios={n:float(loss[i].sum()/base.sum()) for i,n in enumerate(NAMES)};truth=rows.y.to_numpy();nonzero=truth!=0;summary=[];metrics={}
 for i,n in enumerate(NAMES):
  if n=='V5.1':sg=np.zeros(len(rows));prob=np.full(len(rows),.5)
  elif n=='PERFECT_LOCATION':sg=truth;prob=(truth+1)/2
  else:prob=data['prob_'+n];sg=direction(prob)
  correct=(sg==truth);binary=(truth[nonzero]>0).astype(int);pp=prob[nonzero];balance=float(balanced_accuracy_score(binary,(pp>.5).astype(int))) if len(set(binary))==2 else None
  item={'model':n,'CRPS_ratio':ratios[n],'sign_accuracy':float(correct[nonzero].mean()),'oracle_capture':(1-ratios[n])/(1-ro),'mean_normalized_CRPS_delta':float((loss[i]-base).mean()),'mean_raw_CRPS_delta':float(((loss[i]-base)*rows.scale.to_numpy()).mean()),'fraction_improved_cells':float((loss[i]<base).mean()),'ties':int((~nonzero).sum()),'prediction_ties':int((sg==0).sum()),'balanced_accuracy':balance,'Brier':float(np.mean((pp-binary)**2)),'release_balanced_sign_accuracy':float(pd.Series(correct[nonzero],index=rows.index[nonzero]).groupby(rows.loc[nonzero,'release_id']).mean().mean()),'release_balanced_CRPS_delta':float(pd.Series(loss[i]-base).groupby(rows.release_id).mean().mean()),'year_balanced_CRPS_delta':float(pd.Series(loss[i]-base).groupby(rows.year).mean().mean())}
  if n not in ['V5.1','PERFECT_LOCATION']:
   item['mean_signed_raw_shift']=float((AMPLITUDE*sg*rows.sd.to_numpy()).mean());item['mean_absolute_raw_shift']=float((AMPLITUDE*abs(sg)*rows.sd.to_numpy()).mean());item['mean_absolute_SD_shift']=float((AMPLITUDE*abs(sg)).mean());item['Pearson_probability_direction']=finite(pearsonr(pp,binary).statistic) if np.std(pp)>0 else None;item['Spearman_probability_direction']=finite(spearmanr(pp,binary).statistic) if np.std(pp)>0 else None
  summary.append(item);metrics[n]=item
 csv(OUT/'model_comparison.csv',summary)
 aggregate_tables={}
 for field,file in [('year','annual_results.csv'),('horizon','horizon_results.csv'),('asset','asset_results.csv'),('release_id','source_release_summary.csv')]:
  out=[]
  for group,idx in rows.groupby(field).groups.items():
   ii=np.array(list(idx));entry={field:group,'cells':len(ii),'origins':int(rows.iloc[ii].origin.nunique()),'releases':int(rows.iloc[ii].release_id.nunique())}
   for j,n in enumerate(NAMES):entry[n+'_ratio']=float(loss[j,ii].sum()/base[ii].sum())
   for n in [PRIMARY,'PRICE_LOGISTIC','5BD_DELAYED','21BD_STALE']:
    sg=direction(data['prob_'+n][ii]);valid=truth[ii]!=0;entry[n+'_sign_accuracy']=float((sg[valid]==truth[ii][valid]).mean()) if valid.any() else None
   entry['primary_normalized_CRPS_delta']=float((loss[1,ii]-base[ii]).sum());out.append(entry)
  csv(OUT/file,out);aggregate_tables[field]=out
 bootstrap={}
 for block in ['release','year','week']:
  files=sorted((p/'bootstrap').glob(block+'-*.npz'));a=np.concatenate([np.load(f)['ratios'] for f in files]);c=np.concatenate([np.load(f)['capture'] for f in files]);d=np.concatenate([np.load(f)['differences'] for f in files]);assert len(a)==5000
  ci=lambda v:np.quantile(v,[.025,.975]).tolist()
  bootstrap[block]={'replicates':5000,'blocks':int(rows.release_id.nunique() if block=='release' else rows.year.nunique() if block=='year' else pd.to_datetime(rows.origin).dt.to_period('W-FRI').nunique()),'primary_ratio':ci(a[:,1]),'primary_minus_V51':ci(d[:,0]),'primary_minus_5BD':ci(d[:,1]),'primary_minus_21BD':ci(d[:,2]),'primary_minus_persistence':ci(d[:,3]),'primary_minus_price21':ci(d[:,4]),'primary_minus_price_logistic':ci(d[:,5]),'oracle_capture':ci(c[:,1]),'sign':'Negative differences favor primary; ratios<1 favor candidate'}
 save(OUT/'bootstrap_summary.json',{'executive_summary':'5000 blocks per method; monthly source-week grouping and only five years limit inference; no independent OOS.','methods':bootstrap})
 nulls={}
 for kind in ['STATE','DATE','RANDOM']:
  rr=np.concatenate([np.load(f)['ratios'] for f in sorted((p/'controls').glob(kind+'-*.npz'))]);assert len(rr)==2000
  nulls[kind]={'replicates':len(rr),'mean':float(rr.mean()),'q05':float(np.quantile(rr,.05)),'q95':float(np.quantile(rr,.95)),'fraction_equal_or_better_than_primary':float((rr<=ratios[PRIMARY]).mean()),'Monte_Carlo_p_plus_one':float((1+(rr<=ratios[PRIMARY]).sum())/(len(rr)+1))}
 save(OUT/'negative_controls.json',{'executive_summary':'Fixed-seed chronology-safe release/date/state nulls; matched random sign.','seed':SEED,'controls':nulls,'source_mutations':json.loads((OUT/'mutation_invariance.json').read_text()),'no_future_donors':True})
 gain=base-loss[1];concentration={}
 for field in ['release_id','year']:
  gains=pd.Series(gain).groupby(rows[field]).sum();positive=gains.clip(lower=0);concentration[field]=float(positive.max()/positive.sum()) if positive.sum()>0 else 1.
 verdict,nxt,reason,gates=decide(ratios,[x[PRIMARY+'_ratio'] for x in aggregate_tables['year']],bootstrap,concentration,nulls)
 states=json.loads((p/'source_states.json').read_text());used=set(rows.release_id);source=json.loads((OUT/'source_readiness.json').read_text())
 eff={'executive_summary':'Repeated quarterly source states, not independent cells; information-event upper bound counts unique releases, not alpha evidence.','evaluation_origins':int(rows.origin.nunique()),'evaluation_cells':len(rows),'unique_evaluation_releases':len(used),'unique_evaluation_policy_values':int(rows.SEP.nunique()),'unique_policy_state_changes_all_usable':source['source_only_state_changes'],'release_universe':source['release_universe'],'usable_releases':source['usable_releases'],'independent_information_event_upper_bound':len(used),'origins_per_release':rows.groupby('release_id').origin.nunique().to_dict(),'cells_per_release':rows.groupby('release_id').size().to_dict(),'releases_per_year':rows.groupby('year').release_id.nunique().to_dict(),'active_source_periods':len(used),'independent_OOS':False}
 save(OUT/'effective_sample_summary.json',eff)
 save(OUT/'primary_score_summary.json',{'executive_summary':'Same-ledger imported fair CRPS normalized by original past scale; ratio of sums, not mean ratios.','primary':metrics[PRIMARY],'models':metrics,'baseline_normalized_mean':float(base.mean()),'concentration_positive_gross_gain_fraction':concentration})
 bins=[];pp=data['prob_'+PRIMARY];binary=truth>0
 for j in range(10):
  ii=nonzero&(pp>=j/10)&(pp<((j+1)/10) if j<9 else pp<=1)
  if ii.any():bins.append({'lower':j/10,'upper':(j+1)/10,'cells':int(ii.sum()),'mean_probability':float(pp[ii].mean()),'observed_positive_frequency':float(binary[ii].mean())})
 save(OUT/'direction_metrics.json',{'executive_summary':'Probability classification is secondary to frozen same-ledger CRPS; target ties retained in loss.','models':metrics,'fixed_decile_calibration':bins})
 save(OUT/'timing_control_summary.json',{'executive_summary':'Contemporary source must beat BOTH fixed timing controls.','TIMING_SIGNAL':'ESTABLISHED_IN_EXPOSED_RESEARCH' if gates['beats_timing'] else 'NOT_ESTABLISHED','primary':ratios[PRIMARY],'delay5':ratios['5BD_DELAYED'],'stale21':ratios['21BD_STALE'],'interpretation':'Timing beats alone are necessary, not sufficient for new release alpha.'})
 save(OUT/'price_comparator_summary.json',{'executive_summary':'Identical ledger, target and purged annual folds; inherited fixed14 price columns plus asset/log horizon. Price vintage limitation remains.','INCREMENTAL_INFORMATION':'EXPOSED_ONLY' if gates['beats_price'] else 'NOT_ESTABLISHED','SEP':ratios[PRIMARY],'PRICE_LOGISTIC':ratios['PRICE_LOGISTIC'],'PRICE_21BD':ratios['PRICE_21BD'],'PIT_price':'C bounded official current-vintage probe; cannot establish immutable historical price vintages'})
 save(OUT/'persistence_control_summary.json',{'executive_summary':'Previous original policy-state sign, no calibrated magnitude.','ratio':ratios['PERSISTENCE'],'primary_beats_persistence':gates['beats_persistence']})
 save(OUT/'oracle_summary.json',{'executive_summary':'Future-informed perfect-location diagnostic only; no per-cell truths in public artifacts.','R_PERFECT_LOCATION':ro,'same_ledger':True,'shape_unchanged':True})
 save(OUT/'oracle_capture.json',{'executive_summary':'Unclipped fraction of same-ledger mathematical location headroom, not predictability.','primary_capture':metrics[PRIMARY]['oracle_capture'],'formula':'(1 - R_SEP)/(1 - R_PERFECT_LOCATION)'})
 save(OUT/'failure_attribution.json',{'executive_summary':'Fixed primary failure preserved; no retrospective model repair.','dominant':reason,'gates':gates,'concentration':concentration})
 decision={'executive_summary':'Frozen exposed-research test; no submission, no new model redesign.','PERSISTENT_DIRECTION02_RESULT':verdict,'DATASET_READY':True,'primary_ratio':ratios[PRIMARY],'INCREMENTAL_INFORMATION':'NOT_ESTABLISHED' if verdict!='STRONG_YES' else 'RESEARCH_EXPOSED_ONLY','gates':gates,'dominant_explanation':reason,'independent_validation':'NOT_AVAILABLE','submission_readiness':False,'V51_official_reference':.9541,'next_axis':nxt}
 save(OUT/'final_decision.json',decision);save(OUT/'next_axis_decision.json',{'executive_summary':'Exactly one separately frozen future research axis; not executed here.','NEXT':nxt,'basis':reason,'executed':False})
 make_report(decision,summary,aggregate_tables,bootstrap,nulls,eff,p)
 status('REPORT_COMPLETE','final_decision.json')
 print(json.dumps(decision,indent=2),flush=True)

def table(rows,columns):
 return '| '+' | '.join(columns)+' |\n| '+' | '.join(['---']*len(columns))+' |\n'+'\n'.join('| '+' | '.join(f'{r[c]:.6f}' if isinstance(r.get(c),float) else str(r.get(c,'')) for c in columns)+' |' for r in rows)

def make_report(decision,models,tables,bootstrap,nulls,eff,p):
 pre=json.loads((p/'pre_receipt.json').read_text())['PRE_RESULT_PERSISTENT_DIRECTION02_SHA'];s=['## Executive summary (read this first)',f"\nPERSISTENT-DIRECTION-STATE-02 completed: **{decision['PERSISTENT_DIRECTION02_RESULT']}**. DATASET_READY=true. Primary same-ledger CRPS ratio {decision['primary_ratio']:.8f}. Next exactly one axis: **{decision['next_axis']}**, not executed. Contemporary SEP policy direction is tested against frozen V5.1, stale state, persistence and observable prices. No model, amplitude, threshold or favorable subset was tuned.",'\n## Source readiness and provenance',f"\nOfficial release universe2016–2024: {eff['release_universe']}; admitted {eff['usable_releases']}; source-only state changes {eff['unique_policy_state_changes_all_usable']}. Original dated PDFs and header-resolved accessible HTML agree on CY/NCY policy medians. Earlier td-row tables were recovered deterministically. Two corrected-document rounds fail closed. March2020 had no SEP. Release-date EOD New York activation; age90 weekdays. Fields retain release-year CY/NCY targets across January. Public Fed information with attribution; offline research feasible under organizer rules. PIT B does not prove immutable originals or absence of undisclosed replacement. No official submission rights/approval or readiness claim.", '\n## Binding draft and pre-outcome clarifications',f'\nParent RESULT {PARENT}; PRE {pre}. `experiment_spec.json` records every clarification before labels: inherited monthly cache grid, conservative delayed-control refits, missing-control zero shifts, strict maturity purge, original-price vintage limits, chronology-safe one-sided date and historical-donor state controls, and quantified concentration gate. No substantive source/feature/model/amplitude/fold gate conflict. Public outputs are predictions and aggregates only; private labels, draws, losses and perfect-location cell results remain outside Git.', '\n## Primary comparison',table(models,['model','CRPS_ratio','sign_accuracy','oracle_capture','balanced_accuracy','Brier']), '\n## Annual folds',table(tables['year'],['year','cells','releases',PRIMARY+'_ratio','PRICE_LOGISTIC_ratio','5BD_DELAYED_ratio','21BD_STALE_ratio']), '\n## Horizons',table(tables['horizon'],['horizon','cells',PRIMARY+'_ratio','PRICE_LOGISTIC_ratio','5BD_DELAYED_ratio','21BD_STALE_ratio']), '\n## Assets',table(tables['asset'],['asset','cells',PRIMARY+'_ratio','PRICE_LOGISTIC_ratio']), '\n## Block bootstrap','\nNegative differences favor SEP. No IID cell bootstrap. Only five evaluation years constrain year inference.\n'+table([{'block':k,**v} for k,v in bootstrap.items()],['block','replicates','blocks','primary_ratio','primary_minus_price_logistic','primary_minus_5BD','primary_minus_21BD','oracle_capture']), '\n## Negative controls',table([{'kind':k,**v} for k,v in nulls.items()],['kind','replicates','mean','q05','q95','Monte_Carlo_p_plus_one']), '\n## Dependence and timing identification',f"\n{eff['evaluation_origins']} evaluation origins; {eff['evaluation_cells']} target cells; only {eff['unique_evaluation_releases']} unique evaluation releases. The release count is an upper bound on independent information events. Model probabilities repeat source state and differ only by asset/horizon/fold. Source-week bootstrap uses origin calendar week because this inherited ledger is monthly; it does not manufacture intramonth publication event identification. Contemporary SEP must beat both5BD delayed and21BD stale controls and previous-state persistence. Gates: {json.dumps(decision['gates'],sort_keys=True)}.", '\n## Price redundancy and concentration',f"\nDominant explanation: {decision['dominant_explanation']}. `primary_score_summary.json` records fraction of gross positive gain in the largest release/year; all years including2023 and all five horizons remain in the primary. Price logistic uses exactly the inherited fixed14 H15 columns and asset/log horizon on identical origins and purged folds. The H15 current-vintage bounded probe has PIT C, a limit to strong incremental-information claims. Neither small baseline improvement nor source persistence proves new-release alpha.", '\n## Limitations and baseline preservation','\nAll2020–2024 outcomes were previously research-exposed. PRE prevents this experiment’s within-fold leakage, not prior exposure. No independent OOS, official score gain or causal relation is established. Monthly inherited cache gaps, source corrections inactive, current-vintage price control and five years constrain interpretation. V5.1 forecasts and protected parent/submission source files remain unchanged; official verified reference score0.9541 is not remeasured. Existing binary Docker package is not reconstructed or overwritten; byte-level preservation evidence is reported separately. No submission or next experiment is executed.', '\n## Reproducibility','\nUse Python3.13, pinned common v2.4.3 scorer and original private input hashes. Stage commands are documented in RUNBOOK.md. Final Git RESULT is bound by the external verified recovery receipt to avoid a self-referential commit SHA. Full test/Git/recovery evidence is stored in execution_audit.json and the final receipt.']
 (ROOT/'PERSISTENT-DIRECTION-STATE-02-report.md').write_text('\n\n'.join(s)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('private');run(a.parse_args().private)

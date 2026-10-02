"""## Executive summary (read this first)
Publish aggregates only after all frozen card/family/chronological chunks exist; no public answers.
"""
import argparse,csv,json,time
from pathlib import Path
import numpy as np
from qfbench2_track_forecasting.ceiling01.scorer_adapter import aggregate
from qfbench2_track_forecasting.context01.context_schema import TOPICS,CONDITIONALITY,asset_group,horizon_bin
from .freeze_annotations import dump,digest,verify
from .card_block_crossfit import checked_labels
from .text_effect_audit import MAIN_MODELS,MODELS
from .diagnostics import summarize,skill,capture,success
from .evaluate_multi import f1_safety
from .bootstrap_cards import bootstrap,paired

def write_csv(path,rows):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r)),lineterminator='\n');w.writeheader();w.writerows(rows)
def scalar_metrics(records,key):
 d=summarize(records,key)
 if records:
  d.update(skill(np.concatenate([c['residual_delta']for c in records]),np.concatenate([c['prediction'][key]for c in records])))
  d['cap_hits']=int(sum(sum(abs(v)>=10 for v in c['prediction'][key])for c in records))
 return d
def load_mode(private,mode,cards,expected):
 found=[json.loads(f.read_text())for f in sorted((private/'scored').glob(mode+'_card*.json'))]
 assert len(found)==len(expected) and {c['card_id']for c in found}==set(expected),'Incomplete '+mode
 return found

def run(root,private,card_private,pre):
 cards,_=checked_labels(root,private,card_private,pre);protocol=json.loads((root/'backtesting/context01/frozen_protocol.json').read_text());r=root/'backtesting/context01/results';annotations=json.loads((r/'context_annotations.json').read_text())['cards'];cardmap={c['id']:c for c in cards};families=['T2-F'+str(i)for i in range(1,5)];ids=[c['id']for c in cards]
 data=load_mode(private,'loco',cards,ids);fho=load_mode(private,'family',cards,ids);chronids=[c for s in protocol['chronological_splits']for c in s['test_cards']];chrono=load_mode(private,'chrono',cards,chronids)
 assert all(c['pre_result_sha']==pre for c in data+fho+chrono)
 allm={k:scalar_metrics(data,k)for k in MAIN_MODELS};single={k:scalar_metrics([c for c in data if c['single']],k)for k in MAIN_MODELS};multi={k:scalar_metrics([c for c in data if not c['single']],k)for k in MAIN_MODELS}
 family={f:{k:scalar_metrics([c for c in data if c['family']==f],k)for k in MAIN_MODELS}for f in families};fhom={f:{k:scalar_metrics([c for c in fho if c['family']==f],k)for k in MAIN_MODELS}for f in families}
 y=np.concatenate([c['text_effect']['numeric_oracle_delta']for c in data]);p=np.concatenate([c['text_effect']['z_shift']for c in data]);te=skill(y,p)
 nr=aggregate([c['models']['B_NUMERIC']['ratio']for c in data]);tr=aggregate([c['models']['TEXT_LOCATION']['ratio']/c['models']['B_NUMERIC']['ratio']for c in data]);npf=aggregate([c['text_effect']['numeric_perfect_location']['ratio']/c['models']['B_NUMERIC']['ratio']for c in data]);tc=capture(tr,npf)
 textstatus='POSITIVE'if 1/nr<1 and tr<=.97 and tc is not None and tc>.05 and (te['pearson']or 0)>0 and (te['spearman']or 0)>0 else ('WEAK'if 1/nr<1 or(tr<1 and tc is not None and tc>0 and(te['pearson']or 0)>0)else'NONE')
 def textgroup(recs):
  if not recs:return dict(status='NOT_ACTIVE',cards=0)
  out=skill(np.concatenate([c['text_effect']['numeric_oracle_delta']for c in recs]),np.concatenate([c['text_effect']['z_shift']for c in recs]));out.update(cards=len(recs),full_text_over_numeric_fixed_composite=aggregate([1/c['models']['B_NUMERIC']['ratio']for c in recs]),pure_text_location_over_numeric_fixed_composite=aggregate([c['models']['TEXT_LOCATION']['ratio']/c['models']['B_NUMERIC']['ratio']for c in recs]))
  return out
 text=dict(status=textstatus,overall=te,full_text_over_numeric_fixed_composite=1/nr,pure_text_location_over_numeric_fixed_composite=tr,numeric_perfect_location_over_numeric=npf,pure_location_capture_fraction=tc,components={k:summarize(data,k)for k in ['B_NUMERIC','TEXT_LOCATION']},single=textgroup([c for c in data if c['single']]),multi=textgroup([c for c in data if not c['single']]),family={f:textgroup([c for c in data if c['family']==f])for f in families},horizon={h:textgroup([c for c in data if h in [horizon_bin(v)for v in cardmap[c['card_id']]['horizons']]])for h in ['1-5','6-21','22-63','64-126','127+']},group={g:textgroup([c for c in data if g in [asset_group(a,cardmap[c['card_id']]['target_type'])for a in cardmap[c['card_id']]['assets']]])for g in ['FX','Rates','Factor/Equity']},ratio_convention='Composite ratios use unchanged B_TEXT component denominators for both candidates; marginal ratio is separately available. Subgroup horizon memberships can overlap.')
 dump(r/'text_effect_summary.json',text)
 oracle={}
 for name,recs in [('all',data),('single',[c for c in data if c['single']]),('multi',[c for c in data if not c['single']])]+[(f,[c for c in data if c['family']==f])for f in families]:
  oracle[name]=dict(cards=len(recs),B_TEXT_composite_ratio=1.,B_NUMERIC=summarize(recs,'B_NUMERIC'),perfect_residual_location_composite_ratio=aggregate([c['oracle']['ratio']for c in recs]),perfect_residual_location_marginal_ratio=aggregate([c['oracle']['marginal']/c['baseline']['marginal']for c in recs]),baseline_component_means={k:float(np.mean([c['baseline'][k]for c in recs]))for k in ['marginal','joint','tail']},perfect_component_means={k:float(np.mean([c['oracle'][k]for c in recs]))for k in ['marginal','joint','tail']})
  joint=[c for c in recs if c['location_joint_oracle']is not None]
  oracle[name]['feasible_location_joint_composite_ratio']=aggregate([c['location_joint_oracle']['ratio']for c in joint])if joint else None
 dump(r/'residual_oracle_summary.json',dict(scope='Recomputed current24-card B_TEXT center residual oracle, uncapped hindsight; joint permutation12000proposals/3starts for11multi only; not learned forecasts',groups=oracle))
 dump(r/'semantic_crossfit_summary.json',dict(models={k:allm[k]for k in MAIN_MODELS if k.startswith('B')},fit='LOCO24; alpha innerLOCOtrainingcards only; no intercept; all63cells heldout once',fold_hashes={f.name:digest(f)for f in (private/'crossfit').glob('*.npz')},pre_result_sha=pre,embedding_status='NOT_AVAILABLE'))
 coverage=dict(active_cells=sum(c['route']['active_cells']for c in data),total_cells=63,active_cards=sum(c['route']['active_cells']>0 for c in data),total_cards=24,available_expert_cells={})
 from qfbench2_track_forecasting.context01.context_router import EXPERTS
 for j,k in enumerate(EXPERTS):
  count=0
  for i in range(24):
   with np.load(private/'experts'/f'card{i:02d}.npz')as z:count+=int(z['available'][j].sum())
  coverage['available_expert_cells'][k]=count
 coverage['coverage_fraction']=coverage['active_cells']/63
 dump(r/'routed_summary.json',dict(models={k:allm[k]for k in MAIN_MODELS if k.startswith('R')},coverage=coverage,source_limit='Continuous numeric-baseline experts transferred to B_TEXT SD without card recalibration; no same-card label fits; no direct F mapping outside MKT',r3='Fixed50/50B5andR2'))
 dump(r/'single_summary.json',dict(models=single,scope='All13single cards'))
 safety={k:f1_safety([c for c in data if c['family']=='T2-F1'],k)for k in MAIN_MODELS}
 dump(r/'multi_summary.json',dict(models=multi,F1=family['T2-F1'],F1_safety=safety,scope='All11multi cards; all joint/tail/composite rescored'))
 write_csv(r/'family_summary.csv',[dict(family=f,model=k,**family[f][k])for f in families for k in MAIN_MODELS]);write_csv(r/'family_holdout.csv',[dict(family=f,model=k,**fhom[f][k])for f in families for k in MAIN_MODELS])
 write_csv(r/'chronological_card_summary.csv',[dict(boundary=s['boundary'],model=k,training_cards=len(s['train_cards']),**scalar_metrics([c for c in chrono if c['card_id']in s['test_cards']],k))for s in protocol['chronological_splits']for k in MAIN_MODELS])
 for file,tags,selector in [('context_type_summary.csv',CONDITIONALITY,lambda c,t:annotations[c['card_id']]['features'][t]>0),('topic_summary.csv',TOPICS,lambda c,t:t in annotations[c['card_id']]['economic_topics']),('horizon_summary.csv',['1-5','6-21','22-63','64-126','127+'],lambda c,t:t in [horizon_bin(v)for v in cardmap[c['card_id']]['horizons']]),('group_summary.csv',['FX','Rates','Factor/Equity'],lambda c,t:t in [asset_group(a,cardmap[c['card_id']]['target_type'])for a in cardmap[c['card_id']]['assets']])]:
  rows=[dict(subgroup=t,model=k,**scalar_metrics([c for c in data if selector(c,t)],k))for t in tags for k in MAIN_MODELS]
  write_csv(private/'subgroups'/file,rows)
  public_rows=[dict(subgroup=row['subgroup'],model=row['model'],cards=1,cells=row['cells'],status='SUPPRESSED_SINGLE_CARD_PUBLIC_FIREWALL')if row['cards']==1 else row for row in rows]
  write_csv(r/file,public_rows)
 boots={};controls={};clear={};fam=np.array([c['family']for c in data]);sing=np.array([c['single']for c in data])
 for k in MAIN_MODELS:
  values=[c['models'][k]['ratio']for c in data];marg=[c['models'][k]['marginal']/c['baseline']['marginal']for c in data];boots[k]={name:bootstrap(values,marg,sing,fam,strat)for name,strat in [('whole_card',False),('family_stratified',True)]}
  if k in ['B0','R0']:continue
  names=['CTRL_'+n+'_'+k for n in ('ABD'if k.startswith('B')else'ABCD')];controls[k]={}
  for n in names:
   cv=[c['models'][n]['ratio']for c in data];ci=paired(values,cv,fam);cs=paired(values,cv,fam,True);controls[k][n]=dict(aggregate=summarize(data,n),candidate_over_control=aggregate((np.array(values)/cv).tolist()),whole_card_paired95=ci,family_stratified_paired95=cs,clear=ci[1]<1 and cs[1]<1)
  clear[k]=all(v['clear']for v in controls[k].values());print(json.dumps(dict(stage='aggregate5000bootstrap',model=k,clear=clear[k],artifact=str(r/'bootstrap_summary.json'))),flush=True)
  dump(private/'partial_aggregate.json',dict(bootstrap=boots,controls=controls))
 dump(r/'bootstrap_summary.json',dict(models=boots,interpretation='Previously exposed24cards;5000whole-card and5000family-stratified resampling sensitivity; not formal generalization CI'))
 dump(r/'negative_controls.json',dict(controls=controls,all_applicable_controls_clear=clear,guards=dict(E='Label mutation tests passed; annotations/router/source experts do not read card truth',F='Matched experts fitted before card truth, continuous history only; semantic heldout-label mutation passes',G='Future source mutation tests pass for survey/event/quantity queries',H='Every learned candidate preserves original paired centered draw geometry'),limitation='A rotates semantic features within family, B rotates topics; D keeps structure/time/numbers. B1 identical controls do not establish semantic specificity. C cyclic wrong experts may be unavailable and return zero.'))
 verdict={}
 for k in MAIN_MODELS:
  if k in ['B0','R0']:continue
  v=success(allm[k],single[k],multi[k],[fhom[f][k]['geometric_composite_ratio']for f in families],clear[k])
  if v=='MOONSHOT'and(safety[k]!='POSITIVE' or multi[k]['geometric_composite_ratio']>=1):
   v='STRONG_YES'if allm[k]['geometric_composite_ratio']<=.9 and allm[k]['oracle_capture_fraction']>=.2 and all(fhom[f][k]['geometric_composite_ratio']<1 for f in families)else'YES'
  verdict[k]=v
 def signal(keys):
  if any(verdict[k]!='NO'for k in keys):return 'POSITIVE'
  if any(allm[k]['geometric_composite_ratio']<1 and(allm[k]['oracle_capture_fraction']or 0)>0 and sum(fhom[f][k]['geometric_composite_ratio']<1 for f in families)>=2 for k in keys):return 'WEAK'
  return 'NONE'
 sem=signal(['B'+str(i)for i in range(1,6)]);rout=signal(['R1','R2','R3']);accepted=[k for k,v in verdict.items()if v!='NO'];path=[k for k in verdict if safety[k]=='CONTEXT_LOCATION_SIGNAL_BUT_PATH_REQUIRED'and allm[k]['marginal_ratio']<=.97]
 result=max((verdict[k]for k in accepted if k.startswith('B')),key=lambda v:['NO','WEAK_YES','YES','STRONG_YES','MOONSHOT'].index(v),default='NO')
 if result=='NO'and any(k.startswith('R')for k in accepted):result='ROUTING_ONLY_SIGNAL'
 nextstep='CONTEXT-VALIDATION-REQUIRED'if any(v in ['YES','STRONG_YES','MOONSHOT']for v in verdict.values())else('PATH-01'if path else('CONTEXT-02'if any(k.startswith('B')for k in accepted)else('CONTEXT-ROUTER-02'if accepted else('TEXT-ROUTE-AUDIT-02'if textstatus!='NONE'else'HIGHFREQ-01'))))
 decision=dict(CONTEXT01_RESULT=result,EXISTING_TEXT_SIGNAL=textstatus,SEMANTIC_RESIDUAL_SIGNAL=sem,ROUTING_SIGNAL=rout,EMBEDDING_SIGNAL='NOT_AVAILABLE',F1_MULTI_SAFETY=safety,READY_FOR_CONTEXT02='YES'if accepted else'NO',READY_FOR_ONE_SHOT='NO',NEXT_STEP_PRIORITY=nextstep,model_verdicts=verdict,evidence_label='RESEARCH_EXPOSED_CONTEXT_SIGNAL',scope='24previously exposed proxycards; no official or independent OOS validation',pre_result_sha=pre,parent_result_sha=protocol['parent_result_sha'],universe=dict(cards=24,cells=63,single=13,multi=11,family_cards=6))
 dump(r/'final_decision.json',decision)
 report=['## Executive summary (read this first)','',f"CONTEXT-01 result: **{result}**. Existing text: {textstatus}; semantic residual: {sem}; routing: {rout}. Next: **{nextstep}**. One-shot readiness: **NO**. All evidence is RESEARCH_EXPOSED_CONTEXT_SIGNAL on previously exposed proxy cards.",'',f"Branch: track2/context-01-card-semantic-location. Parent RESULT: `{protocol['parent_result_sha']}`. Verified PRE_RESULT_CONTEXT01_SHA: `{pre}`. RESULT SHA is recorded in the external completion receipt to avoid a self-referential commit hash.",'','All24cards,63cells,13single/11multi,6cards per family. B_TEXT is the frozen V5.1 text-enabled baseline. Learned forecasts only add a bounded10SD shift, preserving every centered draw, pairing, tail and covariance. No card was excluded. No embedding checkpoint was available.','',f"Current B_TEXT residual-location oracle composite: {oracle['all']['perfect_residual_location_composite_ratio']:.6f}; multi oracle: {oracle['multi']['perfect_residual_location_composite_ratio']:.6f}; multi feasible location+joint oracle: {oracle['multi']['feasible_location_joint_composite_ratio']:.6f}.",f"Existing full text/numeric fixed composite: {1/nr:.6f}; pure text location/numeric: {tr:.6f}; purelocation capture: {tc}. Numeric-center delta correlation Pearson {te['pearson']}, Spearman {te['spearman']}, sign {te['sign_accuracy']}, slope {te['calibration_slope']}.",'','|Model|Composite|Marginal|Capture|R²|Spearman|Sign|Single|Multi|Wins/24|Gate|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
 for k in MAIN_MODELS:
  d=allm[k];fmt=lambda v:'NA'if v is None else f'{v:.4f}'
  report.append('|'+ '|'.join([k,*[fmt(d[v])for v in ['geometric_composite_ratio','marginal_ratio','oracle_capture_fraction','delta_r2','spearman','sign_accuracy']],fmt(single[k]['geometric_composite_ratio']),fmt(multi[k]['geometric_composite_ratio']),str(d['card_wins']),verdict.get(k,'BASELINE')])+'|')
 report.extend(['',f"Router coverage: {coverage['active_cells']}/63cells,{coverage['active_cards']}/24cards. R1 picks the first available fixed-priority eligible source; R2 equally averages eligible sources; R3 is exactly50/50B5/R2. Source-family models use matured continuous-history labels, never card labels. Exact unmatched horizons are not snapped; transfer targets originally used a numeric baseline and receive no card calibration.",'','LOCO holds each complete card out. Alpha uses inner card-blocked delta MSE. Four family holdouts use18training/6testcards. Three chronological six-card test batches use5/11/18earlier matured training cards,189BDorigin embargo and no target overlap. All are exposed-sample diagnostics. All39candidate/control/numeric/text-location variants are fully rescored on each scored card.','',f"F1 safety: {json.dumps(safety,sort_keys=True)}.",'','|Model|F1 FHO|F2 FHO|F3 FHO|F4 FHO|Controls clear|Whole-card95 composite|Stratified95 composite|','|---|---:|---:|---:|---:|---|---|---|'])
 for k in MAIN_MODELS:
  report.append('|'+ '|'.join([k,*[f"{fhom[f][k]['geometric_composite_ratio']:.4f}"for f in families],str(clear.get(k,'NA')),str(boots[k]['whole_card']['composite_95_interval']),str(boots[k]['family_stratified']['composite_95_interval'])])+'|')
 report.extend(['','Bootstrap:5000whole-card and5000six-per-family resamples, seed1903, including composite/marginal/single/multi intervals. These measure exposed-sample sensitivity and do not support formal generalization intervals. Every applicable A/B/Dcontrol, plus Cforrouting, must have candidate/control upper95<1 under both resampling schemes to clear specificity. No selection, weights or taxonomy changed after outcomes.','', 'Negative controls preserve whole cards and target structure. E/F/G/Hguard tests pass. Structural B1 has identical permutation controls, hence cannot establish semantic specificity. Wrong-expert permutation may encounter unavailable sources, so this control also changes effective availability. No-route returns exactzero. Source timestamps and maturity are guarded.','', 'Public artifacts contain aggregate metrics and hashes only. Card truth, predictions, per-card scores, expert pickles, annotation texts and all fit logs remain in the private recovery package. The report and code import the pinned common scorer; no scoring formula was reimplemented. Main was not changed.','', 'Deterministic context features can miss relationships; weak or absent results here do not establish that context has no forecast information. Additional independent cards are required before any submission claim.','', 'Detailed aggregates: backtesting/context01/results/{text_effect_summary,residual_oracle_summary,semantic_crossfit_summary,routed_summary,single_summary,multi_summary,negative_controls,bootstrap_summary,final_decision}.json and family/context/topic/horizon/group/chronology CSV tables.'])
 (root/'CONTEXT-01-CARD-SEMANTIC-LOCATION-report.md').write_text('\n'.join(report)+'\n')
 dump(r/'artifact_manifest.json',dict(pre_result_sha=pre,public_hashes={str(f.relative_to(root)):digest(f)for f in sorted(r.iterdir())if f.is_file()and f.name!='artifact_manifest.json'},report_sha256=digest(root/'CONTEXT-01-CARD-SEMANTIC-LOCATION-report.md'),private_scored_count=len(data)+len(fho)+len(chrono),private_scored_hashes={f.name:digest(f)for f in (private/'scored').glob('*.json')}))
 dump(private/'STATUS.json',dict(branch='track2/context-01-card-semantic-location',HEAD_SHA=pre,current_stage='report_complete',completed_stages=['environment','card_baselines','annotation_router_freeze','matched_experts','tests','pre_remote','evaluation','diagnostics','report'],pending_stages=['result_remote','preservation'],last_successful_artifact=str(r/'final_decision.json'),last_update_time=time.time()))
 print(json.dumps(decision,indent=2),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--private',type=Path,required=True);p.add_argument('--card-private',type=Path,required=True);p.add_argument('--pre-result-sha',required=True);a=p.parse_args();run(a.root,a.private,a.card_private,a.pre_result_sha)

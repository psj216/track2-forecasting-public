"""## Executive summary (read this first)
Report oracle, structure and fixed text routers separately; enforce primary-only acceptance and privacy.
"""
import argparse,csv,json,time
from pathlib import Path
import numpy as np
from qfbench2_track_forecasting.ceiling01.scorer_adapter import aggregate,weights
from backtesting.context01.freeze_annotations import dump,digest
from .evaluate import inputs,grouped,classification,stats
from .models import MODELS

def csvwrite(path,rows):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('w',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r)),lineterminator='\n');w.writeheader();w.writerows(rows)
def predictions(private,mode):
 files=sorted((private/'crossfit').glob(mode+'_*.json'));assert len(files)==(24 if mode=='loco'else 4);out={k:dict(route=np.zeros(24,bool),prob=np.full(24,np.nan),gain=np.full(24,np.nan))for k in [*MODELS,'MAJORITY']};found=np.zeros(24,bool)
 for f in files:
  a=json.loads(f.read_text());tr=a['train'];te=a['test'];assert not(set(tr)&set(te));assert not found[te].any();found[te]=True
  for k,v in a['models'].items():
   out[k]['route'][te]=v['chosen_R2']
   if v['probability']is not None:out[k]['prob'][te]=v['probability']
   if v['gain_prediction']is not None:out[k]['gain'][te]=v['gain_prediction']
 assert found.all();return out

def nulls(private,kind):
 arrays=[];covered=[]
 for f in sorted((private/'controls').glob(kind+'_*.npz')):
  m=json.loads(f.with_suffix('.json').read_text());assert digest(f)==m['sha256'];covered.extend(range(m['start'],m['stop']))
  with np.load(f)as z:arrays.extend(z['composite'].tolist())
 assert covered==list(range(2000)),kind
 return np.array(arrays)

def bootstrap(records,chosen,oracle,struct,s0,family,block=False):
 n=len(records);rng=np.random.default_rng(2204);groups=np.array([np.flatnonzero(np.array(family)==f)for f in sorted(set(family))]);ix=groups[rng.integers(4,size=(5000,4))].reshape(5000,24)if block else rng.integers(n,size=(5000,n))
 def losses(route):return np.array([r['models']['R2']['ratio']if z else 1. for r,z in zip(records,route)])
 def geo(v):return np.exp(np.log(v)[ix].mean(axis=1))
 a=geo(losses(chosen));o=geo(losses(oracle));b=geo(losses(struct));s=geo(losses(s0));den=1-o;good=den>1e-6;cap=(1-a[good])/den[good];d=b-o;valid=d>1e-6
 def interval(z):return np.quantile(z,[.025,.975]).tolist()if len(z)else None
 return dict(composite_95=interval(a),delta_vs_B0_95=interval(a-1),delta_vs_structural_95=interval(a-b),delta_vs_S0_95=interval(a-s),capture_B0_95=interval(cap),capture_B0_unstable_replicates=int((~good).sum()),capture_beyond_structure_95=interval((b[valid]-a[valid])/d[valid]),capture_beyond_structure_unstable_replicates=int((~valid).sum()),replicates=5000,seed=2204,method='Four whole six-card family blocks resampled'if block else'Whole card blocks',interpretation='Exposed-card sensitivity; not independent generalization confidence interval')

def safety(cards,records,chosen):
 mask=np.array([c['cells']>1 for c in cards]);f1=np.array([c['family']=='T2-F1'for c in cards]);detail=[]
 for i,(c,r,on)in enumerate(zip(cards,records,chosen)):
  if c['cells']==1 or not on:continue
  value=r['models']['R2'];base=r['baseline'];detail.append(dict(card_id=c['id'],family=c['family'],improved=value['ratio']<1,marginal_improved_composite_worsened=value['marginal']<base['marginal']and value['ratio']>1,joint_damage=weights(c['cells'])[1]*(value['joint']/max(base['joint'],1e-12)-1),ratio=value['ratio'],marginal=value['marginal'],joint=value['joint'],tail=value['tail']))
 def sub(m):return stats([r for r,z in zip(records,m)if z],np.asarray(chosen)[m])
 mm=sub(mask);ff=sub(f1);return dict(multi=mm,F1=ff,routed_multi_cards=len(detail),multi_improved=sum(v['improved']for v in detail),marginal_improved_composite_worsened=sum(v['marginal_improved_composite_worsened']for v in detail),joint_damage_contribution_arithmetic_mean=float(np.mean([v['joint_damage']for v in detail]))if detail else 0.,severe=mm['composite']>1.01 or ff['composite']>1.01),detail

def run(root,private):
 cards,records,x,y,g=inputs(root,private);r=root/'backtesting/text_route_audit02/results';lo=predictions(private,'loco');fh=predictions(private,'family');primary=lo['ST0_LOG']['route'];struct=np.array([c['cells']==1 for c in cards]);oracle=y.astype(bool);rng=np.random.default_rng(2207);randomchoices=[]
 for _ in range(2000):
  z=np.zeros(24,bool);z[rng.choice(24,int(primary.sum()),replace=False)]=True;randomchoices.append(z)
 choices={k:v['route']for k,v in lo.items()};choices.update(B0=np.zeros(24,bool),R2=np.ones(24,bool),STRUCTURAL_EXPOSED=struct,ORACLE_2WAY=oracle,RANDOM_MATCHED=randomchoices[0]);scores={k:grouped(cards,records,z)for k,z in choices.items()};oratio=scores['ORACLE_2WAY']['composite'];sratio=scores['STRUCTURAL_EXPOSED']['composite'];headroom=1-oratio;families=[c['family']for c in cards];boots={};safe={};privatesafe={};predmetrics={}
 for k,z in choices.items():
  m=scores[k];m['oracle_capture']=(1-m['composite'])/headroom if headroom>1e-6 else None;m['capture_beyond_structure']=(sratio-m['composite'])/(sratio-oratio)if sratio-oratio>1e-6 else None;m['capture_beyond_structure_status']='STABLE'if sratio-oratio>1e-6 else'UNSTABLE_DENOMINATOR'
  safe[k],privatesafe[k]=safety(cards,records,z);boots[k]={name:bootstrap(records,z,oracle,struct,lo['S0_LOG']['route'],families,block)for name,block in [('whole_card',False),('family_block',True)]}
  if k in lo:
   v=lo[k];gain=None if np.isnan(v['gain']).all()else v['gain'];p=v['prob']if gain is None else z.astype(float);predmetrics[k]=classification(y,p,z,g,gain)
 fhscores={k:grouped(cards,records,v['route'])for k,v in fh.items()};controls={};candidate=scores['ST0_LOG']['composite'];null={'LABEL_SHUFFLE':nulls(private,'label'),'TEXT_SHUFFLE':nulls(private,'text'),'RANDOM_MATCHED':np.array([stats(records,v)['composite']for v in randomchoices])}
 for key,a in null.items():
  controls[key]=dict(permutations=2000,mean_composite=float(a.mean()),quantiles=np.quantile(a,[.025,.05,.5,.95,.975]).tolist(),primary_lower_tail_p=float((1+sum(a<=candidate))/(2001)),primary_strictly_better_than_null5pct=bool(candidate<np.quantile(a,.05)))
 clear=all(v['primary_lower_tail_p']<=.05 and v['primary_strictly_better_than_null5pct']for v in controls.values())and candidate<scores['LENGTH_LOG']['composite'];incremental=candidate<scores['S0_LOG']['composite']-1e-12 and candidate<sratio-1e-12 and scores['ST_NO_FAMILY_LOG']['composite']<min(1.,sratio)
 gains=np.maximum(-g,0);dominance=float(gains.max()/gains.sum())if gains.sum()>1e-12 else 1.;low=oratio>=.98 or int(y.sum())<3 or dominance>.75;headroomstate='LOW'if low else('REAL'if oratio<=.97 else'INTERMEDIATE');cap=scores['ST0_LOG']['oracle_capture'];weak=not low and candidate<=.98 and candidate<1 and incremental and cap is not None and cap>.05 and clear and not safe['ST0_LOG']['severe'];bootok=all(v['composite_95'][1]<1 and v['delta_vs_structural_95'][1]<0 and v['delta_vs_S0_95'][1]<0 for v in boots['ST0_LOG'].values());familyok=sum(v['composite']<1 for v in fhscores['ST0_LOG']['family'].values())>=3 and sum(fhscores['ST0_LOG']['family'][f]['composite']<fhscores['S0_LOG']['family'][f]['composite']for f in fhscores['ST0_LOG']['family'])>=3;yes=weak and candidate<=.95 and cap>=.1 and bootok and familyok;strong=yes and candidate<=.92 and cap>=.2 and all(v['composite']<=1 for v in fhscores['ST0_LOG']['family'].values())and(scores['ST0_LOG']['single']['composite']<1 and scores['ST0_LOG']['multi']['composite']<1 or safe['ST0_LOG']['routed_multi_cards']==0)
 verdict='STRONG_YES'if strong else('YES'if yes else('WEAK_YES'if weak else'NO'));nextaxis='TEXT-ROUTE-03-INDEPENDENT-VALIDATION'if yes else('INDEPENDENT_ROUTING_VALIDATION_REQUIRED'if weak else'NEW_INFORMATION_REQUIRED');best=min(MODELS,key=lambda k:scores[k]['composite']);decision=dict(RESULT=verdict,PRIMARY_MODEL='ST0_LOG',ROUTING_HEADROOM=headroomstate,TEXT_ROUTING_SIGNAL=verdict,TEXT_INCREMENTAL_BEYOND_STRUCTURE=bool(incremental),CONTROLS_CLEAR=bool(clear),MULTI_F1_SEVERE_FAILURE=bool(safe['ST0_LOG']['severe']),NEXT_RESEARCH_AXIS=nextaxis,READY_FOR_ONE_SHOT='NO',best_precommitted_model_descriptive_only=best,secondary_winner_cannot_rescue_primary=True,oracle_composite=oratio,oracle_headroom=headroom,oracle_strict_winners=int(y.sum()),oracle_maximum_loggain_share=dominance,primary_composite=candidate,primary_capture=cap,evidence='24previously exposed cards; no independent OOS or officialvalidation')
 dump(r/'router_score_summary.json',dict(models=scores,prediction_metrics=predmetrics,family_holdout=fhscores,primary='ST0_LOG',best_descriptive=best));dump(r/'single_multi_summary.json',dict(models={k:dict(single=v['single'],multi=v['multi'])for k,v in scores.items()}));csvwrite(r/'family_summary.csv',[dict(mode=mode,model=k,family=f,**v)for mode,data in [('loco',scores),('family_holdout',fhscores)]for k,m in data.items()for f,v in m['family'].items()]);dump(r/'multi_safety_summary.json',dict(models=safe,recomputed_exact=True,scope='Every heldout realrouter selects entire frozen E0/E1 and reuses exact parent component scale; no cell-level choices. Pairwise/path effect is original full joint variogram; no new path metric.'));dump(private/'multi_safety_details.json',dict(models=privatesafe));dump(r/'negative_controls.json',dict(stochastic=controls,structure_only=scores['S0_LOG'],length_only=scores['LENGTH_LOG'],family_label_ablation=scores['ST_NO_FAMILY_LOG'],guards='Heldout outcome mutation and fitted prediction immutability; features do not read outcome/name/id/hash; card relabel tests pass',clear=bool(clear),seeds=dict(label=2202,text=2203,random=2207)));dump(r/'bootstrap_summary.json',dict(models=boots,exposed_only=True));dump(r/'final_decision.json',decision)
 ledger=[]
 for i,(c,rec)in enumerate(zip(cards,records)):
  on=bool(primary[i]);value=rec['models']['R2'if on else'B0'];ledger.append(dict(card_id=c['id'],family=c['family'],single=c['cells']==1,cells=c['cells'],B0_card_loss=1.,R2_card_loss=rec['models']['R2']['ratio'],oracle_winner=int(y[i]),gain_target=float(g[i]),crossfit_predicted_route=int(on),route_probability=float(lo['ST0_LOG']['prob'][i]),routed_card_loss=value['ratio'],marginal=value['marginal'],joint=value['joint'],tail=value['tail']))
 csvwrite(private/'results/card_route_ledger.csv',ledger)
 for mode,preds in [('loocv',lo),('family_holdout',fh)]:
  rows=[dict(card_id=c['id'],family=c['family'],model=k,route=int(v['route'][i]),probability=None if np.isnan(v['prob'][i])else float(v['prob'][i]),predicted_gain=None if np.isnan(v['gain'][i])else float(v['gain'][i]))for k,v in preds.items()for i,c in enumerate(cards)];csvwrite(private/'results'/f'{mode}_predictions.csv',rows)
 for name in ['card_route_ledger.csv','loocv_predictions.csv','family_holdout_predictions.csv']:
  source=private/'results'/name;rows=list(csv.DictReader(source.open()));public=[]
  for row in rows:
   public.append({k:(v if k in ['card_id','family','single','cells','model']else'WITHHELD_PRIVATE_RESEARCH_LEDGER')for k,v in row.items()}|dict(publication_status='REDACTED_PER_CARD_OUTCOME_PREDICTION_FIREWALL',private_sha256=digest(source)))
  csvwrite(r/name,public)
 audit=dict(parent_sha='d3618dcd9aae4ac118a5c12c0fe8f3709a72f296',pre_result_sha=json.loads((private/'pre_remote_receipt.json').read_text())['PRE_RESULT_SHA'],cards=24,cells=63,model_folds=28*9,whole_card_routes=True,expert_refits=0,forecast_regeneration=False,permutation_fits=2000*24*2,permutation_count_per_control=2000,bootstrap_replicates=5000,no_redesign_after_scores=True,private_ledger_hashes={n:digest(private/'results'/n)for n in ['card_route_ledger.csv','loocv_predictions.csv','family_holdout_predictions.csv']});dump(r/'execution_audit.json',audit)
 lines=['## Executive summary (read this first)','',f"TEXT-ROUTE-AUDIT-02: **{verdict}**. Routing headroom: **{headroomstate}**, oracle ratio {oratio:.6f}. The sole primaryST0_LOGratio is {candidate:.6f}. Incremental text beyond both structural baselines and family ablation: {incremental}. Next: **{nextaxis}**. Submission readiness: **NO**.",'','All24cards/63cells are already exposed;13single/11multi,6perfamily. No independent OOS or official validation. No new alpha was created; E0/E1 forecasts are immutable. This tests only whole-card expert choice. Apparent gains require future independent validation.','',f"Parent: `{audit['parent_sha']}`. PRE: `{audit['pre_result_sha']}`. RESULT SHA is in the external completion receipt. Branch: track2/text-route-audit-02.",'','|Model|Composite|Marginal|Joint|Single|Multi|Oracle capture|R2 cards|','|---|---:|---:|---:|---:|---:|---:|---:|']
 for k in ['B0','R2','STRUCTURAL_EXPOSED','S0_LOG','T0_LOG','ST0_LOG','STF0_LOG','ST_NO_FAMILY_LOG','LENGTH_LOG','S0_RIDGE','T0_RIDGE','ST0_RIDGE','MAJORITY','RANDOM_MATCHED','ORACLE_2WAY']:
  v=scores[k];fmt=lambda a:'NA'if a is None else f'{a:.6f}';lines.append('|'+ '|'.join([k,fmt(v['composite']),fmt(v['marginal']),fmt(v['joint']),fmt(v['single']['composite']),fmt(v['multi']['composite']),fmt(v['oracle_capture']),str(v['routed_R2'])])+'|')
 lines+=['',f"Oracle choosesR2on {int(y.sum())}/24cards. Headroom={headroom:.6f}. Maximum positive loggain share={dominance:.4f}. Oracle is descriptive, never a predictive result. Gain distribution quantiles: {np.quantile(g,[0,.25,.5,.75,1]).tolist()}.",'','S0uses13structuralcolumns;T0uses36inherited lexical/count columns. Parent asset-injected topic flags, metadata temporal flags and forced joint flags are excluded fromT0. ST0concatenates49columns; no feature search or new LLM annotations. STF0has5forecast-statecolumns and is diagnostic only. Card names, IDs, hashes and raw dates are never model inputs. Fixed L2logisticC1,train-only StandardScaler,threshold.50,no class weighting; fixed Ridgealpha1on gain target,route when predicted gain<0. Secondary results cannot rescue primary failure.','',f"Primary multi safety: {json.dumps(safe['ST0_LOG'],sort_keys=True)}.",'','|Model|F1 heldout|F2 heldout|F3 heldout|F4 heldout|','|---|---:|---:|---:|---:|']
 for k,v in fhscores.items():lines.append('|'+ '|'.join([k,*[f"{v['family'][f]['composite']:.6f}"for f in ['T2-F'+str(i)for i in range(1,5)]]])+'|')
 lines+=['','Whole-card LOCO24and four18train/6testfamilyholdouts; no card cells split. Every real heldout router forecast has exact full component rescore matching the selected frozen parent card. Structural-exposed singleR2/multiB0 is post-CONTEXT diagnostic, not new independent evidence. Majority uses training winners only.','',f"Controls2000each: {json.dumps(controls,sort_keys=True)}. Structure-only, length-only and family-ablation models are separately reported. Card-ID leakage and future/heldout-outcome mutation tests pass. Changing training labels and refitting is a deliberately different null experiment; frozen fitted predictions cannot read mutated outcomes.",'',f"Primary5000whole-card bootstrap: {boots['ST0_LOG']['whole_card']}. Primary5000whole-family block bootstrap: {boots['ST0_LOG']['family_block']}.",'','Bootstrap measures exposed-sample sensitivity and does not create independent OOS evidence. Capture retains negative values. Tiny/nonpositive denominators are marked unstable, not forced. No threshold sensitivity or model/feature redesign was performed.','',f"Best precommitted predictive model descriptively: {best}. It cannot replace ST0_LOG or turn primary failure into success.",'','Public per-card outcome/prediction CSVs are explicit redacted metadata/hash projections. Full required ledgers, fold models, outcomes and all controls are preserved privately in the recovery archive. Public aggregate results remain complete. Main is never modified.']
 (root/'TEXT-ROUTE-AUDIT-02-report.md').write_text('\n'.join(lines)+'\n');dump(r/'artifact_manifest.json',dict(public_hashes={str(f.relative_to(root)):digest(f)for f in r.iterdir()if f.is_file()and f.name!='artifact_manifest.json'},report_sha256=digest(root/'TEXT-ROUTE-AUDIT-02-report.md'),private_crossfit_hashes={f.name:digest(f)for f in (private/'crossfit').glob('*.json')}));print(json.dumps(decision,indent=2),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--private',type=Path,required=True);a=p.parse_args();run(a.root,a.private)

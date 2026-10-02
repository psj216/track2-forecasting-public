"""## Executive summary (read this first)
Reconstruct the unique parent R2 from immutable baseline/correction bytes and verify every score.
"""
import argparse,json,subprocess,time
from pathlib import Path
import numpy as np
from backtesting.context01.freeze_annotations import dump,digest,verify
from backtesting.context01.diagnostics import summarize
from qfbench2_track_forecasting.context01.engine import apply
from qfbench2_track_forecasting.context01.context_router import route,EXPERTS
from qfbench2_track_forecasting.ceiling01.scorer_adapter import components,score
from .features import build,S_NAMES,T_NAMES,F_NAMES
PARENT='d3618dcd9aae4ac118a5c12c0fe8f3709a72f296'
def run(root,private,parent_private,card_private,main_sha):
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==PARENT;verify(root);out=root/'backtesting/text_route_audit02/results';cards=json.loads((root/'backtesting/context01/results/card_manifest.json').read_text())['cards'];ann=json.loads((root/'backtesting/context01/results/context_annotations.json').read_text())['cards'];texts=json.loads((parent_private/'annotation_texts.json').read_text())['cards'];rows=json.loads((parent_private/'rows.json').read_text())['rows'];b0=[];r2=[];audits=[];records=[]
 assert len(cards)==24 and sum(c['cells']for c in cards)==63
 for i,c in enumerate(cards):
  source=parent_private/'scored'/f'loco_card{i:02d}.json';rec=json.loads(source.read_text());assert rec['card_id']==c['id'];x=np.load(parent_private/'baselines'/(c['id']+'_baseline.npy'));z=apply(x,rec['prediction']['R2']);assert np.array_equal(z,apply(x,rec['prediction']['R2']))
  with np.load(parent_private/'experts'/f'card{i:02d}.npz')as a:expert={k:a['prediction'][j]for j,k in enumerate(EXPERTS)};available={k:a['available'][j]for j,k in enumerate(EXPERTS)}
  assets=[row['asset']for row in rows if row['card_id']==c['id']];_,delta,_,_=route(ann[c['id']]['economic_topics'],assets,expert,available);assert np.array_equal(z,apply(x,delta)),c['id'];assert digest(card_private/c['file'])==c['sha256']
  with np.load(card_private/c['file'])as a:truth=a['truth']
  base=components(x,truth);candidate=score(z,truth,base);assert base==rec['baseline'] and candidate==rec['models']['R2'],c['id']
  path=private/'frozen_forecasts'/f'card{i:02d}.npz';path.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(path,E0=x,E1=z);b0.append(x);r2.append(z);records.append(rec);audits.append(dict(card_id=c['id'],npz_sha256=digest(path),B0_array_sha256=__import__('hashlib').sha256(x.tobytes()).hexdigest(),R2_array_sha256=__import__('hashlib').sha256(z.tobytes()).hexdigest(),parent_score_record_sha256=digest(source),independent_reconstruction_bitwise_equal=True,full_components_exact_equal=True))
  print(json.dumps(dict(stage='frozen_forecast_audit',completed=i+1,total=24,artifact=str(path))),flush=True)
 features=build(cards,texts,ann,b0,r2);np.savez_compressed(private/'features.npz',**features);dump(private/'frozen_parent_records.json',dict(records=records));dump(private/'cards.json',dict(cards=cards))
 parentmetrics=json.loads((root/'backtesting/context01/results/routed_summary.json').read_text())['models']['R2'];current=summarize(records,'R2')
 for k in current:assert current[k]==parentmetrics[k],k
 for f in range(1,5):
  fam='T2-F'+str(f);metric=summarize([rec for rec in records if rec['family']==fam],'R2');prior=json.loads((root/'backtesting/context01/results/multi_summary.json').read_text())['F1']['R2']if f==1 else None
  if prior:
   for k in metric:assert metric[k]==prior[k]
 dump(out/'environment_audit.json',dict(status='PASS',parent_sha=PARENT,branch='track2/text-route-audit-02',main_sha_before=main_sha,main_modified=False,python=__import__('sys').version,common_version='v2.4.3',universe=dict(cards=24,cells=63,single=13,multi=11),parent_artifact_hashes={f.name:digest(f)for f in (root/'backtesting/context01/results').iterdir()if f.is_file()},frozen_text=dict(cards=24,source_sha256=digest(parent_private/'annotation_texts.json'),provenance='Parent public questions and timestamp-checked corpus; annotations frozen before CONTEXT outcomes',parent_topic_caveat='Parent economic_topics include asset-class injections; T0 recomputes only inherited topic regex on frozen question text, no metadata injection'),aggregate_R2=current))
 dump(out/'frozen_expert_manifest.json',dict(experts=['E0=frozenV5.1textB0','E1=frozenCONTEXT01R2'],cards=audits,fit_or_recalibration=False,exact_reconstruction='Original full R2 arrays were not retained. Unique saved baseline+float64correction and unchanged parent pure-shift adapter reproduce identical bytes along two independent paths, and all parent composite/components match exactly. Arrays now stored once and frozen.',score_adapter_sha256=digest(root/'qfbench2_track_forecasting/ceiling01/scorer_adapter.py')))
 dump(out/'feature_manifest.json',dict(primary='ST0_LOG',columns=dict(S0=S_NAMES,T0=T_NAMES,ST0=S_NAMES+T_NAMES,STF0=S_NAMES+T_NAMES+F_NAMES),dimensions={k:v.shape[1]for k,v in features.items()},feature_sha256=digest(private/'features.npz'),outcome_fields_as_features=False,card_ids_names_hashes_dates_as_features=False,text_provenance='Inherited fixed regex, frozen lexical counts and frozen dated texts. New numeric summaries use no outcomes. No LLM/embeddings/new topics. Parent metadata-injected topics and temporal/forced joint flags excluded from T0.',preprocessing='Train-only StandardScaler; no feature selection; no class weighting',forecast_state='STF0secondary only; frozen forecasts only; never promoted to primary'))
 dump(root/'backtesting/text_route_audit02/STATUS.json',dict(branch='track2/text-route-audit-02',HEAD_SHA=PARENT,current_stage='frozen_forecasts_features_verified',completed_stages=['environment','artifact_audit'],pending_stages=['implementation_tests','pre_remote','oracle','crossfit','controls','bootstrap','report','full_tests','result_remote','recovery'],last_successful_artifact=str(out/'feature_manifest.json'),last_update_time=time.time()))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--private',type=Path,required=True);p.add_argument('--parent-private',type=Path,required=True);p.add_argument('--card-private',type=Path,required=True);p.add_argument('--main-sha',required=True);a=p.parse_args();run(a.root,a.private,a.parent_private,a.card_private,a.main_sha)

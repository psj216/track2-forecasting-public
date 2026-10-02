"""## Executive summary (read this first)
Read only public question metadata/dated corpus and frozen baseline arrays; do not load truth.
"""
import argparse,json,tomllib,collections
from pathlib import Path
import numpy as np
from qfbench2_track_forecasting.context01.deterministic_annotator import annotate,matrix
from qfbench2_track_forecasting.context01 import context_schema as schema
from qfbench2_track_forecasting.context01.context_router import EXPERTS,PRIORITY,TOPIC_EXPERTS,eligible
from .freeze_annotations import dump,digest
def run(root,private,card_private):
 result=root/'backtesting/context01/results';cards=json.loads((card_private/'cards.json').read_text());frozen=json.loads((root/'backtesting/ceiling01/frozen_inputs.json').read_text())['card_universe']
 assert len(cards)==24 and sum(c['cells']for c in cards)==63 and sum(c['cells']==1 for c in cards)==13 and collections.Counter(c['family']for c in cards)==dict.fromkeys(['T2-F1','T2-F2','T2-F3','T2-F4'],6)
 annotations={};baseline=[];texts={};public=[]
 for c in cards:
  assert digest(card_private/c['file'])==frozen['files'][c['file']]
  u=root/'units'/c['id'];m=tomllib.loads((u/'card.toml').read_text());assert m['targets']['asset_ids']==c['assets']and list(m['targets']['horizons'])==c['horizons']and str(m['provenance']['data_cutoff'])==c['origin']
  index=json.loads((u/'text/corpus_index.json').read_text());docs=[];record=[]
  for d in index['documents']:
   if str(d['timestamp'])[:10]>c['origin']:raise ValueError('Future indexed text: '+c['id'])
   f=(u/'text'/d['file']).resolve();assert f.is_relative_to((u/'text').resolve());docs.append(f.read_text());record.append(dict(path=str(f.relative_to(root)),timestamp=d['timestamp'],sha256=digest(f)))
  question=str(m['metadata'].get('description',''));annotations[c['id']]=annotate(c,question,docs);texts[c['id']]=dict(question=question,documents=docs)
  with np.load(card_private/c['file'])as z:
   for key in ['baseline','numeric']:
    a=z[key];assert a.shape==(2000,len(c['horizons']),len(c['assets']));path=private/'baselines'/(c['id']+'_'+key+'.npy');path.parent.mkdir(parents=True,exist_ok=True);np.save(path,a);baseline.append(dict(card_id=c['id'],kind='B_TEXT'if key=='baseline'else'B_NUMERIC',sha256=digest(path),draws=2000,shape=list(a.shape)))
  public.append({k:c[k]for k in ['id','family','origin','assets','horizons','cells','target_type','frequency','file','sha256']});annotations[c['id']]['text_provenance']=record;annotations[c['id']]['question_sha256']=__import__('hashlib').sha256(question.encode()).hexdigest()
 x,rows,cols=matrix(cards,annotations);np.save(private/'context_features.npy',x);dump(private/'rows.json',dict(rows=rows));dump(private/'annotation_texts.json',dict(cards=texts))
 dump(result/'card_manifest.json',dict(cards=public,count=24,cells=63,single=13,multi=11,family_counts=dict.fromkeys(['T2-F1','T2-F2','T2-F3','T2-F4'],6),sample='24-card previously exposed research proxy; not independent OOS; not official score',source_card_manifest_sha256=digest(card_private/'cards.json')))
 dump(result/'baseline_manifest.json',dict(baselines=baseline,primary='Frozen V5.1 B_TEXT',diagnostic='Frozen V5.1 B_NUMERIC',truth_not_loaded=True,regeneration=False))
 dump(result/'context_schema.json',dict(columns=cols,topics=schema.TOPICS,conditionality=schema.CONDITIONS,language=schema.LANGUAGE,entities=list(schema.ENTITIES),events=list(schema.EVENTS),topic_scope='Public task description plus structured target asset group. Incidental full-corpus topics are audited but not used for primary routing or topic features.',language_scope='Public task description plus all indexed dated source document bodies',temporal='immediate<=5BD,short6-21,medium22-63,long>63;multi-horizon separate',annotation_method='Deterministic regex dictionaries; no LLM-assisted labels',TEXT_EMBEDDING_DIAGNOSTIC='NOT_AVAILABLE',embedding_reason='No preexisting identified, versioned, hashed and licensed local model selected; no download'))
 dump(result/'context_annotations.json',dict(cards=annotations,feature_sha256=digest(private/'context_features.npy'),outcomes_opened=False))
 dump(result/'router_manifest.json',dict(experts=list(EXPERTS),priority=list(PRIORITY),topic_experts=TOPIC_EXPERTS,no_route='exact zero',multiple='R1 first eligible available in priority; R2 equal available expert average; R3 fixed50/50 B5+R2',flow_mapping='F admitted only MKT; other assets zero',macro_mapping='Inherited US expectation macro exposure and predeclared global USD reserve exposure; not international local surveys',routing_eligibility={c['id']:{a:eligible(annotations[c['id']]['economic_topics'],a)for a in c['assets']}for c in cards},rejected_sources_used=False))
 names=['card_manifest.json','baseline_manifest.json','context_schema.json','context_annotations.json','router_manifest.json'];dump(result/'annotation_manifest.json',dict(status='ANNOTATION_FROZEN_BEFORE_CARD_OUTCOMES',hashes={n:digest(result/n)for n in names},features_sha256=digest(private/'context_features.npy'),truth_load_count=0))
 dump(private/'STATUS.json',dict(branch='track2/context-01-card-semantic-location',current_stage='annotation_frozen',completed_stages=['environment','card_baselines','annotation_router_freeze'],pending_stages=['matched_experts','implementation_tests','pre_remote','evaluation','report_result_remote','preservation'],last_successful_artifact=str(result/'annotation_manifest.json')))
 print(json.dumps(dict(stage='annotation freeze',cards=24,cells=len(x),features=x.shape[1],outcomes_loaded=False,artifact=str(result/'annotation_manifest.json'))),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--private',type=Path,required=True);p.add_argument('--card-private',type=Path,required=True);a=p.parse_args();run(a.root,a.private,a.card_private)

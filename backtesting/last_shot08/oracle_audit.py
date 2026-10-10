"""Executive summary: score frozen whole-card forecasts after verified PRE and enforce the oracle kill gate.
Write private comparative losses incrementally; expose aggregate scores only.
"""
import argparse,json,time,zipfile,csv
from pathlib import Path
import numpy as np
from .core import ROOT,EXPERTS,dump,digest,array_digest,require_pre,kill_gate
from qfbench2_track_forecasting.ceiling01.scorer_adapter import components,score,aggregate

def summarize(cards,records,choices):
 def subset(ix):
  if not ix:return None
  selected=[records[i]['models'][choices[i]]for i in ix]
  result={'composite':aggregate([r['ratio']for r in selected]),'arithmetic':float(np.mean([r['ratio']for r in selected])),'cards':len(ix)}
  for k in ['marginal','joint','tail']:
   rr=[records[i]['models'][choices[i]][k]/records[i]['baseline'][k]for i in ix if records[i]['baseline'][k]>1e-12]
   result[k]=aggregate(rr)
  return result
 allix=list(range(len(cards)));full=subset(allix)
 full.update(single=subset([i for i,c in enumerate(cards)if c['cells']==1]),multi=subset([i for i,c in enumerate(cards)if c['cells']>1]),families={f:subset([i for i,c in enumerate(cards)if c['family']==f])for f in sorted({c['family']for c in cards})},winner_counts={e:choices.count(e)for e in EXPERTS})
 return full

def concentration(cards,records,choices):
 g=np.maximum(0,np.array([1-records[i]['models'][e]['ratio']for i,e in enumerate(choices)]));total=float(g.sum())
 frac=lambda v:float(v/total)if total>1e-12 else None
 families={f:float(g[[i for i,c in enumerate(cards)if c['family']==f]].sum())for f in sorted({c['family']for c in cards})}
 return {'basis':'gross arithmetic per-card ratio gain; future-informed oracle only','gross_gain':total,'largest_card_fraction':frac(g.max()),'largest_family_fraction':frac(max(families.values())),'single_fraction':frac(g[[i for i,c in enumerate(cards)if c['cells']==1]].sum()),'multi_fraction':frac(g[[i for i,c in enumerate(cards)if c['cells']>1]].sum()),'expert_fraction':{e:frac(g[[i for i,x in enumerate(choices)if x==e]].sum())for e in EXPERTS},'CARD_CONCENTRATED':bool(total>0 and g.max()/total>.4),'FAMILY_CONCENTRATED':bool(total>0 and max(families.values())/total>.6)}

def run(private,archive):
 pre=require_pre(private);out=ROOT/'backtesting/last_shot08/results';cards=json.loads((private/'recovered/text/private/cards.json').read_text())['cards'];dest=private/'scored';dest.mkdir(exist_ok=True)
 manifest=json.loads((out/'expert_reproduction_manifest.json').read_text());records=[];beg=time.monotonic()
 with zipfile.ZipFile(archive)as z:
  for i,c in enumerate(cards):
   sp=dest/f'card{i:02d}.json'
   if sp.exists():records.append(json.loads(sp.read_text()));continue
   historical_name=f'context01-private/scored/loco_card{i:02d}.json';raw=z.read(historical_name)
   old=json.loads(raw)
   assert old['card_id']==c['id']
   source=private/'recovered/ceiling/private'/c['file'];assert digest(source)==c['sha256']
   with np.load(source)as truthfile:truth=truthfile['truth']
   with np.load(private/'library'/f'card{i:02d}.npz')as x:
    for e in EXPERTS:assert array_digest(x[e])==manifest['cards'][i]['forecast_hashes'][e]
    reference=components(x['B0'],truth);models={e:score(x[e],truth,reference)for e in EXPERTS}
   assert reference==old['baseline'],'Historical scorer baseline mismatch'
   for e in EXPERTS:assert models[e]==old['models'][e],f'Historical component mismatch {e} card index {i}'
   r={'baseline':reference,'models':models,'historical_components_exact':True,'source_record_sha256':__import__('hashlib').sha256(raw).hexdigest(),'PRE_RESULT_LAST_SHOT08_SHA':pre}
   dump(sp,r);records.append(r)
   print(json.dumps({'stage':'whole-card score verification','completed':i+1,'total':24,'elapsed':round(time.monotonic()-beg,2),'path':str(sp)}),flush=True)
 choices=[min(EXPERTS,key=lambda e:r['models'][e]['ratio'])for r in records]
 summary=summarize(cards,records,choices);summary.update(future_informed=True,predictive_result=False,whole_card_selection=True,headroom=1-summary['composite'],GEOMETRIC_ONLY_HEADROOM_RISK=summary['arithmetic']>=1,best_card_ratio=min(r['models'][choices[i]]['ratio']for i,r in enumerate(records)),worst_card_ratio=max(r['models'][choices[i]]['ratio']for i,r in enumerate(records)))
 dump(out/'library_oracle_summary.json',summary);dump(out/'concentration_summary.json',concentration(cards,records,choices))
 expertrows=[];familyrows=[]
 for e in EXPERTS:
  s=summarize(cards,records,[e]*24);expertrows.append({'executive_summary':'Same 24 exposed cards; aggregate only','expert':e,**{k:s[k]for k in ['composite','arithmetic','marginal','joint','tail']},'single':s['single']['composite'],'multi':s['multi']['composite']})
  for f,v in s['families'].items():familyrows.append({'executive_summary':'Six exposed whole cards per family','expert':e,'family':f,**v})
 for name,rows in [('expert_aggregate_summary.csv',expertrows),('expert_family_summary.csv',familyrows)]:
  with (out/name).open('w',newline='')as fp:w=csv.DictWriter(fp,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 dump(out/'arithmetic_sensitivity.json',{'B0':1.,'LIBRARY_ORACLE':summary['arithmetic'],'experts':{r['expert']:r['arithmetic']for r in expertrows},'primary':'NOT_RUN_PENDING_GATE' if summary['composite']<=.75 else 'NOT_RUN_KILL_GATE'})
 manifest.update(historical_score_verification='All five profiles reproduce every historical marginal/joint/tail/composite exactly; zero tolerance',verified_card_count=24,truth_deserialized_after_PRE=True,PRE_RESULT_LAST_SHOT08_SHA=pre)
 dump(out/'expert_reproduction_manifest.json',manifest)
 decision=kill_gate(len(EXPERTS),summary['composite'])
 dump(private/'oracle_stage_receipt.json',{'PRE':pre,'complete':True,'cards':24,'historical_score_reproduction_exact':True,'decision':decision})
 print(json.dumps({'oracle_composite':summary['composite'],'arithmetic':summary['arithmetic'],'kill_gate':decision}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--private',type=Path,required=True);p.add_argument('--archive',type=Path,required=True);a=p.parse_args();run(a.private,a.archive)

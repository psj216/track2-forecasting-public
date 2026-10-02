"""## Executive summary (read this first)
Complete requested matched random reporting for every router without changing any frozen forecast/gate.
"""
import argparse,json,csv
from pathlib import Path
import numpy as np
from backtesting.context01.freeze_annotations import digest,dump
from backtesting.text_route_audit02.evaluate import inputs,stats,grouped
from backtesting.text_route_audit02.aggregate_results import predictions
from backtesting.text_route_audit02.models import MODELS
parser=argparse.ArgumentParser();parser.add_argument('--private',type=Path,required=True);args=parser.parse_args();r=Path.cwd();p=args.private;d=r/'backtesting/text_route_audit02/results';cards,records,x,y,g=inputs(r,p);pred=predictions(p,'loco');models=json.loads((d/'router_score_summary.json').read_text())['models'];control=json.loads((d/'negative_controls.json').read_text());rates={};cache={}
for k in MODELS:
 K=int(pred[k]['route'].sum())
 if K not in cache:
  rng=np.random.default_rng(2207);a=[];first=None
  for _ in range(2000):
   chosen=np.zeros(24,bool);chosen[rng.choice(24,K,replace=False)]=True
   if first is None:first=grouped(cards,records,chosen)
   a.append(stats(records,chosen)['composite'])
  cache[K]=(np.array(a),first)
 a,first=cache[K];candidate=models[k]['composite'];rates[k]=dict(application_cards=K,application_fraction=K/24,permutations=2000,seed=2207,mean_composite=float(a.mean()),quantiles=np.quantile(a,[.025,.05,.5,.95,.975]).tolist(),lower_tail_p=float((1+sum(a<=candidate))/2001),first_fixed_random_baseline=first)
control['matched_random_for_every_precommitted_predictive_router']=rates;control['supplementary_reporting_note']='Requested per-router random application-rate comparisons derived from already frozen choices; no fitting, tuning, expert changes or final primary promotion. Primary original2000label/text tests remain sole acceptance controls.';dump(d/'negative_controls.json',{k:v for k,v in control.items()if k!='executive_summary'})
audit=json.loads((d/'execution_audit.json').read_text());audit.update(per_router_matched_random_replicates=2000,distinct_application_counts=sorted(cache),reporting_supplement_only=True);dump(d/'execution_audit.json',{k:v for k,v in audit.items()if k!='executive_summary'})
report=r/'TEXT-ROUTE-AUDIT-02-report.md';s=report.read_text();s+='\nEvery precommitted predictive router also has its own2000random whole-card comparator with exactly the same application count. This requested secondary reporting comparison does not change the precommitted primary or promote a secondary winner. No secondarylabel/text null was selected after outcomes.\n\n|Router|R2cards|Matched random mean|Lower-tail p|\n|---|---:|---:|---:|\n'
for k,v in rates.items():s+=f"|{k}|{v['application_cards']}|{v['mean_composite']:.6f}|{v['lower_tail_p']:.6f}|\n"
s+='\nThe secondary text-only Ridge uses a continuous score-gain label and can behave differently from the primary binary winner classifier. Its apparent gain is retained as a descriptive diagnostic, not erased, and cannot substitute for a failed primary. SecondaryRidge did not receive primary acceptance-level text/label permutation testing, so no confirmed incremental text-routing claim is made for it. Further independent evidence would be required before taking it forward; this experiment does not authorize TEXT-ROUTE-03 or official submission.\n';report.write_text(s)
f=d/'artifact_manifest.json';m=json.loads(f.read_text());m['public_hashes']={str(f.relative_to(r)):digest(f)for f in d.iterdir()if f.is_file()and f.name!='artifact_manifest.json'};m['report_sha256']=digest(report);dump(f,{k:v for k,v in m.items()if k!='executive_summary'});print('All9predictive models have matched-rate2000random comparisons; frozen primary unchanged')

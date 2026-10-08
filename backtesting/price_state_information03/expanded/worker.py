"""Executive summary: bounded restartable task batches; preserve every completed replicate."""
from .core import *
from . import evaluate as e
import argparse,time

def run(budget):
 p=private();begun=time.monotonic();done=json.loads((p/'worker_completed.json').read_text()) if (p/'worker_completed.json').exists() else []
 folds=pd.read_csv(OUT/'fold_manifest.csv');tasks=[('prepare',None),*[('fold',int(k)) for k in folds.loc[folds.evaluable,'fold']],('collect',None)]
 for u in ['u0','u1']:
  kinds=['N0','FOLD_RANDOM','BALANCED_RANDOM','N1','N2','N3','N4','N5']
  if u=='u1':kinds += ['FAMILY_'+g for g in json.loads((OUT/'frozen_feature_spec.json').read_text())['secondary_groups']]
  for kind in kinds:
   random=kind in ['N0','FOLD_RANDOM','BALANCED_RANDOM'] or kind.startswith('FAMILY_');count=RANDOM_REPS if random else NULL_REPS;chunk=100 if random else 20
   for start in range(0,count,chunk):tasks.append(('null',(u,kind,start,min(start+chunk,count))))
  for block in ['origin','year','quarter','asset']:
   for start in range(0,BOOTSTRAP_REPS,500):tasks.append(('bootstrap',(u,block,start,start+500)))
 for stage,args in tasks:
  key=json.dumps([stage,args]);
  if key in done:continue
  if time.monotonic()-begun>=budget:
   save(p/'continuation.json',dict(next_task=[stage,args],completed=len(done),total=len(tasks),elapsed=time.monotonic()-begun));print('BOUNDED_YIELD',len(done),'/',len(tasks),'next',stage,args,flush=True);return
  failures=json.loads((p/'worker_failures.json').read_text()) if (p/'worker_failures.json').exists() else {}
  if failures.get(key,0)>=2:raise RuntimeError('STOP: same task failed twice '+key)
  print('STAGE',stage,args,'completed',len(done),'/',len(tasks),'elapsed',round(time.monotonic()-begun,1),'output',p,flush=True)
  try:
   if stage=='prepare':e.prepare_data()
   elif stage=='fold':e.fit_fold(args)
   elif stage=='collect':e.collect()
   elif stage=='null':e.null_chunk(*args)
   else:e.bootstrap_chunk(*args)
  except Exception:
   failures[key]=failures.get(key,0)+1;save(p/'worker_failures.json',failures);save(p/'continuation.json',dict(next_task=[stage,args],completed=len(done),total=len(tasks),failed=True,failures=failures[key]));raise
  done.append(key);save(p/'worker_completed.json',done)
 save(p/'continuation.json',dict(completed=len(done),total=len(tasks),complete=True));print('ALL_TASKS_COMPLETE',len(done),flush=True)

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--budget',type=int,default=540);run(a.parse_args().budget)

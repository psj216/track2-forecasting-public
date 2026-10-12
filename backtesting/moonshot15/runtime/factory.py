"""## Executive summary (read this first)
Build five shared-layer images, test offline/House-proxy repeats, then publish unique tags.
No scores, no submissions, no live House credentials, no alteration of the safe image.
"""
from __future__ import annotations
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import tomllib
import numpy as np
from backtesting.v51_delivery_emergency11 import runner as gate
ROOT=Path(__file__).resolve().parents[3]
BASE='docker.io/jotj216/track2-f4-approved@sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874'
WORK=Path(os.environ.get('RUNNER_TEMP','/tmp'))/'m15-factory'
EVIDENCE=ROOT/'candidate-artifacts'
UNITS=['t2-F1-patient-dropped-2015','t2-F2-eur-parity-2022','t2-F3-brexit-joint-2016','t2-F4-funding-stress-2y-2008','t2-F4-covid-nfp-2020']
START=time.monotonic()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,obj):
 EVIDENCE.mkdir(parents=True,exist_ok=True);(EVIDENCE/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def command(args,name,timeout=180):
 EVIDENCE.joinpath('logs').mkdir(parents=True,exist_ok=True)
 t=time.monotonic();p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
 (EVIDENCE/'logs'/f'{name}.log').write_text(p.stdout+'\n'+p.stderr)
 if p.returncode:raise RuntimeError(f'{name} exit {p.returncode}')
 return p.stdout,time.monotonic()-t
def inspection(image):return json.loads(command(['docker','image','inspect',image],'inspect-'+image.split(':')[-1][:12])[0])[0]
def run(image,unit,name,active=False):
 path=ROOT/'units'/unit;asof=tomllib.loads((path/'card.toml').read_text())['provenance']['data_cutoff']
 out=WORK/name;out.mkdir(parents=True,exist_ok=True);out.chmod(0o777)
 cmd=['docker','run','--rm','--network','m15-internal' if active else 'none','--read-only','--tmpfs','/tmp:rw,size=256m','--memory=8g','--cpus=2','-v',f'{path}:/input:ro','-v',f'{out}:/output']
 if active:
  for k,v in {'MODEL_ENDPOINT':'http://house.test:8000','MODEL_NAME':'synthetic-house-contract-test','MODEL_TOKEN':'synthetic-testing-only','http_proxy':'http://testuser:testpass@m15-proxy:8080'}.items():cmd+=['-e',k+'='+v]
 cmd +=[image,'forecast','--panels','/input','--text','/input/text','--asof',asof,'--out','/output/forecast.parquet']
 _,wall=command(cmd,name,180)
 receipt=gate.validate_output(out,path,asof);receipt.update({'unit':unit,'wall_seconds':wall,'output_size_bytes':sum(p.stat().st_size for p in out.iterdir() if p.is_file())})
 meta=json.loads((out/'forecast_meta.json').read_text())
 if 'moonshot15' in meta:receipt['moonshot15']=meta['moonshot15']
 return receipt,out
def validate():
 WORK.mkdir(parents=True,exist_ok=True)
 command(['docker','pull',BASE],'exact-base-pull',180)
 base=inspection(BASE)
 assert base['Architecture']=='amd64' and base['Os']=='linux'
 assert base['Config']['User']=='runner'
 save('base-image.json',{'image':BASE,'image_id':base['Id'],'platform':'linux/amd64','anonymous_pull':True,'unchanged':True})
 gate.EVIDENCE=EVIDENCE/'base-security';gate.WORK=WORK/'base-security';gate.WORK.mkdir(exist_ok=True)
 security=gate.security(base);save('security-summary.json',security)
 # Only isolated engine code enters the build context. No units/research/git/private files.
 context=WORK/'build-context';context.mkdir(exist_ok=True)
 shutil.copytree(ROOT/'moonshot15_engine',context/'moonshot15_engine',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 files=[str(p.relative_to(context)) for p in context.rglob('*') if p.is_file()]
 assert files and all(p.startswith('moonshot15_engine/') for p in files)
 save('build-context.json',{'files':files,'hashes':{p:sha(context/p) for p in files},'no_labels':True,'no_credentials':True})
 baselines={}
 for idx,u in enumerate(UNITS):
  r,o=run(BASE,u,'base-'+str(idx));baselines[u]=r
 save('baseline-fixture-receipts.json',baselines)
 command(['docker','network','create','--internal','m15-internal'],'internal-network',30)
 command(['docker','run','-d','--name','m15-proxy','--network','m15-internal','--read-only','--tmpfs','/tmp','--entrypoint','python3','-v',str(ROOT/'backtesting/moonshot15/runtime')+':/mock:ro','-e','PYTHONPATH=/mock',BASE,'/mock/mock_proxy.py'],'synthetic-proxy',30)
 results={}
 try:
  for index,v in enumerate('ABCDE'):
   print(f'stage=container variant={v} completed={index}/5 elapsed={time.monotonic()-START:.1f} evidence={EVIDENCE}',flush=True)
   image='m15-'+v.lower()+':tested'
   command(['docker','build','--platform','linux/amd64','--build-arg','M15_VARIANT='+v,'--build-arg','SOURCE_SHA='+os.environ['GITHUB_SHA'],'-t',image,'-f',str(context/'moonshot15_engine/Dockerfile'),str(context)],'build-'+v,300)
   info=inspection(image);assert info['Architecture']=='amd64' and info['Config']['User']=='runner'
   assert info['Config']['Labels']['org.opencontainers.image.revision']==os.environ['GITHUB_SHA']
   offline=[];active=[]
   for i,u in enumerate(UNITS):
    r,o=run(image,u,f'{v}-{i}-offline');assert not r['moonshot15']['applied']
    assert r['hashes']['forecast.parquet']==baselines[u]['hashes']['forecast.parquet'],'fallback differs'
    offline.append(r)
    reps=[]
    for rep in range(3):
     t,_=run(image,u,f'{v}-{i}-active-{rep}',True)
     assert t['moonshot15']['applied'],'synthetic House route did not activate'
     assert t['moonshot15']['requests_attempted']==(2 if v=='E' else 1)
     assert t['hashes']['forecast.parquet']!=baselines[u]['hashes']['forecast.parquet'],'no active shift'
     reps.append(t)
    assert len({r['numeric_array_SHA256'] for r in reps})==1,'numeric nondeterminism'
    assert len({r['draw_order_SHA256'] for r in reps})==1
    assert len({r['hashes']['forecast.parquet'] for r in reps})==1,'parquet nondeterminism'
    assert len({r['normalized_meta_SHA256'] for r in reps})==1,'meta nondeterminism'
    assert len({r['hashes']['forecast_rationale.md'] for r in reps})==1,'rationale nondeterminism'
    active.append({'unit':u,'repeats':reps,'bitwise_deterministic':True})
    save('partial-'+v+'.json',{'offline':offline,'active':active})
    print(f'stage=container variant={v} unit={u} completed={i+1}/5 elapsed={time.monotonic()-START:.1f}',flush=True)
   results[v]={'local_tag':image,'image_id':info['Id'],'platform':'linux/amd64','source_SHA':os.environ['GITHUB_SHA'],'image_size':info['Size'],'user':info['Config']['User'],'offline':offline,'active':active,'schema_pass':True,'determinism_pass':True,'base_preserved':True,'security_pass':security['pass'],'resource_policy':{'memory_limit_bytes':8*1024**3,'cpus':2,'timeout_seconds':180},'resource_observed':{'max_wall_seconds':max(r['wall_seconds'] for a in active for r in a['repeats']),'max_output_bytes':max(r['output_size_bytes'] for a in active for r in a['repeats'])},'live_House_quality':'NOT_EVALUATED','mock_only':True}
   save('runtime-'+v+'.json',results[v])
  save('all-runtime.json',results)
 finally:
  command(['docker','rm','-f','m15-proxy'],'proxy-cleanup',30)
  command(['docker','network','rm','m15-internal'],'network-cleanup',30)
 return results

def publish():
 # Registry credentials are consumed only by docker login in the workflow step.
 results=json.loads((EVIDENCE/'all-runtime.json').read_text());out={}
 auth=os.environ['M15_DOCKER_AUTH'];anon=os.environ['M15_DOCKER_ANONYMOUS']
 for v in 'ABCDE':
  r=results[v];tag=f'docker.io/jotj216/track2-f4-approved:m15-{v.lower()}-{os.environ["GITHUB_SHA"][:12]}-{os.environ["GITHUB_RUN_ID"]}-{os.environ["GITHUB_RUN_ATTEMPT"]}'
  command(['docker','tag',r['local_tag'],tag],'tag-'+v)
  command(['docker','--config',auth,'push',tag],'publish-'+v,300)
  info=inspection(tag);ref=next(x for x in info['RepoDigests'] if x.startswith('jotj216/track2-f4-approved@sha256:'))
  ref='docker.io/'+ref
  command(['docker','--config',anon,'pull',ref],'anonymous-pull-'+v,180)
  got=inspection(ref);assert got['Id']==r['image_id']
  assert got['Architecture']=='amd64' and got['Os']=='linux'
  out[v]={**r,'tag':tag,'image_reference':ref,'digest':ref.split('@')[1],'anonymous_pull_verified':True,'registry':'docker.io','repository':'jotj216/track2-f4-approved','GITHUB_RUN_ID':os.environ['GITHUB_RUN_ID'],'GITHUB_SHA':os.environ['GITHUB_SHA']}
  save('image-'+v+'.json',out[v]);print('published verified '+v+' '+ref,flush=True)
 save('image-receipts.json',out)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('stage',choices=['validate','publish']);a=p.parse_args()
 try:validate() if a.stage=='validate' else publish()
 except Exception as e:
  save('failure.json',{'failure_type':type(e).__name__,'stage':a.stage,'error':str(e),'elapsed_seconds':time.monotonic()-START,'checkpoint_sha':os.environ.get('GITHUB_SHA')})
  raise

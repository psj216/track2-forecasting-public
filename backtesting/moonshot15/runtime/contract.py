"""## Executive summary (read this first)
Revalidate existing digests under latest uid65534/64MiB tmpfs/PID256 contract; no rebuild.
"""
from pathlib import Path
import json
import os
import subprocess
import tomllib
import time
from . import factory as f
ROOT=f.ROOT;W=f.WORK/'strict';W.mkdir(parents=True,exist_ok=True)
inputs=json.loads((ROOT/'backtesting/moonshot15/results/strict_image_inputs.json').read_text())['images']
f.EVIDENCE=ROOT/'candidate-artifacts'
rows=[];started=time.monotonic()
try:
 f.command(['docker','network','create','--internal','m15-internal'],'strict-network',30)
 f.command(['docker','run','-d','--name','m15-proxy','--network','m15-internal','--read-only','--tmpfs','/tmp:rw,size=64m','--user','65534:65534','--cap-drop','ALL','--security-opt','no-new-privileges','--entrypoint','python3','-v',str(ROOT/'backtesting/moonshot15/runtime')+':/mock:ro','-e','PYTHONPATH=/mock',f.BASE,'/mock/mock_proxy.py'],'strict-proxy',30)
 for i,v in enumerate('ABCDE'):
  source=inputs[v];image=source['image_reference']
  f.command(['docker','pull',image],'strict-anonymous-pull-'+v,180)
  info=f.inspection(image);assert info['Id']==source['image_id']
  for j,u in enumerate(f.UNITS):
   path=ROOT/'units'/u;asof=tomllib.loads((path/'card.toml').read_text())['provenance']['data_cutoff']
   for active in [False,True]:
    name=f'strict-{v}-{j}-'+str(active);out=W/name;out.mkdir(exist_ok=True);out.chmod(0o777)
    cmd=['docker','run','--rm','--network','m15-internal' if active else 'none','--read-only','--user','65534:65534','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','256','--ulimit','nofile=1024:1024','--ulimit','nproc=256:256','--tmpfs','/tmp:rw,nosuid,nodev,size=64m','--memory','8g','--cpus','2','-e','HOME=/nonexistent','-e','OPENBLAS_NUM_THREADS=1','-e','OMP_NUM_THREADS=1','-v',str(path)+':/input:ro','-v',str(out)+':/output']
    if active:
     for k,val in {'MODEL_ENDPOINT':'http://house.test:8000','MODEL_NAME':'synthetic-house-contract-test','MODEL_TOKEN':'synthetic-testing-only','http_proxy':'http://testuser:testpass@m15-proxy:8080'}.items():cmd+=['-e',k+'='+val]
    cmd+=[image,'forecast','--panels','/input','--text','/input/text','--asof',asof,'--out','/output/forecast.parquet']
    _,wall=f.command(cmd,name,180)
    r=f.gate.validate_output(out,path,asof)
    assert r['hashes']['forecast.parquet']==source['active' if active else 'offline'][u],'strict output changed'
    m=json.loads((out/'forecast_meta.json').read_text())['moonshot15'];assert m['applied']==active
    r.update({'candidate':v,'unit':u,'active_mock_House':active,'wall_seconds':wall,'matches_original_parquet':True,'uid':65534,'tmpfs_bytes':67108864,'PID_limit':256,'output_tree_bytes':sum(p.stat().st_size for p in out.iterdir() if p.is_file())})
    assert r['output_tree_bytes']<=67108864
    rows.append(r);f.save('strict-partial-'+v+'.json',rows)
   print(f'stage=strict-contract candidate={v} unit={u} completed={i*5+j+1}/25 elapsed={time.monotonic()-started:.1f}',flush=True)
 f.save('strict-contract.json',{'executive_summary':'All five exact immutable images pass updated competition-like constraints with bitwise preserved output.','pass':True,'rows':rows,'rebuilt':False,'uid':65534,'tmpfs_bytes':67108864,'PID_limit':256,'source_SHA':os.environ['GITHUB_SHA'],'live_House_quality':'NOT_EVALUATED'})
finally:
 subprocess.run(['docker','rm','-f','m15-proxy'],capture_output=True)
 subprocess.run(['docker','network','rm','m15-internal'],capture_output=True)

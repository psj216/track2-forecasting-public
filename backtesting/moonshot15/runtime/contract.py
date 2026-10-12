"""## Executive summary (read this first)
Compare exact V5.1 and published candidate digests on the SAME strict runner.
Repeat active outputs three times; keep cross-runner hash differences as diagnostics.
No rebuild, no candidate source or forecast-parameter changes.
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
def run(image,u,name,active):
    path=ROOT/'units'/u;asof=tomllib.loads((path/'card.toml').read_text())['provenance']['data_cutoff']
    out=W/name;out.mkdir(exist_ok=True);out.chmod(0o777)
    cmd=['docker','run','--rm','--network','m15-internal' if active else 'none','--read-only','--user','65534:65534','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','256','--ulimit','nofile=1024:1024','--ulimit','nproc=256:256','--tmpfs','/tmp:rw,nosuid,nodev,size=64m','--memory','8g','--cpus','2','-e','HOME=/nonexistent','-v',str(path)+':/input:ro','-v',str(out)+':/output']
    if active:
        for k,val in {'MODEL_ENDPOINT':'http://house.test:8000','MODEL_NAME':'synthetic-house-contract-test','MODEL_TOKEN':'synthetic-testing-only','http_proxy':'http://testuser:testpass@m15-proxy:8080'}.items():cmd+=['-e',k+'='+val]
    cmd+=[image,'forecast','--panels','/input','--text','/input/text','--asof',asof,'--out','/output/forecast.parquet']
    _,wall=f.command(cmd,name,180)
    r=f.gate.validate_output(out,path,asof)
    r.update({'unit':u,'active_mock_House':active,'wall_seconds':wall,'uid':65534,'tmpfs_bytes':67108864,'PID_limit':256,'output_tree_bytes':sum(p.stat().st_size for p in out.iterdir() if p.is_file())})
    assert r['output_tree_bytes']<=67108864
    meta=json.loads((out/'forecast_meta.json').read_text())
    r['moonshot15']=meta.get('moonshot15')
    f.save('last-strict-cell.json',{'name':name,'image':image,'receipt':r})
    return r
try:
    f.command(['docker','pull',f.BASE],'strict-exact-base-anonymous-pull',180)
    f.command(['docker','network','create','--internal','m15-internal'],'strict-network',30)
    f.command(['docker','run','-d','--name','m15-proxy','--network','m15-internal','--read-only','--tmpfs','/tmp:rw,size=64m','--user','65534:65534','--cap-drop','ALL','--security-opt','no-new-privileges','--entrypoint','python3','-v',str(ROOT/'backtesting/moonshot15/runtime')+':/mock:ro','-e','PYTHONPATH=/mock',f.BASE,'/mock/mock_proxy.py'],'strict-proxy',30)
    baselines={}
    for j,u in enumerate(f.UNITS):
        base=[run(f.BASE,u,f'strict-base-{j}-{rep}',False) for rep in range(3)]
        assert len({r['numeric_array_SHA256'] for r in base})==1,'baseline numeric nondeterminism'
        assert len({r['hashes']['forecast.parquet'] for r in base})==1,'baseline parquet nondeterminism'
        baselines[u]=base[0]
        f.save('strict-baseline.json',baselines)
    for i,v in enumerate('ABCDE'):
        source=inputs[v];image=source['image_reference']
        f.command(['docker','pull',image],'strict-anonymous-pull-'+v,180)
        info=f.inspection(image);assert info['Id']==source['image_id']
        for j,u in enumerate(f.UNITS):
            off=run(image,u,f'strict-{v}-{j}-offline',False)
            assert not off['moonshot15']['applied']
            assert off['hashes']['forecast.parquet']==baselines[u]['hashes']['forecast.parquet'],'same-runner fallback changed V5.1 parquet'
            assert off['numeric_array_SHA256']==baselines[u]['numeric_array_SHA256'],'same-runner fallback changed V5.1 arrays'
            active=[run(image,u,f'strict-{v}-{j}-active-{rep}',True) for rep in range(3)]
            assert all(r['moonshot15']['applied'] for r in active),'House route did not activate'
            assert all(r['moonshot15']['requests_attempted']==(2 if v=='E' else 1) for r in active)
            assert len({r['numeric_array_SHA256'] for r in active})==1,'active numeric nondeterminism'
            assert len({r['hashes']['forecast.parquet'] for r in active})==1,'active parquet nondeterminism'
            assert len({r['normalized_meta_SHA256'] for r in active})==1,'active meta nondeterminism'
            assert len({r['hashes']['forecast_rationale.md'] for r in active})==1,'active rationale nondeterminism'
            record={'candidate':v,'unit':u,'offline':off,'active_repeats':active,'same_runner_V51_byte_exact':True,'bitwise_deterministic':True,'prior_runner_offline_parquet_match':off['hashes']['forecast.parquet']==source['offline'][u],'prior_runner_active_parquet_match':active[0]['hashes']['forecast.parquet']==source['active'][u]}
            rows.append(record);f.save('strict-partial-'+v+'.json',rows)
            print(f'stage=strict-contract candidate={v} unit={u} completed={i*5+j+1}/25 elapsed={time.monotonic()-started:.1f}',flush=True)
    f.save('strict-contract.json',{'executive_summary':'Exact images pass current constraints, same-runner V51 fallback byte equality and three clean repeats.','pass':True,'rows':rows,'rebuilt':False,'uid':65534,'tmpfs_bytes':67108864,'PID_limit':256,'source_SHA':os.environ['GITHUB_SHA'],'live_House_quality':'NOT_EVALUATED','cross_runner_equality':'diagnostic only; comparisons across separate execution environments are not a model-preservation gate'})
finally:
    subprocess.run(['docker','rm','-f','m15-proxy'],capture_output=True)
    subprocess.run(['docker','network','rm','m15-internal'],capture_output=True)

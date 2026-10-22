"""Executive summary: exact archived FF03 Docker, one isolated read-only input per forecast."""
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.request

IMAGE='sha256:23f226ced859978d7a3f16a23c6d1515a1a3bdb14338297f4818d114bcfa2c1c'
root=pathlib.Path(os.environ['RUNNER_TEMP'])/'a19-ecb';root.mkdir(exist_ok=True);root.chmod(0o777)
group=sys.argv[1];raw=root/'ecb.zip'
raw.write_bytes(urllib.request.urlopen('https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip',timeout=45).read())
assert hashlib.sha256(raw.read_bytes()).hexdigest()=='93bac351c4a60e612e641150f2392db9f85fe497336ee9d71c4d241f70063eda'
source=pathlib.Path('backtesting/finalalpha19').resolve()
subprocess.run(['docker','run','--rm','--network=none','--read-only','--tmpfs','/tmp:rw,size=256m','-v',str(root)+':/data:rw','-v',str(source)+':/audit:ro',IMAGE,'python3','/audit/prepare_ecb.py','/data/ecb.zip','/data/inputs',group],check=True,timeout=90)
all_receipts=[]
for unit in sorted((root/'inputs').glob('a19-research-*')):
    dest=root/'outputs'/unit.name;dest.mkdir(parents=True,exist_ok=True);dest.chmod(0o777)
    date=unit.name[-10:]
    command=['docker','run','--rm','--platform=linux/amd64','--network=none','--read-only','--tmpfs','/tmp:rw,size=256m','--cpus=2','--memory=4g','--pids-limit=256','-v',str(unit)+':/input:ro','-v',str(dest)+':/output:rw',IMAGE,'forecast','--panels','/input','--text','/input/text','--asof',date,'--out','/output/forecast.parquet','--seed','17','--n-draws','1000']
    start=time.monotonic();r=subprocess.run(command,capture_output=True,text=True,timeout=120)
    rec=dict(id=unit.name,exit=r.returncode,wall_seconds=time.monotonic()-start,command=command,stdout=r.stdout,stderr=r.stderr,
             image=IMAGE,output_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.iterdir() if p.is_file()})
    (dest/'receipt.json').write_text(json.dumps(rec,indent=2));all_receipts.append(rec)
    print(unit.name,r.returncode,round(rec['wall_seconds'],3),flush=True)
    if r.returncode:raise RuntimeError('forecast failure: preserve evidence, no repeated retries')
(root/'execution.json').write_text(json.dumps({'executive_summary':'Actual archived FF03 forecasts; no labels mounted, no candidate image built.','group':group,'runs':all_receipts},indent=2))

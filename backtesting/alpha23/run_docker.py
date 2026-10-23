"""Executive summary: original FF03 and frozen new engine share isolated inputs and exact archived runtime."""
import pathlib,json,subprocess,sys,time,hashlib,os
IMAGE='sha256:23f226ced859978d7a3f16a23c6d1515a1a3bdb14338297f4818d114bcfa2c1c'
chunk=int(sys.argv[1]);root=pathlib.Path('receipts/alpha23').resolve();source=pathlib.Path('backtesting/alpha23').resolve();out=root/'outputs';out.mkdir(exist_ok=True);out.chmod(0o777);recs=[]
for i,unit in enumerate(sorted((root/'inputs').glob('*/card.toml'))):
 if i%4!=chunk:continue
 unit=unit.parent;dest=out/unit.name;dest.mkdir(exist_ok=True);dest.chmod(0o777)
 common=['docker','run','--rm','--platform=linux/amd64','--network=none','--read-only','--tmpfs','/tmp:rw,size=512m','--cpus=2','--memory=4g','--pids-limit=256','-v',str(unit)+':/input:ro','-v',str(dest)+':/output:rw']
 cmd=common+[IMAGE,'forecast','--panels','/input','--text','/input/text','--asof',unit.name[-10:],'--out','/output/forecast.parquet','--seed','17','--n-draws','1000'];start=time.monotonic();r=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
 rec={'id':unit.name,'ff03_exit':r.returncode,'ff03_wall_seconds':time.monotonic()-start,'stderr':r.stderr,'ff03_command':cmd,'image':IMAGE}
 if r.returncode:raise RuntimeError(rec)
 cmd=common+['-v',str(source)+':/audit:ro',IMAGE,'python3','/audit/container_predict.py'];start=time.monotonic();r=subprocess.run(cmd,capture_output=True,text=True,timeout=120);rec.update(candidate_exit=r.returncode,candidate_wall_seconds=time.monotonic()-start,candidate_stderr=r.stderr,candidate_command=cmd)
 rec['input_hashes']={str(p.relative_to(unit)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(unit.rglob('*')) if p.is_file()};rec['output_hashes']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.iterdir() if p.is_file()};(dest/'receipt.json').write_text(json.dumps(rec,indent=2));recs.append(rec);(out/('execution-'+str(chunk)+'.json')).write_text(json.dumps(recs,indent=2));print(unit.name,rec['ff03_exit'],rec['candidate_exit'],flush=True)
 if r.returncode:raise RuntimeError(rec)

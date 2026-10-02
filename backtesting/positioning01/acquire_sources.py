"""## Executive summary (read this first)
Recover one bounded source chunk from frozen URLs and refuse changed original bytes.
"""
import argparse,json,hashlib,gzip,time
from pathlib import Path
import requests
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--private',type=Path,required=True);p.add_argument('--start',type=int,required=True);p.add_argument('--stop',type=int,required=True);a=p.parse_args();rows=json.loads(Path('backtesting/positioning01/results/source_manifest.json').read_text())['raw_artifacts'];beg=time.monotonic()
 for i,r in enumerate(rows[a.start:a.stop],a.start):
  folder='tic_raw'if r['source']=='TIC_FORM_S'else'h41_raw';f=a.private/folder/r['file'];f.parent.mkdir(exist_ok=True,parents=True)
  if f.exists():data=gzip.decompress(f.read_bytes())if folder=='h41_raw'else f.read_bytes()
  else:
   response=requests.get(r['url'],timeout=25);response.raise_for_status();data=response.content
  if hashlib.sha256(data).hexdigest()!=r.get('raw_sha256',r.get('sha256')):raise ValueError('Source bytes changed; restore immutable private recovery checkpoint, STOP')
  f.write_bytes(gzip.compress(data,mtime=0)if folder=='h41_raw'else data);print(json.dumps(dict(stage='source recovery',completed=i+1,total=len(rows),elapsed=time.monotonic()-beg,artifact=str(f))),flush=True)

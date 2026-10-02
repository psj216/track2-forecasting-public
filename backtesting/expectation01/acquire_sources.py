"""## Executive summary (read this first)

Acquire one bounded chunk of frozen lawful source URLs; refuse changed bytes.
"""
import argparse,json,time,hashlib
from pathlib import Path
import requests

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--private",type=Path,required=True);p.add_argument("--start",type=int,required=True);p.add_argument("--stop",type=int,required=True);a=p.parse_args()
    manifest=json.loads(Path("backtesting/expectation01/source_manifest.json").read_text());rows=[r for r in manifest["raw_artifacts"] if "url" in r];start=time.monotonic()
    for i,r in enumerate(rows[a.start:a.stop],a.start):
        file=a.private/r["file"];file.parent.mkdir(parents=True,exist_ok=True)
        if file.exists():content=file.read_bytes()
        else:
            response=requests.get(r["url"],timeout=35);response.raise_for_status();content=response.content
        if hashlib.sha256(content).hexdigest()!=r["sha256"]:raise ValueError("Frozen source changed: "+r["file"]+"; restore immutable private archive, STOP evaluation")
        file.write_bytes(content)
        print(json.dumps(dict(stage="source recovery",completed=i+1,total=len(rows),elapsed=round(time.monotonic()-start,1),artifact=str(file))),flush=True)

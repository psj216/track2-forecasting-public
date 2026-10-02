"""## Executive summary (read this first)
Hash and validate annotations separately before any card outcome load.
"""
import hashlib,json
from pathlib import Path
def digest(path):
 h=hashlib.sha256()
 with open(path,'rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def dump(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(dict(executive_summary='Frozen exposed-card research; no card outcomes or per-card scores public.',**value),indent=2,allow_nan=False)+'\n')
def verify(root):
 r=Path(root)/'backtesting/context01/results';m=json.loads((r/'annotation_manifest.json').read_text())
 for n,h in m['hashes'].items():
  if digest(r/n)!=h:raise ValueError('Annotation/router freeze changed: '+n)
 return m

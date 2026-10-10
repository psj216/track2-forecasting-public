"""Executive summary: immutable expert identities, integrity checks and frozen kill gates.
No router or base forecast model is implemented here.
"""
import hashlib,json
from pathlib import Path
import numpy as np
PARENT='8475c1ac6cd7311ea1cf32e52bdbfab12206f7a9'
BRANCH='track2/last-shot-08-frozen-expert-router'
EXPERTS=('B0','B_NUMERIC','TEXT_LOCATION','R1','R2')
ROOT=Path(__file__).resolve().parents[2]
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def array_digest(x):return hashlib.sha256(np.asarray(x).tobytes()).hexdigest()
def dump(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 if isinstance(value,dict):value={'executive_summary':'Frozen exposed research; aggregate evidence only; no independent OOS claim.',**value}
 path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')
def kill_gate(n,oracle=None):
 if n<3:return 'LIBRARY_TOO_THIN'
 if oracle is None:raise ValueError('Oracle required after technical eligibility')
 if oracle>.75:return 'INSUFFICIENT_EXISTING_EXPERT_HEADROOM'
 return None
def select_whole_card(forecasts,index):return forecasts[index]
def require_pre(private):
 r=json.loads((Path(private)/'PRE_REMOTE_RECEIPT.json').read_text())
 assert r['remote_verified'] is True and r['parent']==PARENT and len(r['PRE_RESULT_LAST_SHOT08_SHA'])==40
 for p,h in r['frozen_files'].items():assert digest(ROOT/p)==h,p
 return r['PRE_RESULT_LAST_SHOT08_SHA']

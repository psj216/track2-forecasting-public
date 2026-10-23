"""Executive summary: run frozen research engines inside archived FF03 runtime; no new image claim."""
import pathlib,json,hashlib
import numpy as np
from inference_adapter import infer
out=pathlib.Path('/output');receipts={}
for name in ['full','ablation']:
 model=json.loads((pathlib.Path('/audit/weights')/(name+'.json')).read_text());x,meta=infer('/input',model);assert np.array_equal(x,infer('/input',model)[0]);assert x.shape==(1000,36);np.save(out/(name+'.npy'),x);receipts[name]={'repeat_identical':True,'provenance':meta,'array_sha256':hashlib.sha256(x.tobytes()).hexdigest()}
(out/'candidate-receipt.json').write_text(json.dumps(receipts,indent=2))

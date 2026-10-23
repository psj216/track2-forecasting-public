"""Executive summary: independent ALPHA23 research draws and provenance, no live training."""
import json,pathlib,sys,tomllib,hashlib,time
import numpy as np
import pandas as pd
from engine import predict
from feature_builder import ASSETS

def infer(unit,model):
 unit=pathlib.Path(unit);card=tomllib.loads((unit/'card.toml').read_text());frame=pd.read_parquet(unit/'rates_daily.parquet');frame['date']=pd.to_datetime(frame.date)
 p=frame.pivot(index='date',columns='asset',values='value').reindex(columns=ASSETS);docs=json.loads((unit/'policy.json').read_text());asof=card['provenance']['data_cutoff']
 # All features need at most61 observations;121 retains guard-window context too.
 p=p.loc[:asof].tail(121)
 x,meta=predict(p,docs,asof,model);return x,meta
if __name__=='__main__':
 root=pathlib.Path(sys.argv[1]);weights=pathlib.Path(sys.argv[2]);out=pathlib.Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True);start=time.monotonic();receipts=[]
 models={n:json.loads((weights/(n+'.json')).read_text()) for n in ['full','ablation']}
 for i,card in enumerate(sorted(root.glob('*/card.toml'))):
  unit=card.parent;rec={'id':unit.name}
  for name,model in models.items():
   x,meta=infer(unit,model);assert np.array_equal(x,infer(unit,model)[0]);dest=out/unit.name;dest.mkdir(exist_ok=True);np.save(dest/(name+'.npy'),x);rec[name]={'shape':list(x.shape),'sha256':hashlib.sha256(x.tobytes()).hexdigest(),'repeat_identical':True,'provenance':meta}
  receipts.append(rec);(out/'forecast-manifest.json').write_text(json.dumps(receipts,indent=2))
  if i%10==0:print('forecast',i+1,'elapsed',round(time.monotonic()-start,2),flush=True)

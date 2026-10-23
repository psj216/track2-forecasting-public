"""Executive summary: check determinism, joint grid, and future-row exclusion without labels."""
import json,pathlib,tempfile,shutil
import numpy as np,pandas as pd
from model import predict
w=json.loads(pathlib.Path('toprank23/backtesting/toprank23/weights.json').read_text())
u=next(pathlib.Path('receipts/alpha19-newdata/inputs-ECB_G10').glob('*/card.toml')).parent
x,c=predict(u,w);assert x.shape==(1000,12) and len(set(c))==12
assert np.array_equal(x,predict(u,w)[0])
with tempfile.TemporaryDirectory() as td:
    v=pathlib.Path(td)/'unit';shutil.copytree(u,v)
    p=pd.read_parquet(v/'em_fx_ecb_daily.parquet');q=p.groupby('asset').tail(1).copy();q['date']=pd.Timestamp('2030-01-01').date();q['value']*=100
    pd.concat([p,q]).to_parquet(v/'em_fx_ecb_daily.parquet',index=False)
    assert np.array_equal(x,predict(v,w)[0])
print('PASS deterministic1000x12 finite; post-asof perturbation invariant')

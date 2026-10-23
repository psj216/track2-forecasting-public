"""Executive summary: tests deterministic full joint paths and future-row exclusion without labels."""
import pathlib,pickle,tempfile,shutil,json
import numpy as np,pandas as pd
from model import predict,training_arrays
models=pickle.loads(pathlib.Path('/tmp/toprank24-model.pkl').read_bytes())
u=next(pathlib.Path('receipts/alpha19-newdata/inputs-ECB_G10').glob('*/card.toml')).parent
x,c,s=predict(u,models);assert x.shape==(1000,12) and len(set(c))==12 and np.isfinite(x).all()
assert np.array_equal(x,predict(u,models)[0])
with tempfile.TemporaryDirectory() as td:
    v=pathlib.Path(td)/'unit';shutil.copytree(u,v);p=pd.read_parquet(v/'em_fx_ecb_daily.parquet');q=p.groupby('asset').tail(1).copy();q['date']=pd.Timestamp('2030-01-01').date();q['value']*=100
    pd.concat([p,q]).to_parquet(v/'em_fx_ecb_daily.parquet',index=False);assert np.array_equal(x,predict(v,models)[0])
try:
    training_arrays(pd.DataFrame({'A':[1.]},index=[pd.Timestamp('2025-01-01')]))
except AssertionError:pass
else:raise AssertionError('post2023 training data accepted')
print('PASS finite joint grid, repeatability, postasof perturbation, post2023 training rejection')

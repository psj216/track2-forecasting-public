"""Executive summary: leakage, conditional policy, grid and repeatability checks before evaluation."""
import pathlib,json,tempfile,shutil,sys
import numpy as np,pandas as pd
sys.path.insert(0,str(pathlib.Path(__file__).parents[1]))
from inference_adapter import infer
from feature_builder import build
from policy_signal import features
root=pathlib.Path('receipts/alpha23');u=next((root/'inputs').glob('*/card.toml')).parent;w=json.loads(pathlib.Path('alpha23/backtesting/alpha23/weights/full.json').read_text())
x,meta=infer(u,w);assert x.shape==(1000,36) and np.isfinite(x).all() and np.array_equal(x,infer(u,w)[0])
with tempfile.TemporaryDirectory() as td:
 v=pathlib.Path(td)/'unit';shutil.copytree(u,v);p=pd.read_parquet(v/'rates_daily.parquet');q=p.groupby('asset').tail(1).copy();q['date']=pd.Timestamp('2030-01-01').date();q.value*=100;pd.concat([p,q]).to_parquet(v/'rates_daily.parquet',index=False)
 ds=json.loads((v/'policy.json').read_text());ds.append({'active':'2030-01-01','date':'2029-12-31','sha256':'future','kind':'fomc_statement','signals':[1e6]*8});(v/'policy.json').write_text(json.dumps(ds));assert np.array_equal(x,infer(v,w)[0])
# Publication date-only activates NEXT business day, including Friday -> Monday.
doc={'active':'2025-01-06','date':'2025-01-03','sha256':'x','kind':'fomc_statement','signals':[1.]*8}
f=features(pd.DatetimeIndex(['2025-01-03','2025-01-06']),[doc]);assert f.iloc[0].policy_tightening==0 and f.iloc[1].policy_tightening==1
p=pd.read_parquet(u/'rates_daily.parquet');p['date']=pd.to_datetime(p.date);p=p.pivot(index='date',columns='asset',values='value');ds=json.loads((u/'policy.json').read_text());a,_=build(p,ds);b,_=build(p.tail(121),ds);assert np.allclose(a.iloc[-1],b.iloc[-1],rtol=1e-8,atol=1e-8)
assert np.linalg.eigvalsh(np.array(w['covariance'])).min()>0
r=json.loads(pathlib.Path('alpha23/backtesting/alpha23/weights/training-receipt.json').read_text());assert r['max_target_date']<'2024-01-01'
print('PASS shape finite determinism future-price/text invariance nextBD activation feature-window equivalence PSD target-cutoff')

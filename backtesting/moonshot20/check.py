"""Container-side assertions; no targets/answers are read."""
import json,pathlib,sys,tomllib
import numpy as np
import pandas as pd
sys.path.insert(0,'/opt/moonshot20')
from adapter import anchors_for,transform
from qfbench2_track_forecasting import cli
kind=sys.argv[1]
a=pd.read_parquet('/baseline/forecast.parquet');b=pd.read_parquet('/output/forecast.parquet')
assert list(a.columns)==list(b.columns)
assert a.drop(columns='value').equals(b.drop(columns='value'))
assert np.isfinite(b.value).all() and len(b)==len(a)
assert set(p.name for p in pathlib.Path('/output').iterdir())=={'forecast.parquet','forecast_meta.json','forecast_rationale.md'}
if kind=='monthly':
 for p in pathlib.Path('/baseline').iterdir():
  assert p.read_bytes()==(pathlib.Path('/output')/p.name).read_bytes(),p.name
else:
 c=tomllib.loads(pathlib.Path('/input/card.toml').read_text())
 anchors=anchors_for(c,cli._read_panels(pathlib.Path('/input')),c['provenance']['data_cutoff'])
 expected=transform(a,anchors,c['targets'],17)
 assert np.array_equal(expected.value.to_numpy(),b.value.to_numpy())
 draws=np.sort(a.draw.unique());selected=np.random.default_rng(17).permutation(draws)[:700]
 assert len(selected)==700
 assert a.loc[~a.draw.isin(selected)].equals(b.loc[~b.draw.isin(selected)])
 assert (a.value!=b.value).any()
 # Input-only negative controls, with no changes to the locked candidate.
 for freq,target in [('monthly','level'),('daily','return')]:
  cc={'targets':dict(c['targets'],target_frequency=freq,target_type=target)}
  try: anchors_for(cc,{},c['provenance']['data_cutoff'])
  except ValueError: pass
  else: raise AssertionError('unsupported target accepted')
 print(json.dumps({'selected_joint_draws':700,'unchanged_joint_draws':300,'changed_cells':int((a.value!=b.value).sum())}))
print(kind+' CHECK PASS')

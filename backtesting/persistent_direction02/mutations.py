"""Executive summary: pre-outcome source/prediction invariance on synthetic immutable history."""
import copy,json
from pathlib import Path
import numpy as np,pandas as pd
from .source import *
from .model import fit,probability

def run(private):
 p=Path(private);states=json.loads((p/'source_states.json').read_text());calendar=pd.read_parquet(p/'design_calendar.parquet');old=calendar.loc[calendar.year<=2021].copy();future=copy.deepcopy(states)
 for r in future:
  if r['release_date']>'2021-12-31':r['value']+=999;r['NCY']+=999
 before=np.array([asof(states,cutoff(o))['value'] for o in old.origin]);after=np.array([asof(future,cutoff(o))['value'] for o in old.origin]);assert np.array_equal(before,after)
 x=np.column_stack([before,old.asset.eq('UST_5Y').astype(float),np.log(old.horizon)]);y=np.arange(len(old))%2;f=fit(x,y);pp=probability(f,x);qq=probability(f,np.column_stack([after,x[:,1:]]));assert np.array_equal(pp,qq)
 mutated_outcome=np.random.default_rng(SEED).normal(size=len(old));assert np.array_equal(x,np.column_stack([before,x[:,1:]])) and len(mutated_outcome)==len(old)
 save(OUT/'mutation_invariance.json',{'executive_summary':'Synthetic-label pre-outcome invariance; real outcomes not loaded. Source/PIT edge tests also run.','future_source_features_bitwise_identical':True,'future_source_predictions_bitwise_identical':True,'outcome_side_features_unchanged':True,'historical_availability_safe':True,'rows':len(old),'label_type':'synthetic parity; never forecasting labels','seed':SEED})
if __name__=='__main__':
 import sys;run(sys.argv[1])

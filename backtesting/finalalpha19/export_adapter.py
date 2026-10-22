"""Executive summary: separate research adapter over completed FF03 outputs; no labels.

Reads one supplied card and baseline output. Writes a new output directory, never baseline.
"""
import json
import pathlib
import shutil
import sys
import tomllib
import numpy as np
import pandas as pd
from m0 import hedge
from qfbench2_track_forecasting.grid import grid_from_card,build_sample_matrix
from qfbench2_track_forecasting.limits import inspect_parquet,DEFAULT_LIMITS


def export(unit,baseline,out):
    unit,baseline,out=map(pathlib.Path,(unit,baseline,out))
    if out.resolve()==baseline.resolve():raise ValueError('baseline overwrite forbidden')
    out.mkdir(parents=True,exist_ok=True)
    card=tomllib.loads((unit/'card.toml').read_text());grid=grid_from_card(card)
    meta=json.loads((baseline/'forecast_meta.json').read_text())
    forecast=baseline/'forecast.parquet'
    facts=inspect_parquet(forecast,limits=DEFAULT_LIMITS,what='forecast.parquet')
    a=build_sample_matrix(forecast,facts,grid,meta['n_draws'],limits=DEFAULT_LIMITS)
    b,trace=hedge(unit,a)
    if not trace['applied']:
        for f in ('forecast.parquet','forecast_meta.json','forecast_rationale.md'):shutil.copyfile(baseline/f,out/f)
    else:
        cells=grid.cells();n,d=b.shape
        pd.DataFrame({'draw':np.repeat(np.arange(n),d),'asset':np.tile([c[0] for c in cells],n),
             'horizon':np.tile([c[1] for c in cells],n),'value':b.ravel()}).to_parquet(out/'forecast.parquet',index=False)
        meta['forecast_mode']='m0-hedge-10-research'
        meta['numeric_model']='90 percent FF03 joint rows plus10 percent documented M0 joint rows'
        meta['numeric_experiment']='FINAL-ALPHA-19'
        (out/'forecast_meta.json').write_text(json.dumps(meta,indent=2)+'\n')
        rationale=(baseline/'forecast_rationale.md').read_text()
        (out/'forecast_rationale.md').write_text(rationale+'\n\nResearch adapter: fixed whole-scenario90/10 FF03/M0 mixture. All original text decisions are inherited; M0 is input-only and text-blind.\n')
    (out.parent/(out.name+'.adapter-receipt.json')).write_text(json.dumps({'executive_summary':'Separate non-promoted adapter output; no labels read.','applied':trace['applied'],'reason':trace.get('reason'),'n_draws':len(b)},indent=2))
    return trace

if __name__=='__main__':export(*sys.argv[1:])

"""## Executive summary (read this first)

Verify a frozen CEILING-01 diagnostic contract.
"""

import os,subprocess,sys,tomllib
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from backtesting.ceiling01.build_baseline_ledger import card_draws

@pytest.mark.parametrize('family',['F1','F2','F3','F4'])
def test_baseline_exact_reproduction_with_cli(family,tmp_path):
 root=Path(__file__).resolve().parents[1]
 unit=next(iter(sorted((root/'units').glob('t2-'+family+'-*'))))
 card=tomllib.loads((unit/'card.toml').read_text());t=card['targets'];assets=t['asset_ids'];horizons=t['horizons']
 direct=card_draws(unit,card)
 out=tmp_path/'forecast.parquet';env=os.environ.copy();env['FORECAST_MODE']='text-first-v5.1';env['NUMERIC_VARIANT']='v3'
 subprocess.run([sys.executable,'-m','qfbench2_track_forecasting.cli','--panels',str(unit),'--text',str(unit/'text'),'--asof',str(card['provenance']['data_cutoff']),'--out',str(out),'--n-draws','2000','--seed','19'],check=True,env=env,capture_output=True)
 frame=pd.read_parquet(out);index=pd.MultiIndex.from_product([sorted(frame.draw.unique()),assets,horizons],names=['draw','asset','horizon'])
 cli=frame.set_index(['draw','asset','horizon']).value.reindex(index).to_numpy().reshape(2000,len(assets),len(horizons)).transpose(0,2,1)
 np.testing.assert_array_equal(direct,cli)

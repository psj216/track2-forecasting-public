"""Executive summary: verify calendar origins, complete cells and official CRPS control."""
import pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import fomc_historical_exam as e
import numpy as np
import pandas as pd
def test_fixed_origins():
    c=e.dates()
    assert len(c)==15
    assert [x['asof'] for x in c if x['group']=='fomc']==['2022-06-13','2023-03-20','2024-09-16','2025-09-15','2026-09-14']
    assert all(x['targets'][1]==x['pseudo_event'] for x in c)
def test_canonical_order():
    f=pd.DataFrame({'asset_id':['UST_2Y','UST_2Y'],'horizon':[1,1],'sample_id':[1,0],'sample':[4.,3.]})
    assert e.canon(f)['value'].tolist()==[3.,4.]
def test_official_crps_point_control():
    sys.path.insert(0,str(pathlib.Path.cwd()/'common-current'/'common'))
    from qfbench2_common.scoring.crps import crps_ensemble
    assert float(crps_ensemble(np.full(2000,4.),4.25))==.25

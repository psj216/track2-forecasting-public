"""Executive summary: enforce PIT states, whole scenarios, fixed gates and safe baseline protection."""
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from backtesting.new_mechanism_moonshot12.core import (
    BRANCH, DRAW_COUNT, FEATURE_NAMES, KS, MAIN, MIN_ANALOGS, MIN_COVERAGE,
    ORACLE_MEMBERS, PARENT, SEED, eligible_paths, fingerprint, gate1, gate2,
    joint_draws, map_innovations, normalize_history, oracle_search, shared_distances,
)

ROOT=Path(__file__).resolve().parents[1]


def synthetic():
    dates=pd.bdate_range('1998-01-01',periods=700)
    t=np.arange(len(dates),dtype=float)
    series={'UST_2Y':pd.Series(2+.02*np.sin(t/7)+.0002*t,index=dates),
            'MKT':pd.Series(.1*np.sin(t/13),index=dates)}
    return dates,series,{'UST_2Y':'level','MKT':'log_return'}


def test_fixed_constants():
    assert KS==(8,16,32,64)
    assert SEED==31812 and MIN_ANALOGS==8 and MIN_COVERAGE==.80
    assert ORACLE_MEMBERS==8 and DRAW_COUNT==1000
    assert FEATURE_NAMES==('move5','move21','move63','move126','vol21','vol63','trend21','range126')


def test_exact_parent_branch():
    assert subprocess.check_output(['git','rev-parse',PARENT],cwd=ROOT,text=True).strip()==PARENT
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()==BRANCH


def test_main_unchanged():
    assert subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip()==MAIN


def test_safe_candidate_code_unchanged():
    changed=subprocess.check_output(['git','diff',PARENT,'--name-only','--','qfbench2_track_forecasting','.github/workflows/v51-delivery-emergency11.yml','backtesting/v51_delivery_emergency11'],cwd=ROOT,text=True)
    assert changed==''


def test_future_source_mutation():
    dates,series,kinds=synthetic();cut=dates[500];origins=dates[400:501:5]
    before,scale_before=fingerprint(series,kinds,origins)
    changed={a:s.copy() for a,s in series.items()}
    for s in changed.values():s.loc[s.index>cut]=1e8
    after,scale_after=fingerprint(changed,kinds,origins)
    pd.testing.assert_frame_equal(before,after,check_exact=True)
    pd.testing.assert_frame_equal(scale_before,scale_after,check_exact=True)


def test_prefix_rebuild_identical():
    dates,series,kinds=synthetic();origins=dates[400:501:5]
    full,scale=fingerprint(series,kinds,origins)
    small,scale2=fingerprint({a:s.loc[:origins[-1]] for a,s in series.items()},kinds,origins)
    pd.testing.assert_frame_equal(full,small,check_exact=True)
    pd.testing.assert_frame_equal(scale,scale2,check_exact=True)


def test_normalizer_uses_history_only():
    history=pd.DataFrame({'a':[1.,2.,3.,4.],'b':[8.,8.,8.,8.]});q=pd.Series({'a':1000.,'b':8.})
    transformed,query=normalize_history(history,q)
    np.testing.assert_allclose(transformed.a,[-1,-1/3,1/3,1])
    assert query.a==(1000-2.5)/1.5
    assert np.isfinite(transformed.b).all()


def test_eligibility_requires_entire_path_matured():
    end=np.array([['2010-01-01','2010-02-01'],['2010-01-01','2010-03-01'],['2010-01-01','NaT']],dtype='datetime64[ns]')
    eligible=eligible_paths(end,np.ones((3,2)),'2010-03-01')
    assert eligible.tolist()==[True,False,False]


def test_missing_target_no_partial_path():
    end=np.full((2,2),np.datetime64('2000-01-01'),dtype='datetime64[ns]')
    assert eligible_paths(end,[[1.,2.],[1.,np.nan]],'2001-01-01').tolist()==[True,False]


def test_business_day_endpoint_strictness():
    origin=pd.Timestamp('2020-01-03');endpoint=origin+pd.offsets.BDay(5)
    assert endpoint==pd.Timestamp('2020-01-10')
    end=np.array([[endpoint]],dtype='datetime64[ns]')
    assert not eligible_paths(end,[[1]],endpoint)[0]
    assert eligible_paths(end,[[1]],endpoint+pd.offsets.BDay(1))[0]


def test_level_mapping_and_unscaled_return():
    got=map_innovations(np.array([[2.,.03],[-1.,-.02]]),['level','log_return'],np.array([5.,0]),np.array([.1,99.]))
    np.testing.assert_array_equal(got,np.array([[5.2,.03],[4.9,-.02]]))


def test_joint_draw_indices_never_mix_components():
    paths=np.array([[i,10*i,-i] for i in range(16)])
    draws,indices=joint_draws(paths,np.arange(8),27)
    np.testing.assert_array_equal(draws,paths[indices])
    np.testing.assert_array_equal(draws[:,1],10*draws[:,0])
    np.testing.assert_array_equal(draws[:,2],-draws[:,0])


def test_draw_determinism():
    paths=np.arange(48).reshape(16,3)
    a,i=joint_draws(paths,np.arange(8),19);b,j=joint_draws(paths,np.arange(8),19)
    np.testing.assert_array_equal(a,b);np.testing.assert_array_equal(i,j)


def test_draw_function_has_no_outcome_argument():
    import inspect
    assert 'truth' not in inspect.signature(joint_draws).parameters
    assert 'truth' not in inspect.signature(shared_distances).parameters


def test_no_outcome_metric_in_retrieval():
    h=pd.DataFrame(np.arange(30).reshape(5,6),dtype=float);q=h.iloc[3].copy()
    d,c=shared_distances(h,q)
    assert d[3]==0 and (c==1).all()


def test_missing_coverage_cutoff():
    h=pd.DataFrame([[1.,2.,3.,4.,5.],[1.,np.nan,np.nan,4.,5.],[2.,3.,4.,5.,6.]])
    q=pd.Series([2.,3.,4.,5.,6.]);d,c=shared_distances(h,q)
    assert np.isinf(d[1]) and c[1]==.6


def test_point_oracle_whole_origin():
    paths=np.array([[1.,10.],[2.,20.],[3.,30.]])
    loss,selected,curve=oracle_search(paths,np.array([2.1,21.]),np.ones(2))
    assert len(loss)==2 and len(curve)==8
    assert set(selected)<=set(range(3))


@pytest.mark.parametrize('ratio,expected',[(.65,True),(.6500001,False),(.5,True)])
def test_gate1_fixed_boundary(ratio,expected):
    assert gate1(ratio)==expected


def test_gate1_joint_boundary():
    assert gate1(.6,.7) and not gate1(.6,.700001)


def test_gate2_all_conditions():
    s=dict(ratio=.85,equal_year_ratio=.90,improved_years=6,max_year_gross_share=.35,max_asset_gross_share=.35,origin_upper95=.99,random_p=.05)
    assert gate2(s)
    for k,v in [('ratio',.86),('equal_year_ratio',.91),('improved_years',5),('max_year_gross_share',.36),('max_asset_gross_share',.36),('origin_upper95',1.),('random_p',.051)]:
        assert not gate2({**s,k:v})


def test_spec_no_card_selection_or_hybrid():
    path=ROOT/'backtesting/new_mechanism_moonshot12/results/experiment_spec.json'
    spec=json.loads(path.read_text())
    assert spec['parent']==PARENT
    assert spec['k_selection_years']==list(range(2009,2016))
    assert spec['historical_evaluation_years']==list(range(2016,2025))
    assert spec['optional_hybrid'].startswith('NOT_FROZEN')
    assert spec['independent_OOS'] is False


def test_no_card_loader_in_run_module():
    import backtesting.new_mechanism_moonshot12.run as run
    source=Path(run.__file__).read_text()
    assert "cards.json" not in source and 'read_parquet' in source


def test_similarity_control_selection():
    from backtesting.new_mechanism_moonshot12.historical import selection_indices
    d=np.arange(12,dtype=float);donors=np.arange(12)
    assert selection_indices(d,donors,8).tolist()==list(range(8))
    assert selection_indices(d,donors,8,'REVERSED_SIMILARITY').tolist()==list(range(11,3,-1))
    assert selection_indices(d,donors,8,'CONSTANT_RECENT').tolist()==list(range(11,3,-1))


def test_nulls_have_only_past_donors_and_fixed_seed():
    from backtesting.new_mechanism_moonshot12.historical import random_indices
    donors=np.arange(100,700);selected=np.arange(32)
    for kind in ['RANDOM_ANALOG','TIME_MATCHED_RANDOM','DISTANCE_SHUFFLE']:
        a=random_indices(len(donors),32,donors,selected,kind,np.random.default_rng(SEED),900)
        b=random_indices(len(donors),32,donors,selected,kind,np.random.default_rng(SEED),900)
        np.testing.assert_array_equal(a,b)
        assert len(a)==32 and len(set(a))==32 and (donors[a]<900).all()


def test_K_selection_excludes_evaluation_years():
    import backtesting.new_mechanism_moonshot12.historical as h
    source=Path(h.__file__).read_text()
    assert 'range(2009,2016)' in source
    assert 'cards.json' not in source and 'MOONSHOT12' not in source


def test_private_outcomes_cannot_be_saved_inside_repository(monkeypatch):
    from backtesting.new_mechanism_moonshot12.run import private
    monkeypatch.setenv('MOONSHOT12_PRIVATE',str(ROOT/'forbidden-private'))
    with pytest.raises(AssertionError):private()


def test_tied_range_state_is_deterministic():
    dates=pd.bdate_range('1998-01-01',periods=400)
    series={'UST_2Y':pd.Series(np.ones(len(dates)),index=dates)}
    states,_=fingerprint(series,{'UST_2Y':'level'},dates[-10:])
    np.testing.assert_array_equal(states['UST_2Y:range126'],np.full(10,.5))


def test_ancestor_files_preserved():
    changed=subprocess.check_output(['git','diff',PARENT,'--name-only'],cwd=ROOT,text=True).splitlines()
    assert all(x.startswith('backtesting/new_mechanism_moonshot12/') or x=='tests/test_new_mechanism_moonshot12.py' or x=='NEW-MECHANISM-MOONSHOT-12-report.md' for x in changed)

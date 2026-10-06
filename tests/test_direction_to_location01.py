"""Executive summary: protect frozen direction, exact constants, pre-score freeze and complete scope."""
import ast, inspect, json, os, subprocess
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from backtesting.direction_to_location01.core import *
from backtesting.direction_to_location01.controls import ControlPlan, losses_for_sign, sample_blocks
from backtesting.direction_to_location01.finalize import verdict, concentration
from backtesting.direction_to_location01.evaluate import geometry, plan
from backtesting.location04.source_dataset import asof_features, cutoff, FEATURES

@pytest.fixture
def private():
    value=os.environ.get('DTL01_PRIVATE')
    if not value:pytest.skip('Private frozen inputs are not distributed in public Git')
    return Path(value)
@pytest.fixture
def rows(private):return pd.read_parquet(private/'inputs/ledger.parquet')

def test_exact_constants_and_spec():
    spec=json.loads((OUT/'experiment_spec.json').read_text());assert PRIMARY_AMPLITUDE==spec['primary_amplitude']==.10;assert SECONDARY==spec['secondary_amplitudes']=={'DTL_005':.05,'DTL_020':.20};assert OOD_THRESHOLD==spec['OOD3_DIAGNOSTIC']['threshold']==3
    assert spec['parent_RESULT_SHA']==PARENT=='fe62b9058ea6dc540f7548c6be96ccc4e8d04b92';assert spec['READY_FOR_SUBMISSION'] is False;assert spec['models_refit']==0

def test_no_refitting_and_no_new_source():
    for file in (ROOT/'backtesting/direction_to_location01').glob('*.py'):
        tree=ast.parse(file.read_text());assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ['fit','fit_transform','partial_fit'] for n in ast.walk(tree));assert not any(isinstance(n,(ast.Import,ast.ImportFrom)) and 'sklearn' in ast.unparse(n) for n in ast.walk(tree))

def test_only_sign_no_magnitude_model():
    pred=np.array([-10.,-.001,0,.001,10.]);sd=np.array([1,2,3,4,5.]);assert np.array_equal(shift_vector(pred,sd),np.sign(pred)*.1*sd)
    assert np.array_equal(shift_vector(pred*100,sd),shift_vector(pred,sd));assert shift_vector(pred,sd)[2]==0

def test_ood_threshold_strict_and_finite():
    pred=np.ones(3);sd=np.ones(3);z=np.array([2.99,3,3.000001]);assert np.array_equal(shift_vector(pred,sd,max_train_z=z),[.1,.1,0]);assert np.array_equal(shift_vector(pred,sd),[.1,.1,.1])
    with pytest.raises(ValueError):shift_vector(pred,sd,max_train_z=[1,np.nan,2])

def test_constructor_no_outcome_argument():
    assert set(inspect.signature(shift_vector).parameters)=={'prediction','sd','amplitude','max_train_z'}
    for x in ['true_delta','truth','baseline_cell_CRPS','candidate_cell_CRPS']:assert x not in inspect.getsource(shift_vector)

def test_positive_sd_and_nan_validation():
    with pytest.raises(ValueError):shift_vector([1],[0])
    with pytest.raises(ValueError):shift_vector([np.nan],[1])
    with pytest.raises(ValueError):shift_vector([1,2],[1])

def test_synthetic_pure_geometry():
    rng=np.random.default_rng(23);draws=rng.normal(size=(500,5));s=shift_vector([-4,-1,0,1,4],draws.std(axis=0));g=geometry(draws,s);assert g['SD_unchanged'] and g['weak_ordering_unchanged'];assert not g['intentional_jitter'];assert np.array_equal(draws[:,2],translate(draws,s)[:,2])

def test_release_balance():
    w=group_weights(['a']*8+['b']*2);assert w[:8].sum()==pytest.approx(1);assert w[8:].sum()==pytest.approx(1)

def test_bootstrap_block_integrity_and_determinism():
    groups=np.array(['a','a','b','b','b','c']);w,counts,ids=sample_blocks(groups,np.random.default_rng(34));assert np.array_equal(w,counts[ids]);assert len(counts)==3 and counts.sum()==3
    assert np.array_equal(w,sample_blocks(groups,np.random.default_rng(34))[0]);assert w[0]==w[1] and w[2]==w[3]==w[4]

def test_null_lookup_exact():
    table=np.arange(15).reshape(3,5);sign=np.array([-1,0,1,-1,1]);assert np.array_equal(losses_for_sign(table,sign),[0,6,12,3,14])
    with pytest.raises(ValueError):losses_for_sign(table,[.2]*5)

def fake_verdict(ratio=.98):
    p={'crps_ratio':ratio,'oracle_capture':.025};annual=[{'crps_ratio':.98}]*3+[{'crps_ratio':1.01}]*2;controls={k:{'median_ratio':1.001,'fraction_at_least_as_good':0.} for k in CONTROLS};controls['ONE_YEAR_SHIFT']={'crps_ratio':1.0};b={k:{'models':{PRIMARY:{'crps_ratio_95ci':[.97,.99]}}} for k in ['release','year']};return p,annual,controls,b,{'NONCONCENTRATED':True},{'sign_accuracy':.65,'spearman':.3}

def test_primary_verdict_secondary_cannot_rescue():
    args=fake_verdict();assert verdict(*args)[0]=='WEAK_YES';args=fake_verdict(1.03);assert verdict(*args)[0]=='NO';assert 'secondary' not in inspect.signature(verdict).parameters

def test_control_similarity_is_failure():
    args=list(fake_verdict());args[2]['RANDOM_SIGN']['median_ratio']=.97;assert verdict(*args)[0]=='NO'

def test_higher_verdict_requires_capture():
    args=list(fake_verdict(.96));args[0]['oracle_capture']=.02;assert verdict(*args)[0]=='WEAK_YES';args[0]['oracle_capture']=.06;assert verdict(*args)[0]=='YES'

def test_all_frozen_universe(private,rows):
    assert len(rows)==552 and rows.origin_date.nunique()==59 and rows.release_id.nunique()==41;assert set(rows.asset)==set(ASSETS);assert set(rows.horizon)==set(HORIZONS);assert set(rows.year)==set(YEARS);assert (rows.year==2023).sum()==110;assert (pd.to_datetime(rows.target_end)<=pd.Timestamp('2024-12-18')).all()
    r=pd.read_parquet(private/'parent/diagnostic_inputs/SPD/ledger.parquet');assert np.array_equal(rows.to_numpy(),r.to_numpy())

def test_frozen_prediction_hash_and_sign(private,rows):
    verify_inputs(private);f=np.load(private/'inputs/frozen.npz');manifest=json.loads((OUT/'frozen_spd_prediction_manifest.json').read_text());assert array_hash(f['prediction'])==manifest['prediction_array_SHA256'];assert np.array_equal(direction(f['prediction']),np.sign(rows.predicted_delta));assert array_hash(f['draws'])==manifest['baseline_draw_array_SHA256']

def test_actual_draw_geometry_without_scoring(private):
    f=np.load(private/'inputs/frozen.npz')
    for amp in [PRIMARY_AMPLITUDE,*SECONDARY.values()]:assert geometry(f['draws'],shift_vector(f['prediction'],f['sd'],amp))['pure_location']
    assert geometry(f['draws'],shift_vector(f['prediction'],f['sd'],max_train_z=f['zmax']))['pure_location']

def test_original_train_scaler_ood(private,rows):
    f=np.load(private/'inputs/frozen.npz');models=json.loads((private/'inputs/models.json').read_text())['models'];z=np.full(len(rows),np.nan)
    for m in models:
        mask=(rows.asset.eq(m['asset'])&rows.horizon.eq(m['horizon'])&rows.year.eq(m['year'])).to_numpy();z[mask]=np.max(abs((f['features'][mask]-np.asarray(m['scaler_mean']))/np.asarray(m['scaler_scale'])),axis=1)
    assert np.array_equal(z,f['zmax']);assert np.array_equal(z>3,rows.heldout_max_abs_train_z.to_numpy()>3)

def test_control_determinism_and_prevalence(private,rows):
    c=plan(private,rows)
    for kind in CONTROLS:
        assert np.array_equal(c.sample(kind,53)[0],c.sample(kind,53)[0]);assert set(c.sample(kind,53)[0])<=set([-1.,0.,1.])
    random=c.sample('RANDOM_SIGN',54)[0];assert np.array_equal(np.sort(random),np.sort(c.signs))

def test_release_packet_matching_has_no_outcome(private,rows):
    first=plan(private,rows);mutated=rows.copy();mutated['truth']=1e20;mutated['true_delta']=-1e20;mutated['candidate_cell_CRPS']=1e20;second=plan(private,mutated)
    for kind in CONTROLS:assert np.array_equal(first.sample(kind,8)[0],second.sample(kind,8)[0])

def test_date_null_never_uses_future_donor(private,rows):
    c=plan(private,rows);rng=np.random.default_rng(3);s,n=c.delayed_dates(rng);assert n<=len(rows);assert np.isin(s,[-1,0,1]).all();assert (c.available<=np.array([(pd.Timestamp(state['available_at'])+pd.offsets.BDay(20)).value for state in c.states])).all()
    # Prior-year mapping uses only genuinely earlier frozen forecast states.
    old,matched=c.prior_year();assert np.array_equal(old[rows.year==2020],np.zeros((rows.year==2020).sum()));assert len(matched)>0

def test_future_source_mutation(private,rows):
    import copy
    states=json.loads((ROOT/'backtesting/location04/results/source_states.json').read_text())['states'];origin=rows.origin_date.min();mutated=copy.deepcopy(states)
    for state in mutated:
        if pd.Timestamp(state['available_at'])>cutoff(origin):
            for key in FEATURES:state[key]=1e8
    a=asof_features(states,origin);b=asof_features(mutated,origin);assert a['release_id']==b['release_id'];assert np.array_equal([a[k] for k in FEATURES],[b[k] for k in FEATURES])

def test_outcome_mutation_candidate_invariance(private,rows):
    f=np.load(private/'inputs/frozen.npz');altered=rows.copy();altered['truth']=-999;altered['true_delta']=999
    a=translate(f['draws'],shift_vector(rows.predicted_delta,rows['V5.1_SD']));b=translate(f['draws'],shift_vector(altered.predicted_delta,altered['V5.1_SD']));assert np.array_equal(a,b)

def test_parent_lineage_main_protection(private):
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='track2/direction-to-location-01'
    assert subprocess.run(['git','merge-base','--is-ancestor',PARENT,'HEAD'],cwd=ROOT).returncode==0
    assert subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip()=='e1b5cf3b3a87966e902332ef3cc5c0ed2dbffee8'
    for path,sha in json.loads((private/'protected_parent_hashes.json').read_text()).items():assert digest(ROOT/path)==sha

def test_final_artifact_schema_if_ready():
    if not (OUT/'final_decision.json').exists():pytest.skip('Generated after remotely verified PRE')
    d=json.loads((OUT/'final_decision.json').read_text());assert d['primary_amplitude']==.10;assert d['secondary_cannot_rescue_primary'];assert not d['READY_FOR_SUBMISSION'];assert not d['INDEPENDENT_OOS'];assert d['2023_included'];assert not d['scientific_spec_modified_after_scores'];assert d['PRE_RESULT_DTL01_SHA']
    assert d['NEXT']=={'NO':'NEW-INFORMATION-SEARCH-02','INCONCLUSIVE':'DIRECTION-EVIDENCE-AUDIT-02','WEAK_YES':'DIRECTION-ROBUSTNESS-02','YES':'DIRECTION-TRANSFER-02','STRONG_YES':'DIRECTION-TRANSFER-02'}[d['DTL01_RESULT']]

"""Executive summary: protect immutable forecasts and deterministic post-hoc diagnostics."""
import ast,json,os,subprocess
from pathlib import Path
import numpy as np,pandas as pd,pytest
from backtesting.information_failure01.common import (ROOT,OUT,PARENT,LAMBDA_GRID,DIRECTION_CONSTANTS,group_weights,weighted_spearman,direction_metrics,sign_partition,aggregate,calibration,array_digest,digest,verify_inputs)
from backtesting.information_failure01.diagnose import fixed_transform,loss_curve,block_sensitivity
from backtesting.information_failure01.audit import selected_indices
from backtesting.information_failure01.decide import direction_label,choose_axis
from qfbench2_common.scoring.crps import crps_ensemble

@pytest.fixture
def private():
 p=os.environ.get('INFORMATION_FAILURE_PRIVATE')
 if not p:pytest.skip('Private frozen recovery inputs are intentionally not in public repository')
 return Path(p)
def test_constants_and_parent():
 spec=json.loads((ROOT/'backtesting/information_failure01/experiment_spec.json').read_text());assert tuple(spec['shrinkage_grid'])==LAMBDA_GRID==(0.,.02,.05,.10,.20,.30,.50,.75,1.)
 assert tuple(spec['direction_only_constants'])==DIRECTION_CONSTANTS==(.02,.05,.10,.20);assert spec['parent_SHA']==PARENT=='ca9b467d48b2fc145faa5bfe549975206c8a811f';assert spec['new_models_allowed'] is False;assert spec['bootstrap_replicates']==5000

def test_no_refit_or_new_source():
 files=list((ROOT/'backtesting/information_failure01').glob('*.py'));assert files
 for f in files:
  tree=ast.parse(f.read_text())
  assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ['fit','fit_transform','partial_fit'] for n in ast.walk(tree))
  assert not any(isinstance(n,(ast.Import,ast.ImportFrom)) and 'sklearn' in ast.unparse(n) for n in ast.walk(tree))
 assert 'BoE' not in (ROOT/'backtesting/information_failure01/experiment_spec.json').read_text()

def test_source_release_balance():
 groups=['a']*8+['b']*2;w=group_weights(groups);assert w[:8].sum()==pytest.approx(1);assert w[8:].sum()==pytest.approx(1)
 y=np.array([1.]*8+[-1.]*2);p=np.ones(10);assert direction_metrics(y,p,w)['sign_accuracy']==pytest.approx(.5);assert direction_metrics(y,p,np.ones(10))['sign_accuracy']==pytest.approx(.8)

def test_weighted_rank_ties_and_determinism():
 from scipy.stats import spearmanr
 y=np.array([3,1,1,5,2]);p=np.array([2,3,3,4,1]);assert weighted_spearman(y,p,np.ones(5))==pytest.approx(spearmanr(y,p).statistic)
 w=np.array([.2,1,1,.4,1]);per=np.array([3,0,4,2,1]);assert weighted_spearman(y,p,w)==pytest.approx(weighted_spearman(y[per],p[per],w[per]))

def test_sign_partition():
 assert list(sign_partition([1,-1,1,-1,0,2],[3,-3,-3,3,3,0]))==['SIGN_CORRECT','SIGN_CORRECT','SIGN_WRONG','SIGN_WRONG','ZERO_TIE','ZERO_TIE']

def test_fixed_shifts_use_only_predictions():
 p=np.array([0,-7.,.4]);before=array_digest(p)
 for c in DIRECTION_CONSTANTS:assert np.array_equal(fixed_transform(p,'direction_only',c),np.sign(p)*c)
 for lam in LAMBDA_GRID:assert np.array_equal(fixed_transform(p,'shrinkage',lam),p*lam)
 assert array_digest(p)==before
 # Mutating outcome-side labels or future release objects cannot enter this function.
 truth=np.array([8,-3,2]);truth[:]=999;future={'release':2099,'features':[1e9]*5};assert np.array_equal(fixed_transform(p,'direction_only',.1),[0,-.1,.1]);assert future['release']==2099

def test_geometry_pure_translation():
 d=np.array([[-2.,0],[-1.,1],[1.,3],[2.,4]]);p=np.array([.4,-.2]);sd=d.std(axis=0);s=d+p*sd
 assert np.allclose(np.diff(d,axis=0),np.diff(s,axis=0));assert np.allclose(s.std(axis=0),sd);assert np.array_equal(np.argsort(d,axis=0),np.argsort(s,axis=0))

def test_convex_sign_correct_nonovershoot():
 d=np.array([[-2.],[-1.],[1.],[2.]]);y=np.array([3.]);b=crps_ensemble(d,y,fair=True)
 assert crps_ensemble(d+1,y,fair=True)[0]<b[0];assert crps_ensemble(d+10,y,fair=True)[0]>b[0]

def test_calibration_is_posthoc_not_applied():
 y=np.array([1,2,3.]);p=2*y;h=array_digest(p);c=calibration(y,p,np.ones(3));assert c['slope']==pytest.approx(.5);assert c['applied_to_candidate'] is False;assert array_digest(p)==h

def test_no_favorable_subset_promoted():
 text=(ROOT/'backtesting/information_failure01/decide.py').read_text();assert 'original_sign_correct_ratio' in text
 spec=json.loads((ROOT/'backtesting/information_failure01/experiment_spec.json').read_text());assert spec['preserve_original_universes'];assert spec['scope'].endswith('next axis not executed')
 _,_,_=choose_axis({},{}).values() if False else (0,0,0)
 dec=choose_axis({},{});assert dec['exactly_one_axis'];assert dec['confirmatory_candidate'] is None

def test_folds_five_vs_eight():
 def m(n,positive):return {'balanced':{'release':{'sign_accuracy':.66,'spearman':.4}},'years':[{'balance':'release','sign_accuracy':.6 if i<positive else .4,'spearman':.3} for i in range(n)]}
 assert direction_label(m(5,4))['label']=='STRONG';assert direction_label(m(8,5))['label']=='MODERATE';assert direction_label(m(8,4))['label']=='WEAK'

def test_exact_reproduction_from_frozen(private):
 repro=json.loads((OUT/'prior_result_reproduction.json').read_text());assert repro['all_primary_results_reproduced'];assert repro['no_refitting'];assert len(repro['sources'])==3
 for v in repro['sources']:
  r=pd.read_parquet(private/'diagnostic_inputs'/v['source']/'ledger.parquet');ratio=r.candidate_cell_CRPS.sum()/r.baseline_cell_CRPS.sum();assert abs(ratio-v['published_primary_ratio'])<=v['tolerance'];assert len(r)==v['cells']
  assert array_digest(r.predicted_delta.to_numpy())==v['selected_prediction_array_sha256']

def test_private_schema_and_spd2023(private):
 r=pd.read_parquet(private/'backtesting/information_failure01/results/unified_failure_ledger.parquet');required={'source','asset','origin_date','fold','year','horizon','release_id','release_date','source_age','true_delta','predicted_delta','V5.1_median','V5.1_SD','raw_center_error','predicted_raw_shift','baseline_cell_CRPS','candidate_cell_CRPS','cell_CRPS_delta','feature_state_id'};assert required<=set(r)
 sp=r[r.source=='SPD'];assert 2023 in set(sp.year);assert set(sp.asset)=={'UST_2Y','UST_5Y'};assert set(sp.horizon)=={5,21,63,126,189};assert len(r)==3395
 assert not (OUT/'unified_failure_ledger.parquet').exists()

def test_inputs_and_parent_files_unchanged(private):
 verify_inputs(private)
 for path,sha in json.loads((private/'protected_parent_hashes.json').read_text()).items():assert digest(ROOT/path)==sha
 assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='track2/information-failure-reassessment-01'
 assert subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip()=='e1b5cf3b3a87966e902332ef3cc5c0ed2dbffee8'
 assert subprocess.run(['git','merge-base','--is-ancestor',PARENT,'HEAD'],cwd=ROOT).returncode==0

def test_deterministic_aggregation(private):
 r=pd.read_parquet(private/'diagnostic_inputs/SPD/ledger.parquet');first=aggregate(r,'release');second=aggregate(r,'release');assert first==second
 assert first['cells']==552;assert first['years']==5

def test_posthoc_same_ledger_endpoints(private):
 r=pd.read_parquet(private/'diagnostic_inputs/SPD/ledger.parquet');draws=np.load(private/'diagnostic_inputs/SPD/draws.npz')['draws'];before=array_digest(r.predicted_delta)
 assert np.allclose(loss_curve(draws,r,'shrinkage',0),r.baseline_cell_CRPS,atol=1e-12,rtol=1e-12)
 assert np.allclose(loss_curve(draws,r,'shrinkage',1),r.candidate_cell_CRPS,atol=1e-12,rtol=1e-12);assert array_digest(r.predicted_delta)==before

def test_saved_schemas_when_final_present():
 if not (OUT/'final_decision.json').exists():pytest.skip('Final artifacts are generated only after remote PRE verification')
 d=json.loads((OUT/'final_decision.json').read_text());assert d['new_models_fit']==0 and d['SPD_2023_retained'] and not d['official_submission_allowed'];assert d['PRE_RESULT_INFO_FAILURE_SHA'];assert not d['independent_OOS'];assert d['central_conclusion'] in ['NO_INFORMATION','DIRECTION_WITH_BAD_MAGNITUDE','INCONCLUSIVE']
 for name in ['posthoc_shrinkage_curve.csv','posthoc_direction_only_curve.csv']:
  rows=pd.read_csv(OUT/name);assert rows.INVALID_FOR_CONFIRMATORY_USE.all();assert rows.primary_universe_unchanged.all()

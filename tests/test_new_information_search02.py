"""Executive summary: outcome-free ranking, no lookahead and protected frozen predictions."""
import ast,hashlib,json,os,subprocess
from pathlib import Path
import numpy as np,pandas as pd,pytest
from backtesting.new_information_search02.core import *
from backtesting.new_information_search02.catalog import inventory,SPEC
from backtesting.new_information_search02.parse import sep_fields,h41_reserves,rrp_fields
ROOT=Path(__file__).resolve().parents[1]
def state():
 return pd.DataFrame([dict(origin_date='2024-03-11',asset='UST_2Y',horizon=5,release_id='a',frozen_prediction=-.3,direction=-1),dict(origin_date='2024-03-12',asset='UST_5Y',horizon=21,release_id='b',frozen_prediction=.5,direction=1)])
def test_parent_main_branch():
 assert subprocess.run(['git','merge-base','--is-ancestor',PARENT,'HEAD'],cwd=ROOT).returncode==0
 assert subprocess.check_output(['git','rev-parse','refs/remotes/origin/main'],cwd=ROOT,text=True).strip()==MAIN
 assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='track2/new-information-search-02'
def test_frozen_hash():
 p=Path(os.environ['NEWINFO02_PRIVATE']);d=pd.read_parquet(p/'frozen_spd_direction_state.parquet');m=json.loads((ROOT/'backtesting/new_information_search02/results/frozen_spd_direction_manifest.json').read_text())
 assert hashlib.sha256((p/'frozen_spd_direction_state.parquet').read_bytes()).hexdigest()==m['SHA256']
 assert hashlib.sha256(d.frozen_prediction.to_numpy(dtype=np.float64).tobytes()).hexdigest()==m['frozen_prediction_array_SHA256']
 assert len(project_state(d))==552 and set(d.columns)==set(STATE_COLUMNS)
def test_state_firewall():
 a=state();pd.testing.assert_frame_equal(project_state(a),project_state(a.assign(CRPS=9,future_return=2,realized_truth=8)))
def test_dst_cutoff():
 assert origin_cutoff('2024-03-11').isoformat()=='2024-03-08T21:00:00+00:00'
 assert origin_cutoff('2024-03-12').isoformat()=='2024-03-11T20:00:00+00:00'
def test_no_future_source_mutation():
 s=pd.DataFrame([dict(available_at=available_eod('2024-03-07'),value=-1,source_state_id='old'),dict(available_at=available_eod('2024-03-11'),value=8,source_state_id='new')]);a=join_asof(state(),s)
 assert list(a.source_state_id)==['old','old'];s.loc[1,'value']=999;pd.testing.assert_frame_equal(a,join_asof(state(),s))
def test_expiry():
 s=pd.DataFrame([dict(available_at=available_eod('2024-01-01'),value=1,source_state_id='old')]);assert join_asof(state(),s,5).value.isna().all()
def test_release_balancing():
 a=state().assign(value=[-1,-1],source_state_id=['x','y']);b=pd.concat([a.iloc[[0]]]*100+[a.iloc[[1]]],ignore_index=True)
 assert alignment(a)[2]['agreement']==pytest.approx(.5);assert alignment(b)[2]['agreement']==pytest.approx(.5)
 assert alignment(a)[0]['agreement']!=alignment(b)[0]['agreement']
def test_weighted_rank():
 assert weighted_corr([1,2,3],[3,1,2],[1,1,1],True)==pytest.approx(weighted_corr([1,1,2,3],[3,3,1,2],[.5,.5,1,1],True))
def test_persistence_gap():
 d=pd.Series([1.,2.,3.],index=pd.to_datetime(['2024-01-01','2024-01-03','2024-01-05']));m=persistence(d);assert m['lag_1_pairs']==0 and m['observed_days']==3 and m['grid_days']==5
def test_persistence_linear():
 d=pd.Series(np.arange(50.),index=pd.bdate_range('2024-01-01',periods=50));assert persistence(d)['lag_5_autocorrelation']==pytest.approx(1)
@pytest.mark.parametrize('value,expected',[(.2,'HIGH'),(.4,'MEDIUM'),(.8,'LOW'),(.95,'REDUNDANT'),(None,'UNKNOWN')])
def test_novelty_bounds(value,expected):assert novelty(value)==expected
def test_projection_source_only():
 d=pd.DataFrame({'level':np.arange(30.),'change':np.sin(np.arange(30.))});m=redundancy(2*d.level+1,d);assert m['R2']==pytest.approx(1) and m['novelty']=='REDUNDANT'
def test_deterministic_scoring_gates():
 a=score_and_rank(inventory());assert bytes_canonical(a)==bytes_canonical(score_and_rank(inventory()[::-1]));assert all(r['score']<=20 and r['alignment']<=2 for r in a)
 assert not next(r for r in a if r['source']=='CME_ZQ_POLICY_PATH')['hard_gates_pass']
 assert not next(r for r in a if r['source']=='ATLANTA_MPT_SOFR')['hard_gates_pass']
def test_exactly_one_if_eligible():
 rows=inventory();r=next(x for x in rows if x['source']=='FOMC_SEP_POLICY_PATH');r['Novelty']='HIGH';r['novelty']=2
 d=choose(score_and_rank(rows),[dict(source=r['source'],weighting='release',origins=59,agreement=.65,Spearman=.4)],{});assert d['primary_count']==1 and d['NEWINFO02_PRIMARY_SOURCE']==r['source'];assert len(score_and_rank(rows)[:3])==3
def test_no_forced_winner():
 d=choose(score_and_rank(inventory()),[],{});assert d['primary_count']==0 and d['audit_focus_source']=='CME_ZQ_POLICY_PATH'
def test_outcome_mutation():assert outcome_firewall(inventory(),[],{})['ranking_and_selection_bitwise_identical']
def test_target_year_parser():
 html='<table><thead><tr><th id="m" colspan="3">Median</th></tr><tr><th headers="m">2023</th><th headers="m">2024</th><th headers="m">Longer run</th></tr></thead><tbody><tr><th>Federal funds rate</th><td>5.4</td><td>4.6</td><td>2.5</td></tr></tbody></table>'
 d=sep_fields(html,'2023-12-13');assert d['value']==pytest.approx(-.8) and d['medians_by_target_year']=={2023:5.4,2024:4.6}
def test_wednesday_not_average():assert h41_reserves('<pre>Reserve balances with Federal Reserve Banks 1,234 + 22 - 44 5,678</pre>')==5678

def test_later_update_not_original():
 r=rrp_fields([dict(operationType='Reverse Repo',term='Overnight',operationDate='2015-01-02',lastUpdated='2015-12-05 16:04:47',totalAmtAccepted=123,operationId='x')]);assert pd.Timestamp(r[0]['available_at'])>available_eod('2015-12-04')
def test_no_model_or_crps_calls():
 for file in (ROOT/'backtesting/new_information_search02').glob('*.py'):
  for node in ast.walk(ast.parse(file.read_text())):
   if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):assert node.func.attr not in ['fit','fit_predict','fit_transform','crps_ensemble','score_forecast']
 assert SPEC['model_executions']==SPEC['new_CRPS_executions']==0 and 'no optimized lags' in SPEC['alignment']

def test_mpt_string_means_and_future_cutoff(tmp_path):
 """Regression: provider rate means are strings; unrelated nonnumeric fields must not prevent parsing."""
 import zipfile
 from backtesting.new_information_search02.parse import mpt_state
 with zipfile.ZipFile(tmp_path/'mpt.xlsx','w') as z:z.writestr('xl/drawings/drawing1.xml','<root><t>Personal and educational purposes only.</t></root>')
 pd.DataFrame([
  {'date':'2023-03-29','reference_start':'2023-06-21','target_range':'475bps -500bps','field':'Rate: mean','value':' 481.98'},
  {'date':'2023-03-29','reference_start':'2023-09-20','target_range':'475bps -500bps','field':'Rate: mean','value':' 460.00'},
  {'date':'2023-03-29','reference_start':'2023-09-20','target_range':'475bps -500bps','field':'unrelated metadata','value':'not numeric'},
  {'date':'2025-01-02','reference_start':'2025-06-18','target_range':'test','field':'Rate: mean','value':'9999'}
 ]).to_csv(tmp_path/'mpt_bounded.csv',index=False)
 rows,_=mpt_state(tmp_path/'mpt.xlsx');assert len(rows)==1 and rows.iloc[0].value==pytest.approx(-21.98);assert rows.iloc[0].date=='2023-03-29'

def test_year_keyed_metadata_parquet_without_value_change(tmp_path):
 from backtesting.new_information_search02.parse import write_source_parquet
 frame=pd.DataFrame([{'medians_by_target_year':{2023:5.4,2024:4.6},'value':-.8,'date':'2023-12-13'}])
 write_source_parquet(frame,tmp_path/'source.parquet');restored=pd.read_parquet(tmp_path/'source.parquet')
 assert restored.value.iloc[0]==frame.value.iloc[0]
 assert json.loads(restored.medians_by_target_year.iloc[0])=={'2023':5.4,'2024':4.6}
 assert frame.medians_by_target_year.iloc[0]=={2023:5.4,2024:4.6}
 assert not (tmp_path/'source.tmp.parquet').exists()

def test_constructed_source_schema_and_cutoff():
 p=Path(os.environ['NEWINFO02_PRIVATE']);manifest=json.loads((p/'input_manifest.json').read_text())
 for source,spec in manifest['source_states'].items():
  f=p/(source+'.parquet');assert hashlib.sha256(f.read_bytes()).hexdigest()==spec['SHA256']
  d=pd.read_parquet(f);assert len(d)==spec['rows'] and d.source_state_id.nunique()==len(d)
  assert pd.to_datetime(d.date).max()<=pd.Timestamp('2024-12-18')
  assert pd.api.types.is_numeric_dtype(d.value)
  assert not any(s in d.columns for s in ['future_return','realized_truth','CRPS','true_delta'])

def test_spec_unchanged_from_verified_checkpoint():
 for name in ['catalog.py','core.py','results/experiment_spec.json']:
  f='backtesting/new_information_search02/'+name
  old=subprocess.check_output(['git','show','5ff1ba0664c159bd06705c7cbfbeadb9bf8769fe:'+f],cwd=ROOT)
  assert (ROOT/f).read_bytes()==old

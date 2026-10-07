"""Executive summary: freeze, chronology, original bytes and diagnostic isolation tests."""
import ast,json,os,subprocess
from pathlib import Path
import numpy as np,pandas as pd,pytest
from qfbench2_common.scoring.crps import crps_ensemble
from qfbench2_track_forecasting.location01.oracle_target import target
from backtesting.v51_center_bias04 import core as c,run as r,aggregate as a,oracle as o
P=Path(os.environ.get('BIAS04_PRIVATE','/unavailable'))
def synthetic():
 rows=pd.DataFrame(dict(origin=['2007-01-02','2009-06-01','2009-12-31','2010-01-04','2011-01-03'],target_end=['2007-10-01','2009-10-01','2010-01-05','2010-10-01','2011-10-01'],asset=['A','B','A','A','B'],horizon=[5,21,5,5,21],raw_center_error=[1,-3,99,-9,10],standardized_center_error=[2,-6,99,-9,10]))
 rows["year"]=pd.to_datetime(rows["origin"]).dt.year
 return rows
def test_constants():assert c.PARENT=='0f5c938eeb4054518b0bde81e4de1503890fd684'and c.SEED==31804 and c.AMPLITUDE==.05 and c.WINDOWS==(1,3,5)and len(c.FOLDS)==4
@pytest.mark.parametrize('year,era',[(2016,'<=2016'),(2017,'2017-2019'),(2020,'2020-2021'),(2024,'2022-2024')])
def test_eras(year,era):assert c.era(year)==era
def test_parent_reproduction():
 b=json.loads((c.OUT/'parent_bias_reproduction.json').read_text());assert b['exact']and b['cells']==482 and b['origins']==52;assert b['ratios']['CONSTANT_UP']==.9898286259575693 and b['positive_fraction']==.6410788381742739
@pytest.mark.parametrize('groups',[['a','a','b'],[2020,2020,2021]])
def test_balancing(groups):assert np.array_equal(c.weights(groups),[.5,.5,1])
@pytest.mark.parametrize('values',[[1,2],[1,2,3,4],[1,2,3]])
def test_weighted_median_agrees_equal(values):assert c.weighted_median(values,np.ones(len(values)))==np.median(values)
def test_purge_train_targets():
 rows=synthetic();fold,tr,te,b=next(c.partitions(rows));assert tr.tolist()==[0];assert (rows.iloc[tr].target_end<b).all();assert set(tr).isdisjoint(te)
def test_no_test_label_in_bias():
 rows=synthetic();tr=next(c.partitions(rows))[1];p=c.train_bias(rows,tr);rows.loc[3:,'raw_center_error']=-1e10;rows.loc[3:,'standardized_center_error']=-1e10;assert p==c.train_bias(rows,tr)
def test_fixed_shift_and_cap():
 rows=synthetic();p=c.train_bias(rows,[0]);s=c.predicted_shifts(rows,[3,4],p);assert set(s)==set(c.PREDICTIVE);assert np.array_equal(s['GLOBAL_BIAS_SIGN005'],[.05,.05]);assert np.array_equal(s['GLOBAL_MEDIAN_SHIFT'],[1.,1.]);assert p['median_requested']==2
@pytest.mark.parametrize('delta',[-.05,0.,.05,1.])
def test_geometry(delta):
 d=np.random.default_rng(8).normal(size=(500,8));shift=delta*d.std(axis=0);n=d+shift;assert np.allclose(n.std(axis=0),d.std(axis=0),atol=1e-14);assert np.array_equal(np.argsort(n,axis=0),np.argsort(d,axis=0))
def test_level_and_accumulated_original_semantics():
 dates=pd.bdate_range('2019-01-01',periods=20);levels=pd.Series(np.arange(20.)+10,index=dates);returns=pd.Series(np.ones(20)*.01,index=dates);assert target(levels,'level',dates[0],5)[0]==15;assert np.isclose(target(returns,'log_return',dates[0],5)[0],.05)
def test_oracle_isolation():
 src=Path(c.__file__).read_text();assert 'minimum_location'not in src;tree=ast.parse(src);assert not any(isinstance(n,ast.Name)and n.id in ['GridSearchCV','Ridge','LogisticRegression']for n in ast.walk(tree));f=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='train_bias');assert 'oracle'not in ast.unparse(f).lower()
def test_oracle_minimum_matches_shared_scorer():
 rng=np.random.default_rng(1);d=rng.normal(size=(500,4));truth=np.array([1.,-1.,.1,2.]);sd=d.std(axis=0);scale=np.array([1.,2.,3.,4.]);z=(truth-d)/sd;shift,audit=o.minimum_location(z,sd,scale,np.full(4,500));loss=lambda x:np.sum(crps_ensemble(d+x*sd,truth)/scale);assert loss(shift)<=min(loss(shift-1e-5),loss(shift+1e-5))+1e-12;assert not audit['predictive_use']
@pytest.mark.parametrize('kind',range(4))
def test_control_determinism_and_firewall(kind):
 rows=pd.DataFrame(dict(origin=['2010-01-04']*4,asset=['A','B','A','B'],horizon=[5,21,5,21],year=[2010]*4,fold=[1]*4));params={1:dict(year_sign={2001:-1,2002:1},asset_sign={'A':1,'B':-1},horizon_sign={5:1,21:-1})};s=np.array([1,-1,1,-1]);x=c.random_directions(rows,params,s,kind,1);assert np.array_equal(x,c.random_directions(rows,params,s,kind,1));
 if kind==0:assert sorted(x)==sorted(s)
 with pytest.raises(AssertionError):c.random_directions(rows.assign(truth=3),params,s,kind,1)
def test_decision_global_needs_every_gate():
 e=dict(global_gates={'x':True},global_weak=False,asset_gates={'x':False},horizon_gates={'x':False},episode_gates={'x':False},no_stable_gates={'x':False});assert a.decide(e)[0]=='PERSISTENT_GLOBAL_BIAS';e['global_gates']['x']=False;assert a.decide(e)[0]=='INCONCLUSIVE'
def test_source_manifest_canonical():
 m=json.loads((c.OUT/'canonical_ledger_manifest.json').read_text());old=json.loads((c.ROOT/'backtesting/location01/results/ledger_manifest.json').read_text());assert m['ledger_SHA256']==old['ledger_sha256'];assert m['cells']==old['cells'];assert m['origins']==old['origins'];assert set(m['assets'])==set(old['assets'])
@pytest.mark.skipif(not (P/'protected_parent_hashes.json').exists(),reason='private verified recovery unavailable')
def test_parent_main_draw_protection():
 c.protected();m=json.loads((c.ROOT/'backtesting/location01/results/ledger_manifest.json').read_text());assert all(c.digest(P/'canonical/origins'/k)==v for k,v in m['baseline_cache_sha256'].items())
@pytest.mark.skipif(not (P/'pre_receipt.json').exists(),reason='PRE remote verification pending')
def test_pre_verified():c.verify()
@pytest.mark.skipif(not (P/'center_error_ledger.parquet').exists(),reason='new outcomes gated by PRE')
def test_full_draw_ledger_maturity():
 rows=r.load();m=json.loads((c.OUT/'canonical_ledger_manifest.json').read_text());assert len(rows)==m['cells']and rows.origin.nunique()==m['origins'];assert rows.target_end.max()<='2024-12-18';assert np.array_equal(rows.direction,np.sign(rows.truth-rows['median']))
@pytest.mark.skipif(not (c.OUT/'final_decision.json').exists(),reason='final frozen diagnostics pending')
def test_complete_artifacts_balanced_blocks():
 b=json.loads((c.OUT/'bootstrap_summary.json').read_text());assert set(b['blocks'])=={'origin','year','asset'}and all(x['replicates']==5000 for x in b['blocks'].values());s=json.loads((c.OUT/'negative_controls.json').read_text());assert all(x['replicates']==2000 for x in s['controls'].values());assert 'truth'not in pd.read_csv(c.OUT/'asset_horizon_bias_matrix.csv',nrows=0).columns

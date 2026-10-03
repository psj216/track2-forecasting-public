"""Executive summary: SPD-only, original-publication timing, weighted location-only frozen test."""
import copy,json,subprocess
from pathlib import Path
import numpy as np,pandas as pd,pytest
from backtesting.location04 import source_dataset as s,model as m,evaluate as e,controls as c
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'backtesting/location04/results'
@pytest.fixture
def states():return json.loads((OUT/'source_states.json').read_text())['states']
def test_universe_and_gate():
 u=pd.read_csv(OUT/'spd_release_universe.csv');assert len(u)==112 and u.survey_id.nunique()==112
 g=json.loads((OUT/'spd_dataset_readiness.json').read_text());assert g['DATASET_READY'];assert g['usable_FULL5_releases']>=30;assert len(g['usable_calendar_years'])>=8;assert len(g['policy_eras'])>=3;assert not g['new_outcomes_accessed'];assert not g['unresolved_extractions']
@pytest.mark.parametrize('rid,date',[('2011-December','2012-01-04'),('2018-January','2018-02-22'),('2024-September','2024-10-10')])
def test_publication_traps(states,rid,date):
 x=next(x for x in states if x['release_id']==rid);assert x['publication_date']==date
 y=s.asof_features(states,date);assert y is None or y['release_id']!=rid
@pytest.mark.parametrize('rid',['2018-January','2024-September'])
def test_distribution_not_activation(rid):
 u=pd.read_csv(OUT/'spd_release_universe.csv').set_index('survey_id').loc[rid];assert u.SURVEY_DISTRIBUTED_AT<u.RESULT_PUBLIC_AVAILABLE_AT[:10]
def test_september_near_far_exact(states):
 x=next(x for x in states if x['release_id']=='2024-September');assert x['near_target_date']=='2024-11-07';assert x['POLICY_NEAR']==4.88;assert x['far_target_date']=='2025-03-19';assert x['POLICY_FAR']==4.13;assert x['POLICY_PATH_SLOPE']==pytest.approx(-.75)
def test_source_targets_future_distinct_180(states):
 for x in states:
  if x['full5_usable_at_release']:
   assert x['near_target_date']>x['publication_date'];assert x['far_target_date']>x['near_target_date'];assert (pd.Timestamp(x['far_target_date'])-pd.Timestamp(x['publication_date'])).days<=180
@pytest.mark.parametrize('label,year,expected',[('Dec. 17-18',2024,'2024-12-18'),('Jan. 28-29',2025,'2025-01-29'),('2025 Q1',2024,'2025-03-31'),('Jul. 31 - Aug. 1 2018',2018,'2018-08-01')])
def test_explicit_target_dates(label,year,expected):assert s.target_date(label,year)[0]==expected
def test_same_target_revision_and_missing(states):
 f=pd.read_csv(OUT/'spd_policy_field_ledger.csv');prev={}
 for x in states:
  fields=f.loc[f.survey_id==x['release_id']];values=dict(zip(fields.target_event_date,fields.published_value));near=x['near_target_date'];r=x['POLICY_REVISION_SAME_TARGET']
  if r is not None:assert near in prev;assert r==pytest.approx(x['POLICY_NEAR']-prev[near])
  prev=values
 assert next(x for x in states if x['release_id']=='2016-March')['POLICY_REVISION_SAME_TARGET'] is None
def test_no_target_rollover_subtraction():
 row={'survey_id':'x','RESULT_PUBLIC_AVAILABLE_AT':'2024-01-04'};f=[{'target_event_date':d,'published_value':v,'representation':s.STATISTIC} for d,v in [('2024-03-01',2),('2024-05-01',3)]]
 x=s.state_from_release(row,f,[{'target_event_date':'2023-03-01','published_value':8,'representation':s.STATISTIC}]);assert x['POLICY_REVISION_SAME_TARGET'] is None;assert not x['full5_usable_at_release']
def test_spd_only_no_smp_fallback(states):
 assert len(s.eligible_panel([{'panel':'SPD'},{'panel':'SMP'}]))==1
 x=next(x for x in states if x['full5_usable_at_release']);fake=copy.deepcopy(x);fake.update(panel='SMP',POLICY_NEAR=999)
 assert s.asof_features([fake],str(pd.Timestamp(x['publication_date'])+pd.offsets.BDay(3))) is None
 assert s.asof_features([x,fake],str(pd.Timestamp(x['publication_date'])+pd.offsets.BDay(3)))['POLICY_NEAR']==x['POLICY_NEAR']
def test_latest_incomplete_never_fallback(states):
 x=copy.deepcopy(next(x for x in states if x['full5_usable_at_release']));z=copy.deepcopy(x);z.update(available_at=s.activation('2024-01-03').isoformat(),publication_date='2024-01-03',full5_usable_at_release=False);x.update(available_at=s.activation('2023-12-20').isoformat(),publication_date='2023-12-20');assert s.asof_features([x,z],'2024-01-05') is None
def test_expiry_70_fixed(states):
 x=next(x for x in states if x['full5_usable_at_release']);d=np.busday_offset(np.datetime64(x['publication_date']),70);assert s.asof_features([x],str(pd.Timestamp(d)+pd.offsets.BDay(1))) is not None;assert s.asof_features([x],str(pd.Timestamp(d)+pd.offsets.BDay(2))) is None
def test_errata_original_rule():assert not s.original_fields_admissible(True,False);assert s.original_fields_admissible(True,True);assert s.original_fields_admissible(False,False)
@pytest.mark.parametrize('origin',['2016-06-01','2020-06-01','2024-11-01'])
def test_future_mutation(states,origin):
 z=copy.deepcopy(states)
 for x in z:
  if pd.Timestamp(x['available_at'])>s.cutoff(origin):
   for f in s.FEATURES[:4]:x[f]=1e9
 assert s.asof_features(states,origin)==s.asof_features(z,origin)
def test_outcome_mutation_features_unchanged(states):
 x=s.asof_features(states,'2024-11-01');outcome={'truth':1e9,'delta':-1e9};assert s.asof_features(states,'2024-11-01')==x;assert not set(outcome)&set(s.FEATURES)
def test_five_fixed_features_models():
 assert len(s.FEATURES)==5;assert m.MIN_RELEASES==20;assert m.PRIMARY_ASSETS==('UST_2Y','UST_5Y');assert m.YEARS==(2020,2021,2022,2023,2024);assert list(m.MODELS.values())==[(0,1,2,3,4),(0,1,2,4),(3,4),(0,3,4),(2,3,4),(0,1,2,3,4)]
def test_train_only_weighted_scaler():
 rng=np.random.default_rng(1);x=rng.normal(size=(40,5));r=np.resize(['a','b','c'],40);f=m.fit_ridge(x,rng.normal(size=40),r,tuple(range(5)));assert f[1].alpha==1.;assert np.allclose(f[0].mean_,np.average(x,axis=0,weights=m.release_weights(r)));before=f[0].mean_.copy();m.predict(f,np.ones((3,5))*1e8,tuple(range(5)));assert np.array_equal(before,f[0].mean_)
def test_release_weights_total_one():
 r=np.array(['a']*10+['b']*2);w=m.release_weights(r);assert w[r=='a'].sum()==pytest.approx(1);assert w[r=='b'].sum()==pytest.approx(1)
def test_batch_sklearn_identical():
 rng=np.random.default_rng(3);x=rng.normal(size=(20,50,5));xt=rng.normal(size=(20,8,5));y=rng.normal(size=50);r=np.resize(np.arange(15),50);p=m.batch_ridge(x,y,m.release_weights(r),xt);q=np.array([m.predict(m.fit_ridge(a,y,r,tuple(range(5))),b,tuple(range(5))) for a,b in zip(x,xt)]);assert np.allclose(p,q,atol=1e-13,rtol=1e-13)
def test_location_geometry_scale_ranks():
 rng=np.random.default_rng(4);d=rng.normal(size=(500,12));sd=d.std(0);v=m.shift(d,rng.normal(size=12),sd);assert np.allclose(v.std(0),sd,atol=2e-15);assert np.allclose(v-v.mean(0),d-d.mean(0),atol=4e-15);assert np.array_equal(np.argsort(v,axis=0),np.argsort(d,axis=0))
@pytest.mark.parametrize('h',[5,21,63,126,189])
def test_purge_and_release_isolation(h):
 rows=pd.DataFrame({'origin':['2016-06-01','2019-12-31','2020-01-02'],'target_end':['2017-06-01','2020-05-01','2021-01-02'],'horizon':[h]*3,'release_id':['old','shared','shared']});assert m.train_mask(rows,2020,s.cutoff('2020-01-02')).tolist()==[True,False,False]
def test_pre_gate_blocks_labels(tmp_path):
 (tmp_path/'pre_receipt.json').write_text(json.dumps({'remote_verified':False}))
 with pytest.raises((ValueError,FileNotFoundError)):e.verify_pre(tmp_path)
def test_parent_main_protection():
 p=json.loads((OUT/'parent_manifest.json').read_text());assert p['parent_result_sha']=='938abb88db0dc985d8468950e169098b88ed50b9';assert json.loads((OUT/'environment_audit.json').read_text())['main_untouched']
def test_seed_dates_deterministic(states):
 rows=pd.DataFrame({'origin':['2020-06-01','2024-11-01']});a,r=c.altered_calendar(rows,'RELEASE_DATE_PERMUTATION',9,states);b,rr=c.altered_calendar(rows,'RELEASE_DATE_PERMUTATION',9,states);assert np.array_equal(a,b,equal_nan=True);assert np.array_equal(r,rr)
 for origin,rid in zip(rows.origin,r):
  if rid:assert pd.Timestamp(next(x['available_at'] for x in states if x['release_id']==rid))<=s.cutoff(origin)
def test_cutoff_hardcoded():assert "rows.target_end<='2024-12-18'" in (ROOT/'backtesting/location04/evaluate.py').read_text()

def test_source_spec_schema():
 spec=json.loads((OUT/'experiment_spec.json').read_text());assert spec['features']==list(s.FEATURES);assert spec['assets']==list(m.PRIMARY_ASSETS);assert spec['age_limit_business_days']==70;assert spec['far_calendar_days']==180;assert spec['minimum_train_releases']==20;assert spec['Ridge_alpha']==1.;assert spec['controls']['replicates_per_stochastic_control']==2000

def test_source_rebuild_receipt():
 r=json.loads((OUT/'source_gate_verification.json').read_text());assert r['deterministic_rebuild_identical'];assert r['future_mutation_all_origins'];assert r['origins_tested']>=100

def test_lag_first_state_missing(states):
 rows=pd.DataFrame({'origin':[str(pd.Timestamp(states[0]['publication_date'])+pd.offsets.BDay(3))]});features,release=c.altered_calendar(rows,'ONE_RELEASE_LAG',m.SEED,states[:1]);assert release[0] is None;assert np.isnan(features).all()

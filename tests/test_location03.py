"""Executive summary: source-only/PIT, fixed model, release weights, CV and artifact gates."""
import json,copy,subprocess,hashlib
from pathlib import Path
import numpy as np,pandas as pd,pytest
from backtesting.location03 import source_dataset as s,model as m,evaluate as e,controls as c
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'backtesting/location03/results'

@pytest.fixture
def states():return json.loads((OUT/'source_states.json').read_text())['states']

def test_source_complete_universe():
 u=pd.read_csv(OUT/'sloos_release_universe.csv');assert len(u)==len(u.release_id.unique());assert u.survey_year.min()==1997;assert u.survey_year.max()==2024
 assert len(u.loc[u.survey_year==2020])==5
 r=json.loads((OUT/'sloos_dataset_readiness.json').read_text());assert r['DATASET_READY'];assert not r['outcomes_loaded'];assert not r['errors']

def test_post_panel_scope(states):
 assert min(x['publication_date'] for x in states)=='2013-02-04';assert all(int(x['release_id'][:4])>=2013 for x in states)
 assert json.loads((OUT/'sloos_structural_breaks.json').read_text())['exclude_all_pre_2013']

def test_october2024_publication_regression(states):
 f=next(x for x in states if x['release_id']=='2024-October');assert f['publication_date']=='2024-11-12'
 assert s.asof_features(states,'2024-11-12')['release_id']!='2024-October'
 assert s.asof_features(states,'2024-11-13')['release_id']!='2024-October'
 assert s.asof_features(states,'2024-11-14')['release_id']=='2024-October'

def test_publication_cutoff_no_early_activation(states):
 for state in states[1:]:
  eligible=s.asof_features(states,state['publication_date'])
  assert eligible is None or eligible['release_id']!=state['release_id']

def test_release_delta_first_missing(states):
 assert states[0]['DELTA_CREDIT_STANDARDS'] is None
 for previous,current in zip(states,states[1:]):
  assert current['DELTA_CREDIT_STANDARDS']==current['CREDIT_STANDARDS']-previous['CREDIT_STANDARDS']
  assert current['DELTA_CREDIT_DEMAND']==current['CREDIT_DEMAND']-previous['CREDIT_DEMAND']

def test_no_imputation(states):assert s.asof_features(states,'2013-03-01') is None

def test_nonoriginators_excluded_denominator():
 f=pd.read_csv(OUT/'sloos_field_extraction.csv');x=f.loc[(f.release_id=='2024-October')&(f.variable=='standards')]
 assert x.denominator.tolist()==[62,60];assert x.non_originating_explicit_count.tolist()==[1,3]
 for row in f.itertuples():assert sum(json.loads(row.counts))==row.denominator

@pytest.mark.parametrize('counts,value',[([2,6,52,3,0],100*5/63),([0,1,50,8,1],-100*8/60),([1,11,39,11,1],0)])
def test_direction_signs(counts,value):assert s.net(counts,sum(counts))==value

def test_denominator_failure():
 with pytest.raises(ValueError):s.net([0,1,2,3,4],100)

def test_errata_not_future_rewrite():
 assert not s.original_fields_admissible(True,False);assert s.original_fields_admissible(False,False);assert s.original_fields_admissible(True,True)
 err=json.loads((OUT/'sloos_errata_ledger.json').read_text());assert not any(x['C_I_original_table_counts_affected'] for x in err['events']);assert '202404.pdf' in err['April2024_bad_table_pdf_link']['verified_full_report_url']

def test_expiry_100_fixed(states):
 z=[dict(states[1])];pub=np.datetime64(z[0]['publication_date']);d=np.busday_offset(pub,100)
 assert s.asof_features(z,str(pd.Timestamp(d)+pd.offsets.BDay(1))) is not None
 assert s.asof_features(z,str(pd.Timestamp(d)+pd.offsets.BDay(2))) is None

def test_source_deterministic_rebuild(states):
 raw=[{k:x[k] for k in ['release_id','publication_date','CREDIT_STANDARDS','CREDIT_DEMAND']} for x in states]
 assert s.states_from_rows(raw)==s.states_from_rows(list(reversed(raw)))==states

@pytest.mark.parametrize('origin',['2014-06-02','2020-02-03','2024-11-14'])
def test_future_source_mutation(states,origin):
 changed=copy.deepcopy(states)
 for x in changed:
  if pd.Timestamp(x['available_at'])>s.cutoff(origin):
   for f in s.FEATURES[:4]:x[f]=1e9
 assert s.asof_features(states,origin)==s.asof_features(changed,origin)

def test_features_exact_five():
 assert len(s.FEATURES)==5;spec=json.loads((OUT/'experiment_spec.json').read_text());assert spec['features']==list(s.FEATURES);assert spec['Ridge_alpha']==1.;assert spec['age_limit_business_days']==100
 assert spec['minimum_train_releases']==12;assert spec['controls']['replicates_per_stochastic_control']==2000

def test_source_features_outcome_free(states):
 x=s.asof_features(states,'2020-06-02');z={'truth':1e8,'delta':-1e9};assert s.asof_features(states,'2020-06-02')==x
 assert not set(z)&set(s.FEATURES);assert not any('id' in f.lower() for f in s.FEATURES)

def test_release_weights_equal():
 r=['a']*10+['b']*5+['c']*2;w=m.release_weights(r)
 for k in set(r):assert abs(w[np.array(r)==k].sum()-1)<1e-15
 assert np.array_equal(w,m.release_weights(r))

def test_train_only_scaler_and_fixed_alpha():
 x=np.arange(100,dtype=float).reshape(20,5);y=np.arange(20);r=np.resize(['a','b','c'],20);fit=m.fit_ridge(x,y,r,tuple(range(5)))
 assert fit[1].alpha==1.;assert fit[1].fit_intercept;w=m.release_weights(r)
 assert np.allclose(fit[0].mean_,np.average(x,axis=0,weights=w));original=fit[0].mean_.copy();m.predict(fit,np.ones((3,5))*1e9,tuple(range(5)));assert np.array_equal(original,fit[0].mean_)

def test_batch_identical_ridge():
 rng=np.random.default_rng(11);x=rng.normal(size=(20,50,5));test=rng.normal(size=(20,6,5));y=rng.normal(size=50);r=np.resize(np.arange(13),50)
 p=m.batch_ridge(x,y,m.release_weights(r),test);q=np.array([m.predict(m.fit_ridge(a,y,r,tuple(range(5))),b,tuple(range(5))) for a,b in zip(x,test)])
 assert np.allclose(p,q,atol=1e-13,rtol=1e-13)

def test_location_shift_geometry_scale_order():
 rng=np.random.default_rng(10);draws=rng.normal(size=(500,30));sd=draws.std(axis=0);shift=m.shift(draws,rng.normal(size=30),sd)
 assert np.allclose(shift-shift.mean(0),draws-draws.mean(0),atol=2e-15,rtol=2e-14)
 assert np.allclose(shift.std(0),sd,atol=2e-15,rtol=2e-14)
 ordered=np.take_along_axis(shift,np.argsort(draws,axis=0),axis=0);assert np.all(np.diff(ordered,axis=0)>=0)

def test_horizon_purge_release_no_overlap():
 rows=pd.DataFrame({'origin':['2015-01-02','2016-12-01','2016-12-30','2017-01-03'],'target_end':['2015-02-02','2017-01-05','2017-02-02','2017-02-03'],'horizon':[21]*4,'release_id':['a','b','c','c']})
 mask=m.train_mask(rows,2017,s.cutoff('2017-01-03'));assert mask.tolist()==[True,False,False,False]

@pytest.mark.parametrize('h',[5,21,63,126,189])
def test_horizon_semantics_fixed(h):assert h in m.HORIZONS and pd.Timestamp('2024-01-02')+pd.offsets.BDay(h)>pd.Timestamp('2024-01-02')

def test_truth_cutoff_in_implementation():
 text=(ROOT/'backtesting/location03/evaluate.py').read_text();assert "rows.target_end<='2024-12-18'" in text

def test_control_seed_and_safe_dates(states):
 rows=pd.DataFrame({'origin':['2015-06-01','2017-03-01','2024-11-14']})
 a,r=c.altered_calendar(rows,'RELEASE_DATE_PERMUTATION',5,states);b,rr=c.altered_calendar(rows,'RELEASE_DATE_PERMUTATION',5,states)
 assert np.array_equal(a,b,equal_nan=True);assert np.array_equal(r,rr)
 for origin,rid in zip(rows.origin,r):
  if rid is not None:assert pd.Timestamp(next(x['available_at'] for x in states if x['release_id']==rid))<=s.cutoff(origin)

def test_primary_assets_predeclared():assert m.ASSETS==('UST_2Y','UST_5Y','UST_7Y','UST_10Y','UST_20Y','UST_30Y')

def test_parent_and_main_protection():
 p=json.loads((OUT/'parent_manifest.json').read_text());assert p['parent_result_sha']=='6a9bf9a3507b3dd5b2ef2b8b687b4bfedf89e267'
 assert p['parent_pre_sha']=='d83409f414498b0cadcc508d387252b54dfd1e98';assert p['ECB_CLOSED']
 a=json.loads((OUT/'environment_audit.json').read_text());assert a['main_untouched'];assert a['branch']=='track2/location-03-sloos-alpha'

def test_unverified_pre_blocks_outcomes(tmp_path):
 (tmp_path/'pre_receipt.json').write_text(json.dumps({'remote_verified':False}))
 with pytest.raises((ValueError,FileNotFoundError)):e.verify_pre(tmp_path)

def test_model_input_no_card_or_outcome_features():
 assert not any('truth' in f.lower() or 'delta_card' in f.lower() or 'card' in f.lower() for f in s.FEATURES)
 assert m.MODELS['SLOOS_FULL5_RELEASE_BALANCED']==(0,1,2,3,4)

@pytest.mark.parametrize('ratio,capture,expected',[(1.1,-.1,'NO'),(.96,.07,'WEAK_YES'),(.93,.14,'YES'),(.88,.25,'STRONG_YES')])
def test_frozen_verdict(ratio,capture,expected):
 annual=[{'crps_ratio':ratio}]*8;controls={'null':{'median_ratio':1.1,'fraction_at_least_as_good':0.}}
 assert m.verdict({'crps_ratio':ratio,'oracle_capture':capture},annual,controls,{'crps_ratio_95ci':[.8,.99]},False)==expected

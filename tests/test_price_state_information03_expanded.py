"""Executive summary: expanded audit fixes features, chronology, nulls and public firewall."""
import ast,json,os,subprocess
from pathlib import Path
import numpy as np,pandas as pd,pytest
from sklearn.metrics import balanced_accuracy_score,roc_auc_score
from backtesting.price_state_information03.expanded import core as c
from backtesting.price_state_information03.expanded import evaluate as e

def test_exact_fixed14():
 old=json.loads((c.ROOT/'backtesting/price_state_information03/results/experiment_spec.json').read_text())
 assert list(c.NAMES)==old['features'];assert c.AMPLITUDE==.05;assert c.SEED==31803
 assert c.FOLDS==((2009,2010,2013),(2013,2014,2017),(2017,2018,2020),(2020,2021,2024))
def test_parameters_and_train_only_scaler():
 x=np.arange(120.).reshape(40,3);y=np.tile([0,1],20);f=c.numeric_fit(x,y)
 assert f[1].C==1. and f[1].class_weight is None and f[1].solver=='lbfgs'
 assert f[1].fit_intercept and f[1].tol==1e-8 and f[1].max_iter==2000
 before=f[0].mean_.copy();c.predict(f,x+1e7);assert np.array_equal(before,f[0].mean_)
 assert np.array_equal(before,x.mean(axis=0))
def test_threshold_shift_geometry():
 assert c.direction([.49,.5,.51]).tolist()==[-1,0,1]
 d=np.random.default_rng(9).normal(size=(500,3));s=.05*d.std(axis=0)*c.direction([.49,.5,.51]);out=d+s
 assert np.allclose(out.std(axis=0),d.std(axis=0),atol=1e-14)
 assert np.array_equal(np.argsort(d,axis=0),np.argsort(out,axis=0))
def test_no_amplitude_or_model_search():
 source=Path(e.__file__).read_text()+Path(c.__file__).read_text()
 for forbidden in ['GridSearchCV','RandomForestClassifier','XGBoost','Ridge(']:assert forbidden not in source
 spec=json.loads((c.OUT/'experiment_spec.json').read_text());assert spec['amplitude_SD']==.05
 assert spec['model']['C']==1. and spec['model']['threshold']==.5
def test_publication_and_future_mutation():
 dates=pd.bdate_range('2020-01-01','2020-03-01');frame=pd.DataFrame(np.arange(len(dates)*14).reshape(-1,14),index=dates)
 origins=['2020-01-20','2020-01-21'];a=c.asof_prices(origins,frame)
 mutated=frame.copy();mutated.loc['2020-02-01':]=1e9;b=c.asof_prices(origins,mutated)
 assert np.array_equal(a[0],b[0]);assert np.array_equal(a[1],b[1])
 for origin,date in zip(origins,a[1]):assert c.available_eod(pd.Timestamp(date)+pd.offsets.BDay(1))<=c.origin_cutoff(origin)
def test_source_state_outcome_mutation():
 rows=pd.DataFrame({'origin':['2020-01-20'],'truth':[9.]});dates=pd.bdate_range('2020-01-01','2020-02-01');f=pd.DataFrame(np.ones((len(dates),14)),index=dates)
 a=c.asof_prices(rows.origin.tolist(),f);rows.truth=-1e9;b=c.asof_prices(rows.origin.tolist(),f);assert np.array_equal(a[0],b[0])
def test_future_mutation_predictions_bitwise():
 dates=pd.bdate_range('2019-01-01','2020-03-01');frame=pd.DataFrame(np.arange(len(dates)*14).reshape(-1,14),index=dates)
 origins=['2019-06-03','2019-07-01','2019-08-01','2019-09-02'];x=c.asof_prices(origins,frame)[0];fit=c.numeric_fit(x,np.array([0,1,0,1]))
 before=c.predict(fit,c.asof_prices(['2020-01-20'],frame)[0]);mutated=frame.copy();mutated.loc['2020-02-01':]=-1e12
 after=c.predict(fit,c.asof_prices(['2020-01-20'],mutated)[0]);assert np.array_equal(before,after)
def test_concentration_includes_all_groups():
 from backtesting.price_state_information03.expanded.aggregate import concentration
 rows=pd.DataFrame({'year':[2020,2020,2021],'asset':['A','A','B'],'horizon':[5,21,5],'origin':['a','b','c']})
 table=np.array([[2.,2.,2.],[2.,2.,2.],[1.,1.,3.]])
 a=concentration(rows,np.ones(3),table);assert a['year']['largest_share']==1.;assert a['year']['net_gain_sum']==1.
 assert a['year']['all_group_gains']=={'2020':2.,'2021':-1.}
def test_purge_and_cutoff():
 rows=pd.DataFrame({'origin':['2017-04-03','2017-04-04','2017-12-01'],'target_end':['2017-12-26','2018-01-02','2017-12-31']})
 mask=c.purged_mask(rows,'2018-01-01');assert mask.tolist()==[True,False,False]
 spec=json.loads((c.OUT/'experiment_spec.json').read_text());assert spec['cutoff']=='2024-12-18'
@pytest.mark.parametrize('kind',['N1','N2','N3'])
def test_train_null_labels_deterministic(kind):
 rows=pd.DataFrame({'year':[2016]*4+[2017]*4,'asset':['A']*8,'horizon':[5]*8,'origin':['2016-01-04','2016-02-04','2016-07-04','2016-08-04','2017-01-04','2017-02-04','2017-07-04','2017-08-04']});y=np.array([0,1]*4)
 a=c.null_labels(rows,y,kind,4,3);b=c.null_labels(rows,y,kind,4,3)
 assert np.array_equal(a,b);assert sorted(a)==sorted(y);assert np.array_equal(y,[0,1]*4)
def test_historical_donor_no_future():
 idx=np.array([0,1,2,100]);a=c.historical_donors(idx,7,3);assert (a<=idx).all();assert (a[1:]<idx[1:]).all();assert np.array_equal(a,c.historical_donors(idx,7,3))
def test_balanced_metrics():
 y=np.array([-1,-1,-1,1]);p=np.array([.1,.2,.7,.8]);d=c.direction(p);m=c.information(p,y,y)
 assert m['Balanced_Accuracy']==balanced_accuracy_score(y,d);assert m['AUC']==roc_auc_score(y>0,p)
def test_equal_origin_year_asset_weights():
 for g in [['a','a','b'],[2020,2020,2021]]:assert np.array_equal(c.weights(g),[.5,.5,1.])
def test_ties_only_excluded_from_classifier():
 y=np.array([0,-1,1]);p=np.array([.5,.1,.9]);m=c.information(p,y,y);assert m['Direction_Accuracy']==1.
 assert len(c.direction(p))==3
def test_deterministic_asset_encoding():
 r=pd.DataFrame({'asset':['A','B','C'],'horizon':[5,21,63],'truth':[1,2,3]});s=c.structure(r,['A','B','C']);assert s.shape==(3,3);assert np.array_equal(s[:,:2],[[0,0],[1,0],[0,1]])
 r.truth=-100;assert np.array_equal(s,c.structure(r,['A','B','C']))
def test_training_only_secondary_imputation():
 a=np.array([[1,np.nan],[3,np.nan]]);b=np.array([[1e9,np.nan]]);tr,te,fill=c.impute_training(a,b);assert fill.tolist()==[2,0];assert te[0,1]==0
def test_inventory_and_c_contamination_flag():
 i=json.loads((c.OUT/'existing_price_feature_inventory.json').read_text());s=json.loads((c.OUT/'frozen_feature_spec.json').read_text());p=json.loads((c.OUT/'price_pit_audit.json').read_text())
 assert s['price_names']==list(c.NAMES);assert p['PIT']=='C' and p['PIT_LIMITATION_UNRESOLVED'];assert not p['validated_alpha_ready']
 names={f['name'] for f in i['features']}
 assert all(set(v)<=names for v in s['secondary_groups'].values())
def test_primary_eligibility_before_labels():
 m=json.loads((c.OUT/'canonical_ledger_manifest.json').read_text());assert not m['outcomes_accessed'];assert m['origins']==1250 and m['cells']==135994
 assert not set(m['eligibility_columns'])&{'truth','delta','median','sd'}
 a=json.loads((c.private()/'preparation_audit.json').read_text());assert not a['outcome_labels_deserialized']
def test_no_prior_files_changed():
 changes=subprocess.check_output(['git','diff','--name-only',c.PRIOR],cwd=c.ROOT,text=True).splitlines()
 allowed=('backtesting/price_state_information03/expanded/','backtesting/price_state_information03/results/expanded_20261008/','backtesting/price_state_information03/expanded_STATUS.json','tests/test_price_state_information03_expanded.py','PRICE-STATE-INFORMATION-AUDIT-03-expanded-20261008-report.md')
 assert all(name.startswith(allowed) for name in changes)
 # Extension files are allowed; original tracked source/results stay byte-identical.
 original=json.loads((c.ROOT/'backtesting/price_state_information03/results/artifact_manifest.json').read_text())['files']
 for name,v in original.items():assert c.digest(c.ROOT/name)==v['SHA256']
def test_parent_main_protection():
 assert subprocess.run(['git','merge-base','--is-ancestor',c.PARENT,'HEAD'],cwd=c.ROOT).returncode==0
 assert subprocess.check_output(['git','rev-parse','origin/main'],cwd=c.ROOT,text=True).strip()==c.MAIN
def test_null_counts_and_confidence_bins_frozen():
 assert c.NULL_REPS==2000 and c.RANDOM_REPS==5000 and c.BOOTSTRAP_REPS==5000
 assert c.CONFIDENCE_EDGES==(0,.05,.10,.20,.50)
def test_no_private_outcome_public_csv():
 for f in c.OUT.glob('*predictions.csv'):
  assert not set(pd.read_csv(f,nrows=0).columns)&{'truth','y','delta','median','sd','loss','raw_center_error'}
@pytest.mark.skipif(not (c.private()/'expanded_pre_receipt.json').exists(),reason='Expanded remote PRE not yet verified')
def test_pre_remote_receipt():assert c.verify_pre()['remote_verified']
@pytest.mark.skipif(not (c.OUT/'final_decision.json').exists(),reason='Expanded results not evaluated before PRE')
def test_final_category_and_exact_next():
 a=json.loads((c.OUT/'final_decision.json').read_text());assert a['PRICE_STATE_INFO03_EXPANDED_RESULT'] in ['REAL_PRICE_STATE_SIGNAL','WEAK_PRICE_STATE_SIGNAL','NULL_LIKE','CONCENTRATED_OR_UNSTABLE','PIT_BLOCKED']
 assert a['NEXT']=='PRICE-PIT-RECOVERY-04';assert not a['INDEPENDENT_OOS'];assert not a['submission']

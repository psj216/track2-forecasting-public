"""Executive summary: frozen-price reproduction, target-blind controls and chronology."""
import ast,json,os,subprocess
from pathlib import Path
import numpy as np,pandas as pd,pytest
from scipy.stats import spearmanr
from backtesting.price_state_information03 import core as c
from backtesting.price_state_information03 import run as r
P=Path(os.environ.get('PRICE03_PRIVATE','/unavailable'))
PP=Path(os.environ.get('PRICE03_PARENT_PRIVATE','/unavailable'))

def test_constants():
 assert c.PARENT=='929ca23e0a57a0529cc64d8a14d5a78b791892e6';assert c.PARENT_PRE=='2bdc6722fd5705887bee5f0695a09fe2319bf431';assert c.AMPLITUDE==.05;assert c.SEED==31803;assert c.LAGS==(5,21,63);assert c.HORIZONS==(5,21,63,126,189)
def test_parent_reproduction_schema():
 a=json.loads((c.OUT/'parent_price_reproduction.json').read_text());assert a['loss_arrays_bitwise_equal'];assert not a['PRICE_FULL_refitted'];assert len(a['models'])==9;assert all(abs(x['difference'])<1e-14 for x in a['models'])
def test_price_full_no_refit():
 src=Path(r.__file__).read_text();assert "probs[new]=data['prob_'+old]" in src
 tree=ast.parse(src);assert not any(isinstance(a,ast.Name) and a.id in ['GridSearchCV','Ridge','RandomForestClassifier'] for a in ast.walk(tree))
def test_frozen_model_parameters_train_scaler():
 x=np.arange(80.).reshape(40,2);y=np.tile([0,1],20);f=c.fit_control(x,y);sc,m=f
 assert m.C==1 and m.class_weight is None and m.fit_intercept and m.tol==1e-8 and m.max_iter==2000
 assert np.array_equal(sc.mean_,x.mean(axis=0));before=sc.mean_.copy();c.predict(f,x+1e6);assert np.array_equal(before,sc.mean_)
@pytest.mark.parametrize('y,p', [([0,1],.5),([1,1,0],2/3),([0,0,1],1/3)])
def test_prior_training_only(y,p):assert c.prior_probability(y)==p
def test_group_training_only():
 assert np.array_equal(c.group_prior(['A','A','B'],[0,0,1],['B','A','C']),[1,0,0])
def test_structure_has_no_price():
 a=pd.DataFrame({'asset':['UST_2Y','UST_5Y'],'horizon':[5,21],'price_fake':[99,999],'truth':[1,-1]});assert c.structure(a).shape==(2,2);assert np.array_equal(c.structure(a)[:,0],[0,1])
@pytest.mark.parametrize('p,d',[(.49,-1),(.5,0),(.51,1)])
def test_threshold_fixed(p,d):assert c.direction([p])[0]==d
def test_shift_geometry():
 d=np.random.default_rng(31803).normal(size=(500,10));sd=d.std(axis=0);shift=.05*sd*c.direction(np.linspace(0,1,10));shifted=d+shift
 assert np.allclose(shifted.std(axis=0),sd,atol=1e-14);assert np.array_equal(np.argsort(d,axis=0),np.argsort(shifted,axis=0))
@pytest.mark.parametrize('lag',[5,21,63])
def test_past_only_lag(lag):
 dates=pd.bdate_range('2016-01-01','2020-01-10');frame=pd.DataFrame(np.arange(len(dates)*14).reshape(-1,14),index=dates)
 rows=pd.DataFrame({'price_observation_date':['2020-01-06'],'asset':['UST_2Y'],'horizon':[5]});x,chosen=c.lag_price(rows,lag,frame)
 assert chosen[0]==pd.Timestamp('2020-01-06')-pd.offsets.BDay(lag);assert x.shape==(1,16)
def test_whole_origin_permutation_train_only():
 origins=np.repeat(['2017-01-03','2018-01-02','2019-01-01'],2);x=np.column_stack([np.repeat(np.arange(3),2)[:,None]*np.ones((6,14)),np.arange(12).reshape(6,2)])
 a,donors=c.permuted_train_price(x,origins,9,2020);b,_=c.permuted_train_price(x,origins,9,2020)
 assert np.array_equal(a,b);assert set(donors)==set(origins);assert np.array_equal(a[:,14:],x[:,14:]);assert all(np.array_equal(a[i,:14],a[i+1,:14]) for i in [0,2,4])
def test_random_target_firewall():
 params=ast.parse(Path(c.__file__).read_text());f=next(a for a in params.body if isinstance(a,ast.FunctionDef) and a.name=='random_signs')
 assert [a.arg for a in f.args.args]==['signs','groups','rep','kind'];assert not any(isinstance(a,ast.Name) and a.id in ['truth','y','loss','target'] for a in ast.walk(f))
@pytest.mark.parametrize('group',[np.ones(6),np.array([0,0,0,1,1,1])])
def test_random_exact_frequencies(group):
 s=np.array([-1,0,1,1,1,-1]);a=c.random_signs(s,group,4,0);assert np.array_equal(a,c.random_signs(s,group,4,0))
 for g in np.unique(group):assert sorted(a[group==g])==sorted(s[group==g])
@pytest.mark.parametrize('groups',[['a','a','b'],[2020,2020,2021]])
def test_equal_group_weight(groups):
 w=c.balanced_weights(groups);assert w.tolist()==[.5,.5,1];assert sum(w[:2])==w[2]
def test_spearman_matches_parent_unweighted():
 a=np.array([.2,.9,.9,.7,.2]);b=np.array([0,1,0,1,1]);w=np.ones(5);assert abs(c.correlation(c.weighted_rank(a,w),c.weighted_rank(b,w),w)-spearmanr(a,b).statistic)<1e-14
def test_grouping_frozen():
 assert len(c.PRICE_NAMES)==14;assert sorted(sum((list(x) for x in c.GROUPS.values()),[]))==list(range(14))
def test_broader_blocked_before_evaluation():
 a=json.loads((c.OUT/'broader_ledger_spec.json').read_text());b=json.loads((c.OUT/'broader_transfer_readiness.json').read_text());assert a['outcomes_accessed']==False;assert not b['BROAD_TRANSFER_READY'];assert b['price_PIT']=='C'
def test_protected_parent_main():
 c.assert_protected();assert subprocess.run(['git','merge-base','--is-ancestor',c.PARENT,'HEAD'],cwd=c.ROOT).returncode==0
@pytest.mark.skipif(not (P/'audit_predictions.npz').exists(),reason='new diagnostics not executed before remote PRE')
def test_prediction_hash_preservation():
 a=np.load(P/'audit_predictions.npz');b=np.load(PP/'scores.npz');i=list(a['names']).index('PRICE_FULL');assert np.array_equal(a['probabilities'][i],b['prob_PRICE_LOGISTIC']);assert np.array_equal(a['losses'][i],b['losses'][list(b['names']).index('PRICE_LOGISTIC')])
@pytest.mark.skipif(not (P/'pre_receipt.json').exists(),reason='remote PRE not created yet')
def test_pre_and_input_preservation():c.verify_pre()
@pytest.mark.skipif(not (P/'audit_predictions.npz').exists(),reason='results gated by PRE')
def test_full_ledger_no_subset():
 rows,ev,_=c.load();assert ev.origin.nunique()==52 and len(ev)==482;assert set(ev.year)==set(c.YEARS);assert set(ev.horizon)==set(c.HORIZONS);assert set(ev.asset)=={'UST_2Y','UST_5Y'}

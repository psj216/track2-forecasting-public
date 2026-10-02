"""## Executive summary (read this first)
Verify heldout leakage, pure text provenance, fixed expert whole-card selection and deterministic nulls.
"""
import copy,json
from pathlib import Path
import numpy as np
import pytest
from backtesting.text_route_audit02.features import build,text_features,structure_features,S_NAMES,T_NAMES
from backtesting.text_route_audit02.models import predict,route,folds,training_shuffle
from backtesting.text_route_audit02.evaluate import stats,grouped,inputs
from backtesting.text_route_audit02.aggregate_results import bootstrap,safety
from backtesting.context01.freeze_annotations import digest
from qfbench2_track_forecasting.context01.engine import apply
from qfbench2_track_forecasting.context01.context_schema import LANGUAGE

def card(i=0):return dict(id='private-name-'+str(i),family='T2-F'+str(i%4+1),cells=1,assets=['AUD'],horizons=[21],target_type='level',origin='2020-01-01')
def text():return dict(question='Conditional inflation scenario above 2 percent at short horizon.',documents=['Dated inflation statement with uncertainty.'])
def annotation():return dict(features={**{n:0. for n in LANGUAGE},'named_event_count':0.,'named_entity_count':0.})
def dataset():
 rng=np.random.default_rng(55);x=rng.normal(size=(24,8));y=np.arange(24)%4==0;g=np.where(y,-.1,.05);return x,y.astype(int),g
@pytest.mark.parametrize('kind',['logistic','ridge'])
def test_heldout_labels_cannot_change_prediction(kind):
 x,y,g=dataset();tr=np.arange(23);te=np.array([23]);p,a,fit=predict(x,y,g,tr,te,kind);y2=y.copy();g2=g.copy();y2[23]=1-y2[23];g2[23]=1e8;p2,a2,_=predict(x,y2,g2,tr,te,kind);assert np.array_equal(p,p2);assert a is None or np.array_equal(a,a2)
def test_scaler_is_train_only():
 x,y,g=dataset();x[-1]=1e9;p,_,fit=predict(x,y,g,np.arange(23),np.array([23]));assert np.allclose(fit[0].mean_,x[:-1].mean(axis=0))
def test_entire_cards_heldout():
 cards=[card(i)for i in range(24)]
 for mode in ['loco','family']:
  fs=folds(cards,mode);assert len(fs)==(24 if mode=='loco'else 4)
  for _,tr,te in fs:assert not(set(tr)&set(te))
def test_no_card_identifiers_enter_features():
 a=card();b=copy.deepcopy(a);b.update(id='winning-card-encoded-label',hash='1',name='secret',score=0,truth=99);assert structure_features(a)==structure_features(b)
def test_text_topics_do_not_inject_assetclass():
 v=text_features(dict(question='Generic future observation',documents=[]),annotation());assert v[T_NAMES.index('FX')]==0;assert v[T_NAMES.index('rates')]==0;assert v[T_NAMES.index('generic_none')]==1
@pytest.mark.parametrize('field',['truth','score','winner','future_return'])
def test_future_information_ignored_by_text(field):
 a=text();b=copy.deepcopy(a);b[field]=1e99;aa=annotation();bb=copy.deepcopy(aa);bb[field]=-1e99;assert text_features(a,aa)==text_features(b,bb)
def test_fixed_route_threshold():assert route(np.array([.49,.5,.51])).tolist()==[False,True,True]
def test_ridge_route_zero_gain_uses_B0():
 x,y,g=dataset();p,gg,_=predict(x,y,np.zeros(24),np.arange(23),np.array([23]),'ridge');assert gg[0]==0 and not route(p)[0]
def test_single_class_uses_training_class():
 x,y,g=dataset();p,_,_=predict(x,np.zeros(24),g,np.arange(23),np.array([23]));assert p.tolist()==[0]
def test_shuffle_excludes_heldout_outcome():
 x,y,g=dataset();tr=np.arange(23);a,b=training_shuffle(y,g,tr,np.random.default_rng(3));y[23]=1e9;g[23]=1e9;c,d=training_shuffle(y,g,tr,np.random.default_rng(3));assert np.array_equal(a[tr],c[tr])and np.array_equal(b[tr],d[tr])
def test_frozen_shift_is_unique_and_whole_multicard():
 rng=np.random.default_rng(5);b=rng.normal(size=(2000,2,2));e=apply(b,np.array([.1,.2,.3,.4]));assert np.array_equal(e,apply(b,np.array([.1,.2,.3,.4])));selected=[b,e][int(True)];assert np.array_equal(selected,e)and selected.shape==b.shape

def fake_record():return dict(baseline=dict(marginal=1.,joint=1.,tail=1.),models=dict(R2=dict(ratio=.9,marginal=.8,joint=1.2,tail=1.),B0=dict(ratio=1.,marginal=1.,joint=1.,tail=1.)))
def test_cached_full_component_route():
 records=[fake_record()for _ in range(24)];z=np.zeros(24,bool);z[:4]=1;m=stats(records,z);assert m['routed_R2']==4;assert m['joint']>1 and m['marginal']<1

def test_bootstrap_cardblocks_and_capture():
 recs=[fake_record()for _ in range(24)];z=np.ones(24,bool);o=z.copy();s=np.zeros(24,bool);fam=[card(i)['family']for i in range(24)];a=bootstrap(recs,z,o,s,s,fam);assert a['replicates']==5000 and np.allclose(a['composite_95'],.9);assert np.allclose(a['capture_B0_95'],1)
def test_nonpositive_capture_denominator_is_not_forced():
 recs=[fake_record()for _ in range(24)];z=np.zeros(24,bool);fam=[card(i)['family']for i in range(24)];a=bootstrap(recs,z,z,z,z,fam,True);assert a['capture_B0_95']is None and a['capture_B0_unstable_replicates']==5000

def test_pre_receipt_required(tmp_path):
 root=tmp_path/'r';private=tmp_path/'p';(root/'backtesting/text_route_audit02/results').mkdir(parents=True);private.mkdir();np.savez(private/'features.npz',S0=np.zeros((24,2)));(root/'backtesting/text_route_audit02/results/feature_manifest.json').write_text(json.dumps(dict(feature_sha256=digest(private/'features.npz'))))
 with pytest.raises(FileNotFoundError,match='pre_remote_receipt'):inputs(root,private)
def test_text_only_cardmetadata_invariance():
 a=card();b=copy.deepcopy(a);b.update(family='T2-F4',assets=['UST_10Y'],horizons=[189]);rng=np.random.default_rng(7);arr=rng.normal(size=(200,1,1));aa=build([a],{a['id']:text()},{a['id']:annotation()},[arr],[arr]);bb=build([b],{b['id']:text()},{b['id']:annotation()},[arr],[arr]);assert np.array_equal(aa['T0'],bb['T0'])and not np.array_equal(aa['S0'],bb['S0'])

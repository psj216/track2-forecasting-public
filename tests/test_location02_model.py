"""Executive summary: fixed-model, chronological purge and synthetic geometry tests."""
import json
import numpy as np
import pandas as pd
from backtesting.location02.model import fit_ridge,predict,shift,train_mask,release_weights,MODELS,SEED
from backtesting.location02.source_dataset import FEATURES


def test_train_only_scaler_alpha_and_test_not_fitted():
    x=np.arange(50.).reshape(10,5);y=np.linspace(-1,1,10);releases=np.repeat(['a','b'],5)
    fit=fit_ridge(x,y,releases,tuple(range(5)))
    before=fit[0].mean_.copy();out=predict(fit,np.full((2,5),999.),tuple(range(5)))
    np.testing.assert_array_equal(before,fit[0].mean_)
    np.testing.assert_allclose(before,np.average(x,axis=0,weights=release_weights(releases)))
    assert fit[1].alpha==1.0 and len(out)==2
    assert len(FEATURES)==5 and MODELS['ECB_RIDGE_FULL5']==tuple(range(5))


def test_pure_location_geometry_sd_and_ranks():
    rng=np.random.default_rng(SEED);draws=rng.normal(size=(500,5));sd=draws.std(axis=0)
    result=shift(draws,np.array([.1,.2,-.2,2.,-1.]),sd)
    np.testing.assert_allclose(result.std(axis=0),sd,rtol=1e-14)
    np.testing.assert_array_equal(np.argsort(result,axis=0),np.argsort(draws,axis=0))
    np.testing.assert_allclose(result-result[0],draws-draws[0],atol=1e-14)


def test_chronological_horizon_purge_and_release_leakage():
    rows=pd.DataFrame({'origin':['2018-01-02','2019-11-01','2020-01-02','2018-02-02'],
       'target_end':['2018-02-01','2020-03-01','2020-04-01','2018-03-01'],
       'round_id':['2017Q4','2019Q4','2019Q4','2019Q4']})
    mask=train_mask(rows,2020,'2020-01-01T16:00:00-05:00')
    assert mask.tolist()==[True,False,False,False]
    assert not (pd.to_datetime(rows.loc[mask,'target_end'])>=pd.Timestamp('2020-01-01')).any()


def test_release_balance_deterministic_seeds():
    weights=release_weights(['a','a','b'])
    np.testing.assert_array_equal(weights,[.5,.5,1.])
    x=np.random.default_rng(SEED).normal(size=(30,5));y=x[:,0];r=np.repeat(['a','b','c'],10)
    np.testing.assert_array_equal(predict(fit_ridge(x,y,r,(0,1,2,3,4)),x,(0,1,2,3,4)),
                                  predict(fit_ridge(x,y,r,(0,1,2,3,4)),x,(0,1,2,3,4)))


def test_future_feature_mutation_predictions_unchanged():
    rng=np.random.default_rng(SEED);x=rng.normal(size=(40,5));y=rng.normal(size=40)
    r=np.repeat(['a','b','c','d'],10)
    first=predict(fit_ridge(x[:20],y[:20],r[:20],(0,1,2,3,4)),x[20:25],(0,1,2,3,4))
    x[30:]+=1000.;y[30:]=-1000.
    after=predict(fit_ridge(x[:20],y[:20],r[:20],(0,1,2,3,4)),x[20:25],(0,1,2,3,4))
    np.testing.assert_array_equal(first,after)

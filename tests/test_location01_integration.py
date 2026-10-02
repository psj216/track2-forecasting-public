"""## Executive summary (read this first)

Exercise all frozen model sequences, controls, scoring and block uncertainty.
"""
import numpy as np
import pandas as pd
from qfbench2_track_forecasting.location01.model import LocationModel,choose_alpha,purged_mask
from backtesting.location01.negative_controls import permute_labels,wrong_date_features
from backtesting.location01.diagnostics import metrics,success
from backtesting.location01.bootstrap import year_bootstrap
from backtesting.location01.evaluate_card_transfer import summarize

def test_pipeline_synthetic():
    dates=pd.bdate_range('2001-01-02','2011-12-30')[::3]
    rows=pd.DataFrame([{'origin':str(d.date()),'target_end':str((d+pd.offsets.BDay(189)).date()),
                       'asset':a,'horizon':189} for d in dates for a in ('EUR','JPY')])
    rng=np.random.default_rng(19);x=rng.normal(size=(len(rows),6))
    x[::19,1]=np.nan
    schema=['M_asset_EUR','F_sd','O_move','X_JPY_5','R_mean_5','O_vol']
    x[:,0]=(rows.asset=='EUR').to_numpy();y=.4*np.nan_to_num(x[:,1])+rng.normal(size=len(rows))
    train=purged_mask(rows,'2010-01-01');test=(rows.origin>='2010-01-01').to_numpy()
    wrong,donors=wrong_date_features(x,rows,schema)
    for model in range(6):
        for nonlinear in (False,True):
            fitted=LocationModel(model,nonlinear).fit(x[train],y[train],schema,1.)
            pp,caps=fitted.predict(x[test]);assert np.isfinite(pp).all() and len(pp)==test.sum()
            if model==0:assert np.array_equal(pp,np.zeros(len(pp)))
        if model:
            alpha,audit=choose_alpha(wrong[train],y[train],schema,rows.loc[train].reset_index(drop=True),model,2009,
                lambda rr,labels:permute_labels(rr,labels,'A_label_time'))
            assert alpha in (.01,.1,1.,10.,100.) and audit['inner_folds']==2
    years=pd.to_datetime(rows.loc[test,'origin']).dt.year.to_numpy()
    b=np.ones(test.sum());candidate=b*.96;oracle=b*.4
    interval=year_bootstrap(years,b,candidate,oracle)
    np.testing.assert_allclose(interval['ratio_95_interval'],[.96,.96])
    v=metrics(y[test],np.zeros(test.sum()),b,candidate,oracle)
    assert success(v,[.94,.95,.96,1.01],True)=='WEAK_YES'
    assert success(v,[.94,.95,1.01,1.01],True)=='NO'
    assert success(v,[.94]*4,False)=='NO'
    records=[{'baseline':{'marginal':2.,'joint':4.,'tail':1.},
              'candidate':{'marginal':1.8,'joint':4.4,'tail':.9,'ratio':.97},
              'oracle':{'ratio':.4}}]*6
    transfer=summarize(records)
    assert np.isclose(transfer['joint_ratio'],1.1) and np.isclose(transfer['oracle_capture_fraction'],.05)

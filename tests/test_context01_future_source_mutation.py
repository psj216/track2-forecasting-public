"""## Executive summary (read this first)
Verify the frozen context research contract with synthetic data only.
"""
import numpy as np
from qfbench2_track_forecasting.context01.deterministic_annotator import annotate,matrix
from qfbench2_track_forecasting.context01.context_schema import schema
CARD=dict(id='synthetic',family='T2-F1',origin='2020-01-06',assets=['UST_2Y'],horizons=[21,63],cells=2,target_type='level',frequency='daily')
def annotation(card=CARD):return annotate(card,'Assuming inflation rises, forecast the joint yield path in 2020 above 2 percent.', ['The Federal Reserve may consider uncertainty.'])
from copy import deepcopy
from qfbench2_track_forecasting.context01.expert_transfer import quantity_query
def test_future_report_values_do_not_change_asof_query():
 r=dict(release_date='2020-01-01',observation_date='2019-12-31',publication_time_et='23:59',features=[1.,2.,3.,4.,5.],event_id='old');future={**r,'release_date':'2020-02-01','event_id':'future'};sources={'F':[r,future],'L':[r,future]}
 cols=[dict(name='L_'+str(i),class_id='L',stage=1)for i in range(7)];rows=[dict(origin='2020-01-06',asset='AUD',horizon=21)];before=quantity_query(rows,sources,cols);after=deepcopy(sources);after['L'][1]['features']=[1e9]*5;np.testing.assert_array_equal(before,quantity_query(rows,after,cols))
def test_future_survey_values_do_not_change_asof_query():
 from qfbench2_track_forecasting.context01.expert_transfer import expectation_query
 snaps=[dict(family=f,publication_date=d,target=t,value=v,source_id='synthetic',survey_id=d)for f in ['RGDP','CPI']for d in ['2020-01-01','2020-02-01']for t,v in [('2020Q1',1.),('2020Q2',2.)]]
 rows=[dict(origin='2020-01-06',asset='UST_2Y',group='Rates',horizon=21)];cols=[dict(name='E_RGDP_current',stage=1,family='RGDP'),dict(name='E_CPI_current',stage=1,family='CPI')]
 before=expectation_query(rows,snaps,[],cols);changed=deepcopy(snaps)
 for v in changed:
  if v['publication_date']>'2020-01-06':v['value']=1e9
 np.testing.assert_array_equal(before,expectation_query(rows,changed,[],cols))

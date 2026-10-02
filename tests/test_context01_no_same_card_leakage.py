"""## Executive summary (read this first)
Verify the frozen context research contract with synthetic data only.
"""
import numpy as np
from qfbench2_track_forecasting.context01.deterministic_annotator import annotate,matrix
from qfbench2_track_forecasting.context01.context_schema import schema
CARD=dict(id='synthetic',family='T2-F1',origin='2020-01-06',assets=['UST_2Y'],horizons=[21,63],cells=2,target_type='level',frequency='daily')
def annotation(card=CARD):return annotate(card,'Assuming inflation rises, forecast the joint yield path in 2020 above 2 percent.', ['The Federal Reserve may consider uncertainty.'])
import pytest
from qfbench2_track_forecasting.context01.semantic_model import fit_fold
def test_same_card_outer_split_rejected():
 with pytest.raises(ValueError,match='Same card'):fit_fold(np.eye(3),np.arange(3.),np.array(['a','a','b']),np.array([1,0,1],bool),np.array([0,1,0],bool))
def test_outer_label_mutation_does_not_change_prediction():
 ids=np.array(['a','a','b','b','c','c']);x=np.arange(18.).reshape(6,3)/20;y=np.arange(6.);test=ids=='c';train=~test
 p=fit_fold(x,y,ids,train,test)[0];yy=y.copy();yy[test]=1e6;np.testing.assert_array_equal(p,fit_fold(x,yy,ids,train,test)[0])

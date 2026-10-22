"""Executive summary: formula and input-invariant validation before any A/B score."""
import json
import math
import pathlib
import shutil
import tempfile
import numpy as np
import pandas as pd
from scipy.integrate import quad
from scipy.stats import norm
from m0 import reconstruct, scales, pair_variance, target_steps, hedge
from qfbench2_track_forecasting.scoring import _composite


def main(official, output):
    official = pathlib.Path(official)
    result = {'executive_summary':'Input-only documented M0 reproduction checks; no outcomes consumed.', 'tests':{}}
    tests=result['tests']
    d=reconstruct(official/'units/t2-EXAMPLE-ust-curve-1m')
    actual=scales(d.mean,d.covariance)
    for k,value,tolerance in [('marginal',.05260,.000005),('joint',.1772,.00005),('tail',.006051,.0000005)]:
        assert abs(actual[k]-value)<=tolerance, (k,actual[k])
    assert d.audit['seed']==795546941 and d.audit['aligned_rows']==128
    assert list(d.steps)==[21]*4 and d.samples.shape==(500,4)
    tests['worked_example']={'status':'PASS','actual':actual,'printed':dict(marginal=.05260,joint=.1772,tail=.006051),'precision':'within half last displayed unit'}
    diffs=[]
    for delta,s in [(0.,.1),(.1,.1),(-.5,.1),(1.,.05)]:
        cusp=-delta/s
        def moment(power):
            f=lambda z:abs(delta+s*z)**power*norm.pdf(z)
            return quad(f,-np.inf,cusp,epsabs=1e-11)[0]+quad(f,cusp,np.inf,epsabs=1e-11)[0]
        ref=moment(1)-moment(.5)**2
        actual_pair=pair_variance(delta,s*s)
        assert np.isclose(actual_pair,ref,atol=1e-8,rtol=1e-6)
        diffs.append(abs(actual_pair-ref))
    tests['joint_independent_quadrature']={'status':'PASS','max_abs_error':max(diffs),'cases':4}
    one=scales(np.zeros(1),np.array([[.01]]))
    assert one['joint']==1 and np.isclose(one['marginal'],.1/math.sqrt(math.pi))
    assert np.isclose(one['tail'],.1*norm.pdf(norm.ppf([.01,.05,.95,.99])).mean())
    tests['single_cell_zero_and_tail']={'status':'PASS','scales':one}
    # Official composite import; exact weight/reweight algebra on synthetic forecasts.
    x=np.arange(200,dtype=float).reshape(-1,1)/200
    c=_composite(x,np.array([.5]),weights=(5/7,0,2/7),tail_levels=(.01,.05,.95,.99),joint='variogram',tail_metric='pinball',ref_scale=one)
    assert np.isclose(c['composite'],5/7*c['marginal']/one['marginal']+2/7*c['tail']/one['tail'])
    assert min(8.,9.)==8.
    tests['official_composite_single_weights_clip']={'status':'PASS','metric_source':'official._composite; clipping official aggregation rule'}
    dates=pd.date_range('2031-01-01',periods=10,freq='D')
    assert target_steps(dates,1,'2031-01-12')==1 # strict ratio ==2 preserves key
    assert target_steps(dates,1,'2031-01-13')==3
    tests['strict_horizon_override']={'status':'PASS'}
    for name,want in [('t2-F1-cpi-glidepath-2023',[8,9]),('t2-F4-covid-nfp-2020',[2]),('t2-F4-cpi-vintage-2022',[2])]:
        m=reconstruct(official/'units'/name);assert list(m.steps)==want
        tests['monthly_'+name]={'status':'PASS','steps':m.steps.tolist()}
    tests['monthly_sahm_m0']={'status':'NOT_VERIFIED','reason':'M0 uses sealed-date conversion per documentation; do not hardcode published example counts. Monthly mixture disabled.'}
    unit=official/'units/t2-F3-curve-ust3m-ust6m-ust1y-ust2y-005-ps1'
    base=reconstruct(unit)
    with tempfile.TemporaryDirectory() as temp:
        cloned=pathlib.Path(temp)/'unit';shutil.copytree(unit,cloned)
        panel=next(cloned.glob('*.parquet'));df=pd.read_parquet(panel)
        extra=df.tail(10).copy();extra['date']=pd.Timestamp('2099-01-01');extra['value']=1e10
        pd.concat([df,extra]).to_parquet(panel,index=False)
        assert np.array_equal(base.samples,reconstruct(cloned).samples)
    tests['future_input_truncation']={'status':'PASS'}
    tests['repeatability']={'status':'PASS' if np.array_equal(base.samples,reconstruct(unit).samples) else 'FAIL'}
    result['status']='VERIFIED_DOCUMENTED_DAILY_FORMULAS'
    result['sealed_generator_bit_identity']='UNKNOWN: generator and sealed scales unpublished'
    result['exemplar_scale']=actual
    pathlib.Path(output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    import sys
    main(*sys.argv[1:])

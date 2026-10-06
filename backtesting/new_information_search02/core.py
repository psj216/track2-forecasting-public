"""Executive summary: deterministic source-state diagnostics; never fit a forecast or score outcomes."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
from scipy.stats import rankdata
PARENT='16ef4d87f15151796b072e2a6f658ec076171bda'
MAIN='e1b5cf3b3a87966e902332ef3cc5c0ed2dbffee8'
STATE_COLUMNS=['origin_date','asset','horizon','release_id','frozen_prediction','direction']
SCORE_COLUMNS=['pit','timing','depth','relevance','novelty','persistence','alignment','readability','reproducibility','rights']
def project_state(df):
    """Allowlist is the firewall, including when caller passes additional outcomes."""
    result=df.loc[:,STATE_COLUMNS].copy()
    assert set(result.asset)<= {'UST_2Y','UST_5Y'}
    assert set(result.horizon)<= {5,21,63,126,189}
    assert np.array_equal(result.direction.to_numpy(),np.sign(result.frozen_prediction.to_numpy()))
    return result

def origin_cutoff(origin):
    """Parent cutoff: previous weekday 16:00 America/New_York, DST-aware."""
    day=pd.Timestamp(origin).normalize()-pd.offsets.BDay(1)
    return (day+pd.Timedelta(hours=16)).tz_localize(ZoneInfo('America/New_York')).tz_convert('UTC')

def available_eod(day):
    return (pd.Timestamp(day).normalize()+pd.Timedelta(hours=23,minutes=59,seconds=59)).tz_localize(ZoneInfo('America/New_York')).tz_convert('UTC')

def join_asof(state,source,max_age_BD=None):
    """No leads, lag search or interpolation. Only latest available published state."""
    a=project_state(state); b=source[['available_at','value','source_state_id']+(['date'] if 'date' in source else [])].copy()
    if 'date' in b:b=b.rename(columns={'date':'source_observation_date'})
    b['available_at']=pd.to_datetime(b.available_at,utc=True)
    b=b.dropna(subset=['value']).sort_values('available_at').drop_duplicates('available_at',keep='last')
    a['cutoff']=a.origin_date.map(origin_cutoff)
    if b.empty:
        a['value']=np.nan;a['source_state_id']=None;a['available_at']=pd.NaT;return a
    joined=pd.merge_asof(a.sort_values('cutoff'),b,left_on='cutoff',right_on='available_at',direction='backward')
    assert (joined.available_at.dropna()<=joined.loc[joined.available_at.notna(),'cutoff']).all()
    if max_age_BD is not None:
        days=pd.to_datetime(joined.loc[joined.available_at.notna(),'source_observation_date']).dt.normalize() if 'source_observation_date' in joined else joined.loc[joined.available_at.notna(),'available_at'].dt.tz_convert('America/New_York').dt.tz_localize(None).dt.normalize()
        origins=pd.to_datetime(joined.loc[joined.available_at.notna(),'origin_date']).dt.normalize()
        age=np.busday_count(days.to_numpy(dtype='datetime64[D]'),origins.to_numpy(dtype='datetime64[D]'))
        expired=joined.available_at.notna().copy();expired.loc[expired]=age>max_age_BD
        joined.loc[expired,'value']=np.nan
    return joined

def weighted_corr(x,y,w,rank=False):
    x=np.asarray(x,float);y=np.asarray(y,float);w=np.asarray(w,float)
    ok=np.isfinite(x)&np.isfinite(y)&np.isfinite(w)&(w>0);x=x[ok];y=y[ok];w=w[ok]
    if len(x)<3 or len(np.unique(x))<2 or len(np.unique(y))<2:return None
    if rank:
        # Weighted mid-CDF ranks prevent repeated cells from changing release-balanced ranks.
        def wrank(v):
            unique=np.unique(v);mass=np.array([w[v==z].sum() for z in unique]);mid=(np.cumsum(mass)-mass/2)/mass.sum()
            return mid[np.searchsorted(unique,v)]
        x=wrank(x);y=wrank(y)
    w=w/w.sum();x=x-np.sum(w*x);y=y-np.sum(w*y)
    d=np.sqrt(np.sum(w*x*x)*np.sum(w*y*y))
    return None if d<=0 else float(np.sum(w*x*y)/d)

def alignment(joined):
    rows=[]
    for name,group in [('all',None),('origin','origin_date'),('release','release_id'),('year','year')]:
        d=joined.dropna(subset=['value']).copy();d['year']=pd.to_datetime(d.origin_date).dt.year
        w=np.ones(len(d)) if group is None else 1/d.groupby(group).value.transform('size').to_numpy()
        if len(d)==0:rows.append({'weighting':name,'cells':0,'origins':0,'agreement':None,'balanced_agreement':None,'Spearman':None});continue
        sign=np.sign(d.value.to_numpy());truth=d.direction.to_numpy();w=w/w.sum()
        agreement=float(np.sum(w*(sign==truth)))
        recalls=[float(np.sum(w[truth==s]*(sign[truth==s]==s))/np.sum(w[truth==s])) for s in (-1,1) if np.sum(w[truth==s])>0]
        rows.append({'weighting':name,'cells':len(d),'origins':d.origin_date.nunique(),'SPD_releases':d.release_id.nunique(),'candidate_states':d.source_state_id.nunique(),'agreement':agreement,'balanced_agreement':float(np.mean(recalls)) if recalls else None,'Spearman':weighted_corr(d.value,d.frozen_prediction,w,True),'zero_source_fraction':float(np.sum(w*(sign==0)))})
    return rows

def persistence(series):
    """Requires contiguous weekday sample; gaps remain missing, never silently filled."""
    s=series.astype(float);s=s.reindex(pd.bdate_range(s.index.min(),s.index.max())) if len(s) else s
    vals=s.dropna();out={'observed_days':len(vals),'grid_days':len(s)}
    for lag in (1,5,21):
        prev=s.shift(lag);ok=s.notna()&prev.notna();out[f'lag_{lag}_pairs']=int(ok.sum());out[f'lag_{lag}_autocorrelation']=weighted_corr(s[ok],prev[ok],np.ones(ok.sum()))
    adjacent=s.notna()&s.shift(1).notna();sign=np.sign(s);same=(sign==sign.shift(1))
    out['unchanged_direction_fraction']=float(same[adjacent].mean()) if adjacent.any() else None
    out['value_change_frequency']=float((s!=s.shift(1))[adjacent].mean()) if adjacent.any() else None
    runs=[];run=0;last=None
    for v in sign:
        if not np.isfinite(v):
            if run:runs.append(run)
            run=0;last=None;continue
        if v==last:run+=1
        else:
            if run:runs.append(run)
            run=1;last=v
    if run:runs.append(run)
    out['average_sign_run_BD']=float(np.mean(runs)) if runs else None
    a=out.get('lag_1_autocorrelation');out['half_life_proxy_BD']=float(np.log(.5)/np.log(a)) if a is not None and 0<a<1 else None
    out['not_predictive_performance']=True
    return out

def redundancy(x,prices):
    """Descriptive projection of SOURCE state on lagged prices, never future error."""
    p=prices.copy();d=pd.concat([x.rename('candidate'),p],axis=1).dropna()
    if len(d)<=len(p.columns)+3 or d.candidate.nunique()<2:return {'n':len(d),'R2':None,'novelty':'UNKNOWN'}
    X=np.column_stack([np.ones(len(d)),d[p.columns].to_numpy(float)]);y=d.candidate.to_numpy(float)
    predicted=X@np.linalg.lstsq(X,y,rcond=None)[0]
    r2=float(1-np.sum((y-predicted)**2)/np.sum((y-y.mean())**2))
    cs={c:weighted_corr(d.candidate,d[c],np.ones(len(d))) for c in p.columns}
    return {'n':len(d),'price_features':len(p.columns),'R2':r2,'novelty':novelty(r2),'correlations':cs,'in_sample_descriptive_only':True,'not_original_price_cache':True}

def novelty(r2):
    if r2 is None:return 'UNKNOWN'
    return 'HIGH' if r2<.4 else 'MEDIUM' if r2<.8 else 'LOW' if r2<.95 else 'REDUNDANT'

def score_and_rank(records):
    """Explicit input projection: unrelated outcome fields cannot affect scores or tie breaks."""
    rows=[]
    for record in records:
        r={k:record[k] for k in ['source','family','PIT','Timing','Novelty','access','rights_status','coverage_pass','relevance_pass','reproducible','primary_prohibited',*SCORE_COLUMNS]}
        assert r['PIT'] in ('A','B','C','D');assert r['Timing'] in ('HIGH','MEDIUM','LOW','UNUSABLE')
        assert all(r[k] in (0,1,2) for k in SCORE_COLUMNS)
        r['score']=sum(r[k] for k in SCORE_COLUMNS)
        r['hard_gates_pass']=bool(r['PIT'] in ('A','B') and r['Timing']!='UNUSABLE' and r['coverage_pass'] and r['relevance_pass'] and r['reproducible'] and not r['primary_prohibited'])
        rows.append(r)
    return sorted(rows,key=lambda r:(-r['score'],r['source']))

def choose(ranked,alignments,price_alignment):
    """No forced forecasting winner. Exactly one audit focus, primary only if substantive gates pass."""
    useful={r['source'] for r in alignments if r['weighting']=='release' and r.get('origins',0)>=24 and (r.get('agreement') or 0)>=.55 and (r.get('Spearman') or 0)>=.1}
    viable=[r for r in ranked if r['hard_gates_pass'] and r['source'] in useful and r['Novelty'] in ('HIGH','MEDIUM')]
    primary=viable[0]['source'] if viable else None
    focus=primary or 'CME_ZQ_POLICY_PATH'
    if primary:
        row=viable[0];result='DIRECT_DIRECTION_SOURCE_FOUND' if row['Timing'] in ('HIGH','MEDIUM') else 'PERSISTENT_REGIME_PROXY';next_axis='DIRECTION-SOURCE-02' if row['Timing'] in ('HIGH','MEDIUM') else 'PERSISTENT-DIRECTION-STATE-02'
    elif (price_alignment.get('agreement') or 0)>=.55 and (price_alignment.get('Spearman') or 0)>=.1:
        # A price explanation alone does not prove exclusivity; inaccessible direct contracts remain unresolved.
        result='DATA_ACCESS_BLOCKED';next_axis='DIRECTION-SOURCE-02-ACQUISITION-GATE'
    else:result='DATA_ACCESS_BLOCKED';next_axis='DIRECTION-SOURCE-02-ACQUISITION-GATE'
    return {'NEWINFO02_RESULT':result,'NEWINFO02_PRIMARY_SOURCE':primary,'audit_focus_source':focus,'primary_count':int(primary is not None),'exactly_one_audit_focus':True,'NEXT':next_axis,'no_forced_winner':primary is None,'ranking_uses_future_outcomes':False}

def bytes_canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def outcome_firewall(records,aligned,price):
    base=bytes_canonical({'rank':score_and_rank(records),'decision':choose(score_and_rank(records),aligned,price)})
    changed=[{**r,'future_return':9999,'realized_truth':-1234,'CRPS':.00001,'oracle_direction':1} for r in records]
    altered=bytes_canonical({'rank':score_and_rank(changed),'decision':choose(score_and_rank(changed),aligned,price)})
    return {'ranking_and_selection_bitwise_identical':base==altered,'SHA256':hashlib.sha256(base).hexdigest(),'mutated_ignored_fields':['future_return','realized_truth','CRPS','oracle_direction'],'not_a_proof_of_provider_vintage_integrity':True}

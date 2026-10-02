"""## Executive summary (read this first)

Build a general five-business-day origin grid using real no-text V5.1 draws.
Store individual outcomes, labels and draws outside the public repository.
"""
import argparse
import hashlib
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import numpy as np
import pandas as pd
from qfbench2_track_forecasting.thesis01.asset_semantics import load_universe, family
from qfbench2_track_forecasting.thesis01.v51_shift import v51_no_text_prior
from qfbench2_track_forecasting.v12.data_parity import _prefix
from qfbench2_track_forecasting.location01.oracle_target import target,oracle_label,HORIZONS
from qfbench2_track_forecasting.location01.feature_metadata import ROUTES
from qfbench2_track_forecasting.location01.feature_own_history import history_state
from qfbench2_track_forecasting.location01.engine import prepare,features

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def dump(path,value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

_WORKER=None

def _init_worker(series,kinds,sigma,checkpoint_dir):
    global _WORKER
    _WORKER=series,kinds,sigma,checkpoint_dir

def _cache_origin(stamp):
    series,kinds,sigma,checkpoint_dir=_WORKER
    origin=pd.Timestamp(stamp);cache=checkpoint_dir/f'{stamp}.npz'
    if cache.exists():
        try:
            with np.load(cache) as data:
                for asset in data.files:
                    if not np.isfinite(data[asset]).all():raise ValueError('Invalid cache')
            return stamp
        except (ValueError,EOFError,OSError):
            cache.unlink()
    saved={}
    for asset in sorted(series):
        if origin not in series[asset].index or not np.isfinite(sigma.loc[origin,asset]):continue
        if not any(target(series[asset],kinds[asset],origin,h) is not None for h in HORIZONS):continue
        group=family(asset,kinds[asset]);n=1000 if group=='Factor/Equity' else 500
        saved[asset]=v51_no_text_prior(series[asset],asset,kinds[asset],list(HORIZONS),ROUTES[group],stamp,19,n)
    temp=cache.with_suffix('.tmp.npz');np.savez_compressed(temp,**saved);temp.replace(cache)
    return stamp

def build(root,private):
    if private.resolve().is_relative_to(root.resolve()):
        raise ValueError('Private ledger must stay outside Git')
    private.mkdir(parents=True,exist_ok=True)
    series,kinds,_=load_universe(root)
    series={a:_prefix(s,str(s.index.max().date())) for a,s in series.items()}
    state=history_state(series,kinds); cross,summaries=prepare(state)
    origins=pd.bdate_range('2001-01-02',max(s.index.max() for s in series.values()))[::5]
    rows=[]; xx=[]; schema=None; chunks=[]; drawbuffer=[]; count=0
    # Per-origin checkpoints can be resumed without changing draws or methods.
    checkpoint_dir=private/'origins'; checkpoint_dir.mkdir(exist_ok=True)
    with ProcessPoolExecutor(max_workers=8,mp_context=multiprocessing.get_context('fork'),
            initializer=_init_worker,initargs=(series,kinds,state['sigma'],checkpoint_dir)) as pool:
        for done,stamp in enumerate(pool.map(_cache_origin,[str(o.date()) for o in origins],chunksize=1),1):
            if done%25==0:print(f'baseline cache {done}/{len(origins)} {stamp}',flush=True)
    for oi,origin in enumerate(origins):
        stamp=str(origin.date()); cache=checkpoint_dir/f'{stamp}.npz'
        if cache.exists():
            cached=np.load(cache,allow_pickle=False)
        else:
            cached=None
        saved={}
        for asset in state['assets']:
            sigma=float(state['sigma'].loc[origin,asset])
            if origin not in series[asset].index or not np.isfinite(sigma):
                continue
            answers=[target(series[asset],kinds[asset],origin,h) for h in HORIZONS]
            if not any(a is not None for a in answers):
                continue
            group=family(asset,kinds[asset]); route=ROUTES[group]
            n=1000 if group=='Factor/Equity' else 500
            draws=(cached[asset] if cached is not None else
                   v51_no_text_prior(series[asset],asset,kinds[asset],list(HORIZONS),
                                     route,stamp,19,n))
            if not np.isfinite(draws).all():
                raise ValueError(f'Nonfinite V5.1 draws: {asset} {stamp}')
            saved[asset]=draws
            anchor=float(series[asset].loc[origin]) if kinds[asset]=='level' else 0.
            for hi,h in enumerate(HORIZONS):
                if answers[hi] is None:
                    continue
                truth,end=answers[hi]; reference=draws[:,hi]
                median,sd,delta=oracle_label(reference,truth)
                scale=max(sigma,1e-8)*np.sqrt(h)
                feat=features(state,cross,summaries,asset,kinds[asset],origin,h,
                              reference,anchor,scale)
                if schema is None:
                    schema=sorted(feat)
                if sorted(feat)!=schema:
                    raise ValueError('Feature schema changed')
                rows.append(dict(origin=stamp,asset=asset,group=group,horizon=h,
                    kind=kinds[asset],target_end=str(end.date()),truth=truth,delta=delta,
                    median=median,sd=sd,scale=scale,n_draws=n,draw_row=count))
                xx.append([feat[c] for c in schema]); count+=1
        if cached is None:
            np.savez_compressed(cache,**saved)
        if cached is not None:
            cached.close()
        if oi%25==0:
            print(f'ledger {oi+1}/{len(origins)} {stamp}: {count} cells',flush=True)
    frame=pd.DataFrame(rows)
    frame.to_parquet(private/'ledger.parquet',index=False)
    np.save(private/'features.npy',np.asarray(xx,float))
    dump(private/'schema.json',schema)
    manifest={'status':'PRE_RESULT_INPUTS','scorer_status':'RESEARCH_PROXY_ONLY',
        'origin_anchor':'2001-01-02','origin_stride_business_days':5,
        'origins':int(frame.origin.nunique()),'cells':len(frame),'assets':state['assets'],
        'date_range':[frame.origin.min(),frame.origin.max()],
        'per_asset_coverage':{a:{'start':str(s.index.min().date()),'end':str(s.index.max().date()),
                               'cells':int((frame.asset==a).sum())} for a,s in series.items()},
        'horizons':list(HORIZONS),'seed':19,'draws':{'FX':500,'Rates':500,'Factor/Equity':1000},
        'target_semantics':'V13-R2 _label: calendar business horizon, next observed endpoint within 3 BDays; no gaps >5 BDays; levels convert changes to forecast levels; return increments sum',
        'eligibility':'observed origin; past-only 252-row sigma with 200 observations; mature R2 target; all eligible cells retained',
        'normalization':'sum CRPS/(past-only 252-row daily innovation SD * sqrt(h)), divided by baseline same sum',
        'floor':1e-8,'ledger_sha256':digest(private/'ledger.parquet'),
        'feature_sha256':digest(private/'features.npy'),'feature_shape':list(np.asarray(xx).shape),
        'schema':list(frame.columns),'feature_schema':schema,
        'baseline_cache_sha256':{p.name:digest(p) for p in sorted(checkpoint_dir.glob('*.npz'))}}
    dump(root/'backtesting/location01/results/ledger_manifest.json',manifest)
    dump(root/'backtesting/location01/results/feature_manifest.json',{
        'schema':schema,'channels':{c:[v for v in schema if v.startswith(c+'_')] for c in 'MFOXR'},
        'own_windows':[1,5,21,63,126,252],'cross_windows':[1,5,21,63],
        'cross_cutoff':'t-1; own entries zero; no same-day-peer diagnostic',
        'regime_windows':[5,21,63],'imputation':'training medians, absent columns zero',
        'numeric_scaler':'StandardScaler fit on training rows only; metadata one-hot unscaled',
        'feature_sha256':manifest['feature_sha256']})
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path.cwd())
    p.add_argument('--private',type=Path,required=True);a=p.parse_args()
    build(a.root,a.private)

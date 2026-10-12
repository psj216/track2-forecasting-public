"""## Executive summary (read this first)
Run unchanged V5.1 first; only replace parquet after a complete validated House transform.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tomllib
import pandas as pd
import numpy as np
from qfbench2_track_forecasting.cli import main as baseline_main
from .engine import request, transform, CONFIG
from .context import build_context

def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    ap=argparse.ArgumentParser(add_help=False)
    ap.add_argument('--out',type=Path);ap.add_argument('--panels',type=Path);ap.add_argument('--text',type=Path);ap.add_argument('--asof');ap.add_argument('--card',type=Path)
    args,_=ap.parse_known_args(argv)
    # The baseline is the exact offline V5.1 path even when the organizer injects House credentials.
    names=['MODEL_ENDPOINT','MODEL_NAME','MODEL_TOKEN','MODEL_API_KEY']
    saved={k:os.environ.pop(k) for k in names if k in os.environ}
    os.environ['FORECAST_MODE']='text-first-v5.1'
    try: code=baseline_main(argv)
    finally: os.environ.update(saved)
    if code or args.out is None:return code
    variant=os.environ.get('M15_VARIANT','A')
    if variant not in CONFIG['variants']:raise SystemExit('invalid frozen M15 variant')
    parent=args.out.parent;meta_path=parent/'forecast_meta.json';rationale=parent/'forecast_rationale.md'
    original=args.out.read_bytes();receipt={'candidate_id':'M15-'+variant,'baseline_parquet_SHA256':hashlib.sha256(original).hexdigest(),'applied':False,'requests_attempted':0,'no_retry':True,'fallback':'EXACT_V51_FORECAST_PARQUET'}
    try:
        frame=pd.read_parquet(args.out);meta=json.loads(meta_path.read_text())
        assets=meta['asset_ids'];horizons=meta['horizons'];n=meta['n_draws']
        # The frozen producer's long rows are draw/asset/horizon in declared order.
        ordered=pd.MultiIndex.from_product([range(n),assets,horizons],names=['draw','asset','horizon'])
        indexed=frame.set_index(['draw','asset','horizon'])
        if not indexed.index.is_unique or set(indexed.index)!=set(ordered): raise ValueError('baseline_grid')
        base=indexed.loc[ordered,'value'].to_numpy().reshape(n,len(assets),len(horizons))
        card_path=args.card or next(p for p in [args.panels/'card.toml',args.panels.parent/'card.toml'] if p.is_file())
        card=tomllib.loads(card_path.read_text())
        context=build_context(card,args.panels,args.text,args.asof,assets,horizons,base)
        if not all(os.environ.get(k) for k in ['MODEL_ENDPOINT','MODEL_NAME','MODEL_TOKEN','http_proxy']):raise ValueError('missing_house_configuration')
        receipt['context_SHA256']=hashlib.sha256(json.dumps(context,sort_keys=True,allow_nan=False).encode()).hexdigest()
        receipt['documents_used']=[{'id':d['id'],'timestamp':d['timestamp']} for d in context['dated_text']]
        if variant=='E':
            receipt['requests_attempted']=1
            first=request('E1',context)
            context['stage1_uncertain_assessment']=first
            receipt['requests_attempted']=2
            reply=request('E2',context)
        else:
            receipt['requests_attempted']=1;reply=request(variant,context)
        adjusted,geometry=transform(base,variant,reply,assets,horizons)
        values=pd.Series(adjusted.ravel(),index=ordered)
        result=frame.copy();result['value']=[float(values.loc[(int(row.draw),row.asset,int(row.horizon))]) for row in frame.itertuples()]
        temp=parent/'moonshot15.pending.parquet';result.to_parquet(temp,index=False)
        if not np.array_equal(pd.read_parquet(temp)['value'].to_numpy(),result['value'].to_numpy()):raise ValueError('serialization')
        temp.replace(args.out)
        receipt.update({'applied':True,'fallback':None,'geometry':geometry})
    except Exception as exc:
        # Never emit exception messages: HTTP/proxy exceptions may contain credentials.
        receipt['failure_type']=type(exc).__name__
        if args.out.read_bytes()!=original:args.out.write_bytes(original)
        if (parent/'moonshot15.pending.parquet').exists():(parent/'moonshot15.pending.parquet').unlink()
    meta=json.loads(meta_path.read_text());meta['moonshot15']=receipt
    meta['reasoning_applied']=bool(receipt['applied']) or bool(meta.get('reasoning_applied',False))
    if receipt['applied']:meta['forecast_adjustment_applied']=True
    meta_path.write_text(json.dumps(meta,indent=2,sort_keys=True,allow_nan=False)+'\n')
    rationale.write_text(rationale.read_text()+ '\n## M15 House candidate\n\n'+json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print('M15 '+variant+' applied='+str(receipt['applied'])+' calls='+str(receipt['requests_attempted']))
    return 0
if __name__=='__main__':raise SystemExit(main())

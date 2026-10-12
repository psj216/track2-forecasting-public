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
from .official_transport import HouseError, new_call_receipt
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
    original=args.out.read_bytes();receipt={'candidate_id':'M15-'+variant,'baseline_parquet_SHA256':hashlib.sha256(original).hexdigest(),'applied':False,'requests_attempted':0,'no_retry':True,'fallback':'EXACT_V51_FORECAST_PARQUET','runtime_revision':'M16_TRANSPORT_REPAIR','requests':[],'request_attempted':False,'request_sent':False,'response_received':False,'response_validated':False,'adjustment_applied':False,'fallback_used':True,'failure_category':None,'location_shift_statistics':None}
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
        receipt['context_SHA256']=hashlib.sha256(json.dumps(context,sort_keys=True,allow_nan=False).encode()).hexdigest()
        receipt['documents_used']=[{'id':d['id'],'timestamp':d['timestamp']} for d in context['dated_text']]
        if variant=='E':
            receipt['requests_attempted']=1
            call=new_call_receipt();receipt['requests'].append(call)
            first=request('E1',context,call)
            context['stage1_uncertain_assessment']=first
            receipt['requests_attempted']=2
            call=new_call_receipt();receipt['requests'].append(call)
            reply=request('E2',context,call)
        else:
            receipt['requests_attempted']=1
            call=new_call_receipt();receipt['requests'].append(call)
            reply=request(variant,context,call)
        adjusted,geometry=transform(base,variant,reply,assets,horizons)
        values=pd.Series(adjusted.ravel(),index=ordered)
        result=frame.copy();result['value']=[float(values.loc[(int(row.draw),row.asset,int(row.horizon))]) for row in frame.itertuples()]
        temp=parent/'moonshot15.pending.parquet';result.to_parquet(temp,index=False)
        if not np.array_equal(pd.read_parquet(temp)['value'].to_numpy(),result['value'].to_numpy()):raise ValueError('serialization')
        temp.replace(args.out)
        receipt.update({'applied':True,'fallback':None,'geometry':geometry,'adjustment_applied':not np.array_equal(adjusted,base),'fallback_used':False,'location_shift_statistics':geometry})
    except Exception as exc:
        # Never emit exception messages: HTTP/proxy exceptions may contain credentials.
        receipt['failure_type']=type(exc).__name__
        receipt['failure_category']=exc.category if isinstance(exc,HouseError) else ('timeout' if isinstance(exc,TimeoutError) else 'runtime_failure')
        if args.out.read_bytes()!=original:args.out.write_bytes(original)
        if (parent/'moonshot15.pending.parquet').exists():(parent/'moonshot15.pending.parquet').unlink()
    calls=receipt['requests']
    receipt['request_attempted']=any(c['request_attempted'] for c in calls)
    receipt['request_sent']=True if any(c['request_sent'] is True for c in calls) else ('unknown' if any(c['request_sent']=='unknown' for c in calls) else False)
    receipt['response_received']=any(c['response_received'] for c in calls)
    receipt['response_validated']=bool(calls) and all(c['response_validated'] for c in calls)
    meta=json.loads(meta_path.read_text());meta['moonshot15']=receipt
    meta['reasoning_applied']=bool(receipt['applied']) or bool(meta.get('reasoning_applied',False))
    if receipt['applied']:meta['forecast_adjustment_applied']=True
    meta_path.write_text(json.dumps(meta,indent=2,sort_keys=True,allow_nan=False)+'\n')
    rationale.write_text(rationale.read_text()+ '\n## M15 House candidate\n\n'+json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print('M15 '+variant+' applied='+str(receipt['applied'])+' calls='+str(receipt['requests_attempted']))
    return 0
if __name__=='__main__':raise SystemExit(main())

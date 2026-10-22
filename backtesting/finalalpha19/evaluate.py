"""Executive summary: label-side evaluation using imported official losses and M0 scales.

Forecast construction lives in a separate module without label reads. No outcomes are exported.
"""
import argparse
import hashlib
import json
import pathlib
import tomllib
import numpy as np
import pandas as pd
from m0 import reconstruct, scales, hedge
from qfbench2_track_forecasting.scoring import _composite
from qfbench2_track_forecasting.grid import grid_from_card


def digest(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def matrix(path,cells):
    df=pd.read_parquet(path)
    assert not df.duplicated(['draw','asset','horizon']).any()
    x=df.pivot(index='draw',columns=['asset','horizon'],values='value').reindex(columns=cells).to_numpy()
    assert len(df)==x.size and np.isfinite(x).all()
    return x


def metrics(x,y,scale):
    weights=(5/7,0,2/7) if x.shape[1]==1 else (.5,.3,.2)
    raw=_composite(x,y,weights=weights,tail_levels=(.01,.05,.95,.99),joint='variogram',tail_metric='pinball',ref_scale=scale)
    return dict(raw=raw,normalized={k:raw[k]/scale[k] for k in ('marginal','joint','tail')},score=min(8.,raw['composite']),
        coverage90=float(np.mean((y>=np.quantile(x,.05,axis=0))&(y<=np.quantile(x,.95,axis=0)))),
        coverage98=float(np.mean((y>=np.quantile(x,.01,axis=0))&(y<=np.quantile(x,.99,axis=0)))))


def summary(rows):
    out={'cards':len(rows),'origins':len(set(r['origin'] for r in rows))}
    for name in ['ff03','candidate','m0']:
        if rows and name in rows[0]:
            out[name]={'score':float(np.mean([r[name]['score'] for r in rows])),
              'normalized':{k:float(np.mean([r[name]['normalized'][k] for r in rows])) for k in ['marginal','joint','tail']},
              'coverage90':float(np.mean([r[name]['coverage90'] for r in rows])),'coverage98':float(np.mean([r[name]['coverage98'] for r in rows]))}
    if 'candidate' in out:
        out['improvement']=out['ff03']['score']-out['candidate']['score']
        out['relative_improvement']=out['improvement']/out['ff03']['score']
    return out


def evaluate_one(unit,forecast,label,baseline_only=False):
    card=tomllib.loads((unit/'card.toml').read_text());spec=grid_from_card(card);cells=spec.cells()
    d=reconstruct(unit);scale=scales(d.mean,d.covariance);a=matrix(forecast,cells)
    # Candidate constructed before labels are opened; source draws selected in whole rows.
    b,trace=(None,None) if baseline_only else hedge(unit,a)
    label_df=pd.read_parquet(label)
    indexed=label_df.set_index(['asset','horizon'])
    if indexed.index.duplicated().any() or not all(c in indexed.index for c in cells):
        return {'id':unit.name,'status':'MISSING_LABEL_GRID','forecast_success':True}
    y=np.array([float(indexed.loc[c,'value']) for c in cells]);assert np.isfinite(y).all()
    meta=json.loads(forecast.with_name('forecast_meta.json').read_text())
    r=dict(id=unit.name,origin=card['provenance']['data_cutoff'],family=card['metadata']['category'],
       assets=list(spec.assets),horizons=list(spec.horizons),cells=len(cells),
       market=('UST' if all(a.startswith('UST_') for a in spec.assets) else 'ECB_EM' if 'em_fx_ecb_daily' in card.get('panels',{}).get('panel_ids',[]) else 'G10'),
       text_active=bool(meta.get('forecast_adjustment_applied') or meta.get('reasoning_applied')),
       scales=scale,ff03=metrics(a,y,scale),m0=metrics(d.samples,y,scale),forecast_sha256=digest(forecast),label_sha256=digest(label),status='SCORED')
    if not baseline_only:
        r['candidate']=metrics(b,y,scale);r['applied']=trace['applied'];r['fallback_reason']=trace.get('reason')
        r['candidate_array_sha256']=hashlib.sha256(b.tobytes()).hexdigest()
        r['row_selection_sha256']=hashlib.sha256(json.dumps(trace,sort_keys=True).encode()).hexdigest()
        assert np.array_equal(b,hedge(unit,a)[0])
        r['sampling_sensitivity']={str(seed):metrics(hedge(unit,a,selection_salt=seed)[0],y,scale)['score'] for seed in [18,19]}
        r['cell_change_count']=int(np.count_nonzero(a!=b))
        r['subsets']={}
        for key,indices in [(f'asset:{asset}',[i for i,c in enumerate(cells) if c[0]==asset]) for asset in spec.assets]+[(f'horizon:{h}',[i for i,c in enumerate(cells) if c[1]==h]) for h in spec.horizons]:
            subscale=scales(d.mean[indices],d.covariance[np.ix_(indices,indices)])
            r['subsets'][key]={'ff03':metrics(a[:,indices],y[indices],subscale),'candidate':metrics(b[:,indices],y[indices],subscale)}
    return r


def main():
    p=argparse.ArgumentParser();p.add_argument('--official',type=pathlib.Path,required=True);p.add_argument('--receipts',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--baseline-only',action='store_true');args=p.parse_args()
    rows=[]
    for receipt in sorted(args.receipts.glob('*/*/ff03/receipt.json')):
        name=receipt.parent.parent.name
        row=evaluate_one(args.official/'units'/name,receipt.parent/'output/forecast.parquet',args.official/'practice-answers'/(name+'.parquet'),args.baseline_only)
        rows.append(row)
    assert len(rows)==22 and all(r['status']=='SCORED' for r in rows)
    result={'executive_summary':'Local reconstructed official-formula normalized exposed practice; not authenticated leaderboard scores. Lower is better.',
        'exposure':'EXPOSED_PRACTICE','summary':summary(rows),'cards':rows}
    args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))

if __name__=='__main__':main()

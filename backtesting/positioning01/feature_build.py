"""## Executive summary (read this first)
Freeze offline source matrices, age guards and all report controls without reading targets.
"""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from qfbench2_track_forecasting.positioning01.publication_alignment import latest,age
from qfbench2_track_forecasting.positioning01.flow_features import enrich as flow_enrich
from qfbench2_track_forecasting.positioning01.liquidity_features import enrich as liquidity_enrich
from qfbench2_track_forecasting.positioning01.source_asset_map import FLOW_ASSET,LIQUIDITY_ASSETS
from .negative_controls import donor_index
from .align_location_ledger import dump,digest
HORIZONS=(5,21,63,126,189)
NAMES={'F':('flow_usd_trillion','one_release_change','net_over_gross_transactions','past_z','four_release_cumulative','publication_age','observation_age'),'L':('reserve_usd_trillion','one_release_change','four_release_change','thirteen_release_change','past_z','publication_age','observation_age')}
def schema():
    columns=[]
    for c in ('F','L'):
        columns.extend(dict(name=c+'_'+name,class_id=c,stage=1) for name in NAMES[c])
    base=columns.copy()
    for h in HORIZONS:columns.extend(dict(**{**s,'name':s['name']+'_h'+str(h),'stage':2,'horizon':h})for s in base)
    return columns

def build(private,location):
    releases=json.loads((private/'processed_releases.json').read_text());r={'F':flow_enrich(releases['F']),'L':liquidity_enrich(releases['L'])}
    rows=pd.read_parquet(location/'ledger.parquet',columns=['origin','asset','group','horizon']);cols=schema();mat={k:np.zeros((len(rows),len(cols)))for k in ('primary','A','B')};info={};events={x['event_id']:x['release_date'] for c in r.values()for x in c}
    # Information-cutoff and fixed Mon-Fri calendar exactly match inherited LOCATION.
    for origin,sub in rows.groupby('origin',sort=True):
        o=str(origin);info[o]={}
        for c in ('F','L'):
            maximum=30 if c=='F' else 10
            actual=latest(r[c],o,maximum)
            if actual is None:continue
            index=next(i for i,x in enumerate(r[c])if x['event_id']==actual['event_id']);info[o][c]=dict(event_id=actual['event_id'],release_date=actual['release_date'],observation_date=actual['observation_date'],age=age(actual['release_date'],o))
            eligible=sub.index[sub.asset==FLOW_ASSET].to_numpy() if c=='F' else sub.index[sub.asset.isin(LIQUIDITY_ASSETS)].to_numpy()
            for k in mat:
                j=index if k=='primary' else donor_index(index,k)
                if j is None:continue
                chosen=r[c][j]
                if k=='B' and age(chosen['release_date'],o)>maximum:continue
                # A permutes past content but keeps true publication/observation age,
                # isolating information content; B is a genuinely older available report.
                age_record=actual if k=='A' else chosen
                v=np.array(chosen['features']+[age(age_record['release_date'],o)/(30 if c=='F' else 10),age(age_record['observation_date'],o)/63])
                baseix=[i for i,s in enumerate(cols)if s['class_id']==c and s['stage']==1];mat[k][np.ix_(eligible,baseix)]=v
                for h in HORIZONS:
                    ix=eligible[rows.loc[eligible,'horizon'].to_numpy()==h];dest=[i for i,s in enumerate(cols)if s['class_id']==c and s.get('horizon')==h];mat[k][np.ix_(ix,dest)]=v
    files={}
    for name,x in mat.items():
        np.save(private/f'features_{name}.npy',x);files[name]=digest(private/f'features_{name}.npy')
    dump(private/'schema.json',dict(columns=cols));dump(private/'origin_reports.json',dict(origins=info,event_dates=events));dump(private/'enriched_releases.json',dict(**r))
    out=Path('backtesting/positioning01/results');dump(out/'feature_manifest.json',dict(features=files,processed_sha256=digest(private/'processed_releases.json'),schema_sha256=digest(private/'schema.json'),origin_reports_sha256=digest(private/'origin_reports.json'),columns=cols,rows=len(rows),absent_classes=['P'],no_target_columns_read=True))
    evaluation=pd.to_datetime(rows.origin).dt.year.between(2010,2024).to_numpy();cov={}
    for name,c in [('P',[]),('F',['F']),('L',['L']),('C',['F','L'])]:
        ix=[i for i,s in enumerate(cols)if s['class_id'] in c and s['stage']==1];active=np.any(mat['primary'][:,ix]!=0,axis=1)&evaluation if ix else np.zeros(len(rows),bool);origins=sorted(rows.loc[active,'origin'].unique());eventids={info[str(o)][cc]['event_id'] for o in origins for cc in c if cc in info[str(o)] and (cc!='F' or name=='F' or rows.loc[(rows.origin==o)&active,'asset'].eq(FLOW_ASSET).any())}
        cov[name]=dict(active_cells=int(active.sum()),full_cells=int(evaluation.sum()),coverage_fraction=float(active.sum()/evaluation.sum()),active_origins=len(origins),unique_reports=len(eventids),years=sorted(pd.to_datetime(rows.loc[active,'origin']).dt.year.unique().tolist()),available_test_eras=sum(any(a<=y<=b for y in pd.to_datetime(rows.loc[active,'origin']).dt.year.unique())for a,b in [(2010,2013),(2014,2017),(2018,2020),(2021,2024)]),source_instruments=len(c),categories=len(c))
    dump(out/'coverage_summary.json',dict(classes=cov,source_releases={c:len(v)for c,v in r.items()},ledger_cells=len(rows),full_evaluation_cells=int(evaluation.sum()),full_evaluation_origins=int(rows.loc[evaluation,'origin'].nunique()),assets=int(rows.asset.nunique()),publication_day_excluded=True));print(json.dumps(cov),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private',type=Path,required=True);p.add_argument('--location',type=Path,required=True);a=p.parse_args();build(a.private,a.location)

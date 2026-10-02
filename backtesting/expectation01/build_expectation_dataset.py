"""## Executive summary (read this first)

Align real source values to original origins and build fixed metadata interactions.
"""
import argparse,json,time
from pathlib import Path
import numpy as np,pandas as pd
from qfbench2_track_forecasting.expectation01.source_schema import FAMILIES
from qfbench2_track_forecasting.expectation01.expectation_features import E_NAMES,V_NAMES,expectation_at
from qfbench2_track_forecasting.expectation01.surprise_features import build_events,surprise_at
from .negative_controls import CONTROLS,controlled_events
from .align_location_ledger import dump,digest,verify

BASE=E_NAMES+["S_RGDP_1","S_RGDP_5","S_RGDP_21"]

def schema_for(rows):
    schema=[dict(name=n,stage=1,family=n.split("_")[1]) for n in BASE]
    for stage,key in [(2,"horizon"),(3,"group"),(4,"asset")]:
        for value in sorted(rows[key].unique()):
            schema.extend(dict(name=f"{n}__{key}={value}",stage=stage,family=n.split("_")[1],metadata=key,value=str(value)) for n in BASE)
    schema.extend(dict(name=n,stage=5,family=n.split("_")[1]) for n in V_NAMES)
    return schema

def build_matrix(rows,snapshots,events,schema,control=None):
    date_data={};origin_ids={};families={};surprise_ids={};start=time.monotonic()
    ev=controlled_events(events,control,snapshots) if control else events
    origins=sorted(rows.origin.unique())
    for j,origin in enumerate(origins):
        e,v,eids=expectation_at(snapshots,origin,older=control=="C_older_snapshot");s,sids=surprise_at(ev,origin)
        date_data[origin]=np.r_[e,s,v];origin_ids[origin]=eids+sids;surprise_ids[origin]=sids
        families[origin]=[f for k,f in enumerate(FAMILIES) if np.any(e[k*5:(k+1)*5]!=0) or (f=="RGDP" and np.any(s!=0))]
        if j%250==0:print(json.dumps(dict(stage="source alignment",completed=j,total=len(origins),elapsed=round(time.monotonic()-start,1),origin=origin,control=control)),flush=True)
    lookup={n:i for i,n in enumerate(BASE+V_NAMES)};base=np.array([date_data[d] for d in rows.origin],dtype=np.float32)
    x=np.empty((len(rows),len(schema)),np.float32)
    for j,col in enumerate(schema):
        n=col["name"].split("__")[0];x[:,j]=base[:,lookup[n]]
        if "metadata" in col:x[:,j]*=(rows[col["metadata"]].astype(str)==col["value"]).to_numpy()
    return x,origin_ids,families,surprise_ids

def run(root,private,location):
    verified=verify(location);rows=pd.read_parquet(location/"ledger.parquet");snaps=json.loads((private/"survey_snapshots.json").read_text());actual=json.loads((private/"first_actuals.json").read_text());events=build_events(snaps,actual)
    dump(private/"events.json",dict(events=events));schema=schema_for(rows)
    dump(private/"schema.json",dict(columns=schema))
    for name in ["primary",*CONTROLS]:
        x,ids,families,sids=build_matrix(rows,snaps,events,schema,None if name=="primary" else name);np.save(private/f"features_{name}.npy",x)
        if name=="primary":
            dump(private/"origin_events.json",dict(origin_events=ids,origin_families=families,surprise_events=sids))
            active=np.any(x!=0,axis=1);evmask=pd.to_datetime(rows.origin).dt.year>=2010;selected=rows[evmask];used={eid for d in selected.origin.unique() for eid in ids[d]}
            coverage=dict(full_cells=len(selected),active_cells=int((active&evmask).sum()),full_origins=int(selected.origin.nunique()),active_origins=int(rows[active&evmask].origin.nunique()),coverage_fraction=float((active&evmask).sum()/evmask.sum()),events=len(used),event_ids_count_by_type={"survey":sum(e.startswith("SPF") for e in used),"true_surprise":sum(e.startswith("GDP") for e in used)},years=int(pd.to_datetime(rows[active&evmask].origin).dt.year.nunique()),fold_active_origins=[int(rows[active&(pd.to_datetime(rows.origin).dt.year.between(a,b))].origin.nunique()) for a,b in [(2010,2013),(2014,2017),(2018,2020),(2021,2024)]])
            dump(root/"backtesting/expectation01/results/coverage_summary.json",coverage)
    out=root/"backtesting/expectation01/results"
    dump(out/"feature_manifest.json",dict(columns=schema,column_count=len(schema),row_count=len(rows),features={name:digest(private/f"features_{name}.npy") for name in ["primary",*CONTROLS]},schema_sha256=digest(private/"schema.json"),source_snapshots_sha256=digest(private/"survey_snapshots.json"),first_actuals_sha256=digest(private/"first_actuals.json"),events_sha256=digest(private/"events.json"),origin_events_sha256=digest(private/"origin_events.json"),frozen_location_inputs=verified))
    dump(out/"event_manifest.json",dict(survey_publications=108,survey_values=len(snaps),first_actual_events=len(events),standardized_events=sum(e["z"] is not None for e in events),cold_start_events=sum(e["z"] is None for e in events),sign="first actual minus last genuine same-target prerelease survey",units="annualized quarter-on-quarter GDP percentage points",normalization="expanding strictly prior same-family sample SD; minimum 24 events",event_detail_private=True))
    print(json.dumps(coverage),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path.cwd());p.add_argument("--private",type=Path,required=True);p.add_argument("--location",type=Path,required=True);a=p.parse_args();run(a.root,a.private,a.location)

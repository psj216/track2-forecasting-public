"""## Executive summary (read this first)

Score original draws through common fair CRPS, saving bounded origin chunks.
"""
import argparse,json,time,subprocess
from pathlib import Path
import numpy as np,pandas as pd
from qfbench2_common.scoring.crps import crps_ensemble
from qfbench2_track_forecasting.positioning01.engine import shift,geometry_guard
from qfbench2_track_forecasting.location01.oracle_target import HORIZONS
from .chronological_crossfit import KEYS
from .align_location_ledger import dump,digest

ALL_KEYS=["P0",*KEYS]

def load_predictions(private,rows):
    pred={"P0":np.zeros(len(rows))};audits={}
    for key in KEYS:
        pred[key]=np.zeros(len(rows));audits[key]=[]
        for fold in range(1,5):
            file=private/"crossfit"/f"fold{fold}_{key}.npz";audit=json.loads(file.with_suffix(".json").read_text())
            if digest(file)!=audit["prediction_sha256"]:raise ValueError("Prediction artifact changed")
            with np.load(file) as z:pred[key][z["row_index"]]=z["prediction"]
            audits[key].append(audit)
    return pred,audits

def score(private,location,start,stop,pre_sha):
    if subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()!=pre_sha:raise ValueError("Unfrozen HEAD")
    path=private/"score_chunks"/f"origins_{start:04d}_{stop:04d}.npz";meta=path.with_suffix(".json")
    if path.exists() and meta.exists():print("SAVED "+str(path),flush=True);return
    rows=pd.read_parquet(location/"ledger.parquet");pred,audits=load_predictions(private,rows);origins=sorted(rows.loc[pd.to_datetime(rows.origin).dt.year>=2010,"origin"].unique());chosen=origins[start:stop];indices=np.flatnonzero(rows.origin.isin(chosen));dest={int(v):i for i,v in enumerate(indices)};loss=np.zeros((len(ALL_KEYS),len(indices)));beg=time.monotonic();guards=0
    inherited=np.load(location/"losses.npz");oldmap={int(v):i for i,v in enumerate(inherited["row_index"])}
    for count,origin in enumerate(chosen):
        with np.load(location/"origins"/f"{origin}.npz") as archive:
            for asset,group in rows[rows.origin==origin].groupby("asset"):
                ix=group.index.to_numpy();cols=[HORIZONS.index(int(h)) for h in group.horizon];draws=archive[asset][:,cols].astype(float);truth=group.truth.to_numpy();sd=group.sd.to_numpy();scale=group.scale.to_numpy();p=np.array([pred[k][ix] for k in ALL_KEYS])
                before=np.tile(draws,(1,len(ALL_KEYS)));after=shift(draws[:,None,:],p[None,:,:],sd[None,None,:]).reshape(len(draws),-1)
                if not geometry_guard(before,after):raise ValueError("Pure location geometry changed")
                scored=crps_ensemble(after,np.tile(truth,len(ALL_KEYS))).reshape(len(ALL_KEYS),len(ix))/scale
                old=np.array([inherited["baseline"][oldmap[int(v)]] for v in ix]);np.testing.assert_allclose(scored[0],old,rtol=1e-12,atol=1e-12)
                scored=np.where(p==0,old[None,:],scored);loss[:,[dest[int(v)] for v in ix]]=scored;guards+=1
        if (count+1)%20==0:print(json.dumps(dict(stage="marginal scoring",completed=count+1,total=len(chosen),elapsed=round(time.monotonic()-beg,1),origin=origin,artifact=str(path))),flush=True)
    path.parent.mkdir(exist_ok=True);np.savez_compressed(path,row_index=indices,loss=loss);dump(meta,dict(pre_result_sha=pre_sha,origins=len(chosen),cells=len(indices),models=ALL_KEYS,geometry_checks=guards,baseline_exact_reproduction=True,sha256=digest(path)));print("SAVED "+str(path),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--private",type=Path,required=True);p.add_argument("--location",type=Path,required=True);p.add_argument("--start",type=int,required=True);p.add_argument("--stop",type=int,required=True);p.add_argument("--pre-result-sha",required=True);a=p.parse_args();score(a.private,a.location,a.start,a.stop,a.pre_result_sha)

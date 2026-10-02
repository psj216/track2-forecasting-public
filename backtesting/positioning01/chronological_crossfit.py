"""## Executive summary (read this first)

Save each fixed fold/model prediction immediately and refuse unfrozen execution.
"""
import argparse,json,time,pickle,subprocess,threading
from pathlib import Path
import numpy as np,pandas as pd
from qfbench2_track_forecasting.positioning01.model import QuantityModel,choose_alpha,FOLDS,purged_mask
from .align_location_ledger import dump,digest
from .negative_controls import CONTROLS

KEYS=['F1','F2','L1','L2','C1','C2','nonlinear',*CONTROLS]
def model_for_key(key):
    if key not in KEYS:raise ValueError('Not a precommitted model')
    return 1 if key in ('F1','L1','C1') else 2

def track_for_key(key):return 'C' if key=='nonlinear' else key[0]

def run(private,location,fold,key,pre_sha):
    if key not in KEYS:raise ValueError("Not a precommitted model")
    path=private/"crossfit"/f"fold{fold}_{key}.npz";auditpath=path.with_suffix(".json")
    if path.exists() and auditpath.exists():print("SAVED CHECKPOINT "+str(path),flush=True);return
    head=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    if head!=pre_sha:raise ValueError("HEAD is not verified frozen PRE_RESULT")
    manifest=json.loads(Path("backtesting/positioning01/results/feature_manifest.json").read_text());name=key[1] if key in CONTROLS else "primary";file=private/f"features_{name}.npy"
    if digest(file)!=manifest["features"][name]:raise ValueError("Feature hash changed")
    rows=pd.read_parquet(location/"ledger.parquet");x=np.load(file,mmap_mode="r");schema=json.loads((private/"schema.json").read_text())["columns"]
    model=model_for_key(key)
    track=track_for_key(key);selected=[i for i,c in enumerate(schema) if track=='C' or c['class_id']==track];x=x[:,selected];schema=[schema[i] for i in selected]
    cutoff,start,end=FOLDS[fold-1];years=pd.to_datetime(rows.origin).dt.year;train=purged_mask(rows,f"{start}-01-01");test=years.between(start,end).to_numpy();y=rows.delta.to_numpy();beg=time.monotonic()
    finished=threading.Event()
    def heartbeat():
        while not finished.wait(60):print(json.dumps(dict(stage="crossfit heartbeat",fold=fold,model=key,elapsed=round(time.monotonic()-beg,1),artifact=str(path))),flush=True)
    threading.Thread(target=heartbeat,daemon=True).start()
    print(json.dumps(dict(stage="fit",fold=fold,model=key,train=int(train.sum()),test=int(test.sum()),artifact=str(path))),flush=True)
    alpha,cv=(100.,dict(status="FIXED_NONLINEAR")) if key=="nonlinear" else choose_alpha(x[train],y[train],schema,rows.loc[train].reset_index(drop=True),model,cutoff)
    print(json.dumps(dict(stage="inner CV complete",fold=fold,model=key,alpha=alpha,elapsed=round(time.monotonic()-beg,1))),flush=True)
    fitted=QuantityModel(model,key=="nonlinear").fit(x[train],y[train],schema,alpha);raw=fitted.predict_raw(x[test]);prediction=np.clip(raw,-10,10);path.parent.mkdir(exist_ok=True);np.savez_compressed(path,row_index=np.flatnonzero(test),prediction=prediction,raw_prediction=raw)
    with open(path.with_suffix(".pkl"),"wb") as f:pickle.dump(fitted,f)
    audit=dict(pre_result_sha=pre_sha,fold=fold,key=key,cutoff_year=cutoff,train_cells=int(train.sum()),test_cells=int(test.sum()),alpha=alpha,inner_cv=cv,fit_intercept=False,train_scaling="StandardScaler with_mean=False fitted only on active training",train_max_origin=str(rows.loc[train,"origin"].max()),train_max_target_end=str(rows.loc[train,"target_end"].max()),test_min_origin=str(rows.loc[test,"origin"].min()),cap_count=int((abs(raw)>10).sum()),elapsed_seconds=time.monotonic()-beg,prediction_sha256=digest(path))
    finished.set();dump(auditpath,audit);dump(private/"STATUS.json",dict(branch="track2/positioning-01-public-positioning-flow-liquidity",HEAD_SHA=head,current_stage="crossfit",completed_stages=["environment","source_gates","features","tests","pre_result_remote_verified"],pending_stages=["remaining_folds","scoring","aggregate_bootstrap","report","result_remote_verified","preservation"],last_successful_artifact=str(path),updated_at=pd.Timestamp.now(tz="UTC").isoformat(),fold=fold,model=key,pre_result_sha=pre_sha));print(json.dumps(audit),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--private",type=Path,required=True);p.add_argument("--location",type=Path,required=True);p.add_argument("--fold",type=int,required=True);p.add_argument("--key",required=True);p.add_argument("--pre-result-sha",required=True);a=p.parse_args();run(a.private,a.location,a.fold,a.key,a.pre_result_sha)

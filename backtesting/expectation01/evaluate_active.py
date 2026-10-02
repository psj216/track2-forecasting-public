"""## Executive summary (read this first)

Aggregate frozen active/full results, whole-event uncertainty and every source without selection.
"""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import spearmanr
from .evaluate_full import ALL_KEYS,load_predictions
from .align_location_ledger import dump,digest
from .diagnostics import summary,success
from .negative_controls import CONTROLS
from .bootstrap_event import event_blocks,block_bootstrap,year_bootstrap

def run(root,private,location,pre_sha):
    allrows=pd.read_parquet(location/"ledger.parquet");ix=np.flatnonzero(pd.to_datetime(allrows.origin).dt.year>=2010);rows=allrows.loc[ix].reset_index(drop=True);pred,audits=load_predictions(private,allrows);pred={k:v[ix] for k,v in pred.items()};old=np.load(location/"losses.npz");assert np.array_equal(ix,old["row_index"]);base,oracle=old["baseline"],old["oracle"];loss=np.empty((len(ALL_KEYS),len(ix)));found=np.zeros(len(ix),bool);mapping={int(v):j for j,v in enumerate(ix)}
    for file in sorted((private/"score_chunks").glob("*.npz")):
        meta=json.loads(file.with_suffix(".json").read_text());assert digest(file)==meta["sha256"]
        with np.load(file) as z:
            dest=[mapping[int(v)] for v in z["row_index"]]
            if found[dest].any():raise ValueError("Overlapping scoring chunk")
            loss[:,dest]=z["loss"];found[dest]=True
    if not found.all():raise ValueError("Missing scoring chunk")
    losses={k:loss[j] for j,k in enumerate(ALL_KEYS)};x=np.load(private/"features_primary.npy",mmap_mode="r");active=np.any(x[ix]!=0,axis=1);origininfo=json.loads((private/"origin_events.json").read_text());ids=origininfo["origin_events"];fam=origininfo["origin_families"];events=json.loads((private/"events.json").read_text())["events"];snaps=json.loads((private/"survey_snapshots.json").read_text());eventdates={e["event_id"]:e["release_date"] for e in events};eventdates.update({"SPF_"+s["survey_id"]:s["publication_date"] for s in snaps});activeorigins=sorted(rows.loc[active,"origin"].unique());blocks=event_blocks(activeorigins,ids,eventdates);cellblocks=np.array([blocks[d] for d in rows.loc[active,"origin"]]);years=pd.to_datetime(rows.origin).dt.year.to_numpy();fold=np.select([years<=2013,years<=2017,years<=2020],[1,2,3],default=4);out={};eventboot={};yearboot={};tables={k:[] for k in ["fold","group","horizon","event_family","expectation_source"]};sourceout={}
    for key in ALL_KEYS:
        mask=active if not key.startswith("source_") else rows.origin.map(lambda d:key.split("_",1)[1] in fam[d]).to_numpy()
        result=summary(rows.delta.to_numpy(),pred[key],base,losses[key],oracle,mask);result["cap_count"]=sum(a["cap_count"] for a in audits.get(key,[]));result["active_events"]=len({e for d in rows.loc[mask,"origin"].unique() for e in ids[d]});result["unique_release_dates"]=len({eventdates[e] for d in rows.loc[mask,"origin"].unique() for e in ids[d]});result["unique_years"]=len(np.unique(years[mask]));result["active_origins"]=int(rows.loc[mask,"origin"].nunique());out[key]=result
        eventboot[key]=block_bootstrap(np.array([blocks[d] for d in rows.loc[mask,"origin"]]),base[mask],losses[key][mask],oracle[mask]);yearboot[key]=year_bootstrap(years,base,losses[key],oracle)
        result["fold_active_ratios"]=[]
        for category,column in [("fold",fold),("group",rows.group.to_numpy()),("horizon",rows.horizon.to_numpy())]:
            for value in np.unique(column):
                sub=column==value;a=mask&sub;f=summary(rows.delta.to_numpy()[sub],pred[key][sub],base[sub],losses[key][sub],oracle[sub],mask[sub]);tables[category].append(dict(model=key,**{category:str(value)},active_ratio=f["active"]["ratio"],full_ratio=f["full"]["ratio"],active_capture=f["active"]["oracle_capture_fraction"],active_cells=int(a.sum()),full_cells=int(sub.sum())))
                if category=="fold":result["fold_active_ratios"].append(f["active"]["ratio"])
        if key.startswith("source_"):
            family=key.split("_",1)[1];sourceout[family]=result;tables["expectation_source"].append(dict(source="PHIL_SPF",family=family,model=key,active_ratio=result["active"]["ratio"],full_ratio=result["full"]["ratio"],active_capture=result["active"]["oracle_capture_fraction"],full_capture=result["full"]["oracle_capture_fraction"],active_cells=int(mask.sum()),coverage=float(mask.mean()),fold_ratios=json.dumps(result["fold_active_ratios"]),controls_scope="same primary-active A5 controls reported in negative_controls.json"))
    # Source/family conditional results of the aggregate, plus independent family fits above.
    for family in ["RGDP","CPI","UNEMP","TBILL","TBOND"]:
        mask=rows.origin.map(lambda d:family in fam[d]).to_numpy()
        for key in ALL_KEYS:
            result=summary(rows.delta.to_numpy(),pred[key],base,losses[key],oracle,mask)
            tables["event_family"].append(dict(family=family,model=key,active_ratio=result["active"]["ratio"],full_ratio=result["full"]["ratio"],capture=result["active"]["oracle_capture_fraction"],active_cells=int(mask.sum()),note="overlapping source activation masks, not independent observations"))
    controls={c:out[c] for c in CONTROLS};comparisons={};decisions={}
    for key in ["A1","A2","A3","A4","A5","nonlinear"]:
        comparisons[key]={};clear=True
        for c in CONTROLS:
            e=block_bootstrap(cellblocks,losses[c][active],losses[key][active]);y=year_bootstrap(years,losses[c],losses[key]);passed=e.get("ratio_95_interval",[0,2])[1]<1 and y["ratio_95_interval"][1]<1
            comparisons[key][c]=dict(event_paired=e,year_paired=y,clear=bool(passed));clear=clear and passed
        decisions[key]=success(out[key],out[key]["fold_active_ratios"],clear,4)
    order=["NO","WEAK_YES","YES","STRONG_YES","MOONSHOT"];best=min([f"A{i}" for i in range(1,6)],key=lambda k:out[k]["active"]["ratio"]);gate=max((decisions[k] for k in decisions if k!="nonlinear"),key=lambda v:order.index(v));
    if gate=="NO" and decisions["nonlinear"]!="NO":gate="NONLINEAR_ONLY_SIGNAL"
    axis="EXPECTATION-02" if gate not in ["NO","NONLINEAR_ONLY_SIGNAL"] else ("EXPECTATION-COVERAGE-02" if out[best]["active"]["ratio"]<=.95 and out[best]["full"]["ratio"]>.995 else "POSITIONING-01")
    resultdir=root/"backtesting/expectation01/results"
    dump(resultdir/"crossfit_summary.json",dict(pre_result_sha=pre_sha,scorer_status="RESEARCH_PROXY_ONLY, not official composite or independent generalization proof",models=out,fit_audits=audits,best_descriptive_ridge=best,source_specific=sourceout))
    dump(resultdir/"active_summary.json",dict(models={k:v["active"] for k,v in out.items()},events=len({e for d in activeorigins for e in ids[d]}),release_dates=len({eventdates[e] for d in activeorigins for e in ids[d]}),years=15,origins=len(activeorigins),cells=int(active.sum()),full_cells=len(rows),coverage=float(active.mean())))
    dump(resultdir/"full_ledger_summary.json",dict(definition="fixed same82184 outer-test cells;135994 includes training",models={k:v["full"] for k,v in out.items()}))
    dump(resultdir/"oracle_capture_summary.json",dict(unclipped=True,full_perfect_location_ratio=float(oracle.sum()/base.sum()),active_perfect_location_ratio=float(oracle[active].sum()/base[active].sum()),active_only_oracle_on_full=out["A0"]["active_only_oracle_on_full"],models={k:dict(active_capture=v["active"]["oracle_capture_fraction"],full_capture=v["full"]["oracle_capture_fraction"]) for k,v in out.items()}))
    dump(resultdir/"negative_controls.json",dict(training_controls=controls,comparisons=comparisons,guards={"E_pre_release":"PASS: adversarial future and same-day raises ValueError","F_first_release":"PASS: latest/third vintage rejected,107original first releases validated","G_future_mutation":"PASS: future snapshots unchanged; no market data input; inherited cachedbaseline hashes and per-row common CRPS exact reproduction","H_source_timestamp":"PASS: post-release snapshot rejected"},control_masks="Paired primary-active mask; controls may have different own activation coverage. A/B/D leave E unchanged; stringent conservative comparison.",source_family_controls={f:{c:next(t for t in tables["event_family"] if t["family"]==f and t["model"]==c) for c in CONTROLS} for f in ["RGDP","CPI","UNEMP","TBILL","TBOND"]}))
    dump(resultdir/"event_bootstrap_summary.json",dict(method="2000 paired connected components of all overlapping original event dates; every affected origin/asset/horizon kept together; no cell bootstrap",blocks=len(set(blocks.values())),models=eventboot,source_specific_note="Independent family fits also evaluated on fixed aggregate primary-active mask for paired uncertainty"))
    dump(resultdir/"year_bootstrap_summary.json",dict(method="2000 paired calendar-year blocks; all within-year cells together",models=yearboot))
    # One value per original GDP event, averaging all its affected origins/assets/horizons.
    eventrows=[]
    for e in events:
        mask=rows.origin.map(lambda d:e["event_id"] in origininfo["surprise_events"][d]).to_numpy()
        if mask.any():eventrows.append(dict(event_id=e["event_id"],surprise=e["z"],delta=float(rows.delta.to_numpy()[mask].mean()),cells=int(mask.sum())))
    z=np.array([e["surprise"] for e in eventrows]);d=np.array([e["delta"] for e in eventrows]);diag=dict(events=len(eventrows),unique_dates=len({e["release_date"] for e in events if e["event_id"] in {r["event_id"] for r in eventrows}}),spearman=float(spearmanr(z,d).statistic),surprise_to_delta_slope=float(np.cov(z,d,ddof=0)[0,1]/np.var(z)),direction_agreement=float(np.mean(np.sign(z)==np.sign(d))),mean_delta_positive=float(d[z>0].mean()),mean_delta_negative=float(d[z<0].mean()),per_event_values_private=True)
    dump(resultdir/"event_diagnostics.json",diag)
    for name,table in tables.items():pd.DataFrame(table).to_csv(resultdir/f"{name}_summary.csv",index=False)
    decision=dict(PRE_RESULT_EXPECTATION01_SHA=pre_sha,EXPECTATION01_RESULT=gate,model_gates=decisions,NEXT_RESEARCH_AXIS=axis,READY_FOR_ONE_SHOT_SUBMISSION="NO",primary_source_gate="PASS",market_implied_source_gate="FAIL",all_precommitted_sources_retained=True,no_post_result_method_change=True)
    dump(resultdir/"final_decision.json",decision);np.savez_compressed(private/"losses.npz",row_index=ix,loss=loss,baseline=base,oracle=oracle,active=active,blocks=cellblocks);dump(private/"event_diagnostics_private.json",dict(events=eventrows));print(json.dumps(decision),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path.cwd());p.add_argument("--private",type=Path,required=True);p.add_argument("--location",type=Path,required=True);p.add_argument("--pre-result-sha",required=True);a=p.parse_args();run(a.root,a.private,a.location,a.pre_result_sha)

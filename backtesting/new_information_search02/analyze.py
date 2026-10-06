"""Executive summary: source persistence/alignment and price redundancy only; stop before forecasting."""
from pathlib import Path
import os,json,hashlib,subprocess,time
from datetime import datetime,timezone
import numpy as np,pandas as pd
from .core import *
from .catalog import inventory,SPEC
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent/'results'

def write(name,data):
    OUT.mkdir(exist_ok=True)
    (OUT/name).write_text(json.dumps(data,indent=2,allow_nan=False,default=lambda x:int(x) if isinstance(x,np.integer) else str(x)))

def status(stage,completed):
    (OUT.parent/'STATUS.json').write_text(json.dumps({'executive_summary':'Outcome-free source audit; no new forecasts or CRPS.','branch':'track2/new-information-search-02','HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'current_stage':stage,'completed_stages':completed,'last_update':datetime.now(timezone.utc).isoformat(),'last_successful_artifact':stage},indent=2))

def price_states(private):
    frame=pd.read_csv(private/'fred_prices.txt',index_col=0,parse_dates=True)
    assert frame.index.max()<=pd.Timestamp(SPEC['numeric_cutoff'])
    frame=frame.reindex(pd.bdate_range(frame.index.min(),frame.index.max())).ffill(limit=3)
    features={}
    for col in frame:
        features[col+'_level']=frame[col]
        for lag in [5,21,63]:features[col+'_'+str(lag)+'BD']=frame[col]-frame[col].shift(lag)
    features['2s5s']=frame.DGS5-frame.DGS2;features['2s10s']=frame.DGS10-frame.DGS2
    return pd.DataFrame(features),frame

def expanded_source(source,calendar,max_age):
    # Calendar is the complete known publication universe. An inactive/missing release interrupts held-state continuity.
    dates=pd.bdate_range('2016-01-01',SPEC['numeric_cutoff']);source=source.copy();source['available_at']=pd.to_datetime(source.available_at,utc=True)
    events={str(pd.Timestamp(d).date()):None for d in calendar}
    for _,r in source.iterrows():events[str(pd.Timestamp(r.date).date())]=r.value if np.isfinite(r.value) else None
    vals=[];last=None;release=None
    for d in dates:
        ds=str(d.date())
        if ds in events:last=events[ds];release=d
        expired=release is None or np.busday_count(np.datetime64(release.date(),'D'),np.datetime64(d.date(),'D'))>max_age
        vals.append(np.nan if expired or last is None else last)
    return pd.Series(vals,index=dates)

def run():
    private=Path(os.environ['NEWINFO02_PRIVATE']);pre=json.loads((private/'PRE-receipt.json').read_text())
    assert pre['remote_verified'] and pre['PRE_RESULT_NEWINFO02_SHA']
    # Verify all frozen parsed/receipt bytes before any source ranking.
    manifest=json.loads((private/'input_manifest.json').read_text())
    for path,sha in manifest['files'].items():assert hashlib.sha256((private/path).read_bytes()).hexdigest()==sha,path
    state=project_state(pd.read_parquet(private/'frozen_spd_direction_state.parquet'))
    features,price=price_states(private);records=inventory();persistence_rows=[];align_rows=[];red_rows=[]
    calendars={'FOMC_SEP_POLICY_PATH':[pd.Timestamp(__import__('re').search('20[0-9]{6}',u)[0]).date() for u in json.loads((private/'sep_links_full.json').read_text())], 'H41_RESERVES':[pd.Timestamp(d).date() for d in json.loads((private/'h41_acquisition_plan.json').read_text())['universe']], 'NYFED_ONRRP':pd.bdate_range('2015-01-01',SPEC['numeric_cutoff']), 'ATLANTA_MPT_SOFR':pd.bdate_range('2023-03-29',SPEC['numeric_cutoff'])}
    ages={'FOMC_SEP_POLICY_PATH':90,'H41_RESERVES':20,'NYFED_ONRRP':5,'ATLANTA_MPT_SOFR':5}
    for n,(source,calendar) in enumerate(calendars.items(),1):
        frame=pd.read_parquet(private/(source+'.parquet'));joined=join_asof(state,frame,ages[source]);joined.to_parquet(private/(source+'_joined.parquet'),index=False)
        ar=alignment(joined)
        for r in ar:r['source']=source;r['asof_only']=True;r['PIT']=next(x['PIT'] for x in records if x['source']==source)
        align_rows.extend(ar)
        pm=persistence(expanded_source(frame,calendar,ages[source]));pm['source']=source;pm['PIT']=ar[0]['PIT'];pm['expansion_is_contemporaneous_release_state_not_future_forecast']=True
        persistence_rows.append(pm)
        # One source row per origin. No future yields; 14 already known price variables only.
        j=joined.drop_duplicates('origin_date').set_index('origin_date');px=[]
        for origin in j.index:
            cutoff=origin_cutoff(origin);eligible=[d for d in features.index if available_eod(d+pd.offsets.BDay(1))<=cutoff]
            px.append(features.loc[eligible[-1]].to_dict() if eligible else {c:np.nan for c in features})
        px=pd.DataFrame(px,index=j.index);rm=redundancy(j.value,px);rm['source']=source
        red_rows.append({k:v for k,v in rm.items() if k!='correlations'});write(source+'-redundancy.json',rm)
        rec=next(x for x in records if x['source']==source)
        rec['Novelty']=rm['novelty'];rec['novelty']={'HIGH':2,'MEDIUM':1,'LOW':0,'REDUNDANT':0,'UNKNOWN':0}[rm['novelty']]
        rec['persistence']=2 if pm['observed_days']>=60 and (pm.get('lag_5_autocorrelation') or 0)>=.8 and (pm.get('unchanged_direction_fraction') or 0)>=.9 else 1 if pm['observed_days']>=20 and (pm.get('lag_5_autocorrelation') or 0)>=.5 else 0
        rb=next(r for r in ar if r['weighting']=='release');rec['alignment']=2 if rb['origins']>=24 and (rb['agreement'] or 0)>=.55 and (rb['Spearman'] or 0)>=.1 else 1 if rb['origins']>=12 and (rb['Spearman'] or 0)>0 else 0
        # Persist after each independently acquired source. Missing quant source is missing, not evidence of no information.
        pd.DataFrame(persistence_rows).to_csv(OUT/'persistence_summary.csv',index=False);pd.DataFrame(align_rows).to_csv(OUT/'spd_alignment_summary.csv',index=False);pd.DataFrame(red_rows).to_csv(OUT/'price_redundancy_summary.csv',index=False)
        print('source-state diagnostics',n,'/',len(calendars),source,'no target outcomes; output',OUT,flush=True)
    # Fixed price-only comparator; all assets/horizons retained, no best lag selection.
    prows=[]
    for asset,series in [('UST_2Y',price.DGS2),('UST_5Y',price.DGS5)]:
        for lag in [5,21,63]:
            src=pd.DataFrame({'date':series.index.astype(str),'available_at':[available_eod(d+pd.offsets.BDay(1)) for d in series.index],'value':(series-series.shift(lag)).to_numpy(),'source_state_id':['PRICE_'+str(d.date()) for d in series.index]})
            a=alignment(join_asof(state[state.asset==asset],src,5))
            for row in a:row.update(source='PRICE_'+str(lag)+'BD',asset=asset)
            prows.extend(a)
    # Combined fixed21 comparator, not an optimized horizon/lag subset.
    combined=[]
    for asset,series in [('UST_2Y',price.DGS2),('UST_5Y',price.DGS5)]:
        src=pd.DataFrame({'date':series.index.astype(str),'available_at':[available_eod(d+pd.offsets.BDay(1)) for d in series.index],'value':(series-series.shift(21)).to_numpy(),'source_state_id':['PRICE_'+str(d.date()) for d in series.index]});combined.append(join_asof(state[state.asset==asset],src,5))
    pa=alignment(pd.concat(combined));price_rb=pa[2];write('price_state_alignment.json',{'executive_summary':'Lagged official-yield proxy, not byte-identical original price cache. No future targets.','combined21BD':pa,'asset_lag_diagnostics':prows,'comparison_not_conclusive_for_full_prior_price_model':True})
    ranked=score_and_rank(records);decision=choose(ranked,align_rows,price_rb)
    # Report descriptive candidates; only genuinely eligible source can be the primary. A blocked high-priority acquisition target may be displayed separately.
    top=ranked[:3];lookup={r['source']:r for r in records}
    write('top3_sources.json',{'executive_summary':'Quality shortlist; inclusion does not override PIT/access/novelty gates.','sources':[{**r,'risk':lookup[r['source']]['risk'],'documentation':lookup[r['source']]['documentation']} for r in top]})
    pd.DataFrame(ranked).to_csv(OUT/'source_scorecard.csv',index=False)
    primary={'executive_summary':'Exactly one audit focus. No forced forecasting primary if hard gates or identification criteria fail.',**decision,'required_access':[] if decision['NEWINFO02_PRIMARY_SOURCE'] else ['Licensed CME ZQ contract-level settlement history2015/16-2024 with contract specifications, first-publication timestamps, settlement corrections and historical versions','Written historical API and derived-feature/offline contest-use permission','Contract-roll/expiry reconstruction and independent source-readiness gate before the draft can run']}
    write('selected_primary_source.json',primary)
    firewall=outcome_firewall(records,align_rows,price_rb);assert firewall['ranking_and_selection_bitwise_identical'];firewall.update(executive_summary='Input allowlists ignore future targets and CRPS. No forecast outcome ledgers read.',allowed_prediction_columns=STATE_COLUMNS,private_forecast_outcome_files_loaded=[],new_CRPS=0,new_forecasting_models=0)
    write('outcome_firewall_test.json',firewall)
    write('final_decision.json',{'executive_summary':'Audit-only source selection; no independent OOS and no official submission.',**primary,'Q1_beats_original_price_state':'NOT_ESTABLISHED: no exact prior market cache and no full original price-model replication','Q2_resolves_timing':'NOT_ESTABLISHED unless selected source has higher frequency; daily derivatives require license','Q3_persistence':'Source-state autocorrelation is descriptive; does not establish that SPD timing generated alpha','Q4_real_update_vs_regime':'No identified source has yet passed a future timing-specific forecast test','Q5_historical_asof_acquisition':'Original SEP/H41 samples available; licensed contract history not acquired','Q6_new_information':'Distinct policy-path contracts potentially novel, not empirically verified; spot-yield derivatives are price history','INDEPENDENT_VALIDATION':'NOT_AVAILABLE','next_model_executed':False,'new_CRPS':0,'no_official_submission':True})
    status('source_analysis_and_ranking_complete',['environment','direction_freeze','source_audit','implementation','research_tests','PRE','source_analysis','ranking'])
if __name__=='__main__':run()

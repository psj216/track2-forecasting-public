"""## Executive summary (read this first)
Complete every fixed model, conditional table, control comparison and paired block interval.
"""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from .evaluate_full import ALL_KEYS,load_predictions
from .chronological_crossfit import track_for_key
from .align_location_ledger import digest,dump
from .diagnostics import summary,success
from .negative_controls import CONTROLS
from .bootstrap import event_blocks,block_bootstrap,year_bootstrap

def run(private,location,pre_sha):
    allrows=pd.read_parquet(location/'ledger.parquet');ix=np.flatnonzero(pd.to_datetime(allrows.origin).dt.year.between(2010,2024));rows=allrows.loc[ix].reset_index(drop=True);pred,audits=load_predictions(private,allrows);pred={k:v[ix]for k,v in pred.items()};old=np.load(location/'losses.npz');assert np.array_equal(ix,old['row_index']);base,oracle=old['baseline'],old['oracle'];loss=np.zeros((len(ALL_KEYS),len(ix)));found=np.zeros(len(ix),bool);mapping={int(v):j for j,v in enumerate(ix)}
    for file in sorted((private/'score_chunks').glob('*.npz')):
        meta=json.loads(file.with_suffix('.json').read_text());assert digest(file)==meta['sha256']
        with np.load(file)as z:
            dest=[mapping[int(v)]for v in z['row_index']]
            if found[dest].any():raise ValueError('Overlapping score chunk')
            loss[:,dest]=z['loss'];found[dest]=True
    if not found.all():raise ValueError('Missing scoring chunk')
    losses={k:loss[j]for j,k in enumerate(ALL_KEYS)};x=np.load(private/'features_primary.npy',mmap_mode='r');schema=json.loads((private/'schema.json').read_text())['columns'];origin=json.loads((private/'origin_reports.json').read_text());info=origin['origins'];dates=origin['event_dates'];years=pd.to_datetime(rows.origin).dt.year.to_numpy();fold=np.select([years<=2013,years<=2017,years<=2020],[1,2,3],default=4);mask={};blocks={};effective={}
    for track in ('F','L','C'):
        classes=('F','L')if track=='C'else(track,);selected=[i for i,s in enumerate(schema)if s['class_id']in classes and s['stage']==1];mask[track]=np.any(x[ix][:,selected]!=0,axis=1);origins=sorted(rows.loc[mask[track],'origin'].unique());ids={str(o):[info[str(o)][c]['event_id']for c in classes if c in info[str(o)]]for o in origins};b=event_blocks(origins,ids,dates);blocks[track]=np.array([b[str(o)]for o in rows.loc[mask[track],'origin']]);reports={r for v in ids.values()for r in v};effective[track]=dict(active_cells=int(mask[track].sum()),active_origins=len(origins),unique_reports=len(reports),unique_report_weeks=len({str(pd.Timestamp(dates[e]).to_period('W-FRI'))for e in reports}),unique_release_dates=len({dates[e]for e in reports}),unique_years=len(np.unique(years[mask[track]])),source_instruments=len(classes),category_count=len(classes),connected_bootstrap_blocks=len(set(b.values())))
    resultdir=Path('backtesting/positioning01/results');tables={k:[]for k in ['fold','group','horizon','asset','source','category','report_age']};out={};reportboot={};yearboot={}
    for key in ALL_KEYS:
        track='C'if key=='P0'else track_for_key(key);a=mask[track];r=summary(rows.delta.to_numpy(),pred[key],base,losses[key],oracle,a);r['cap_hits']=sum(m['cap_count']for m in audits.get(key,[]));r['effective_sample_size']=effective[track];r['fold_active_ratios']=[];out[key]=r
        reportboot[key]=block_bootstrap(blocks[track],base[a],losses[key][a],oracle[a]);yearboot[key]=year_bootstrap(years,base,losses[key],np.where(a,oracle,base));
        for kind,column in [('fold',fold),('group',rows.group.to_numpy()),('horizon',rows.horizon.to_numpy()),('asset',rows.asset.to_numpy())]:
            for value in np.unique(column):
                sub=column==value;s=summary(rows.delta.to_numpy()[sub],pred[key][sub],base[sub],losses[key][sub],oracle[sub],a[sub]);aa=s['active'];ff=s['full'];tables[kind].append(dict(model=key,**{kind:str(value)},active_ratio=None if aa is None else aa['ratio'],full_ratio=None if ff is None else ff['ratio'],active_capture=None if aa is None else aa['oracle_capture_fraction'],active_cells=int((sub&a).sum()),full_cells=int(sub.sum()),status=s.get('status','EVALUATED')))
                if kind=='fold':r['fold_active_ratios'].append(None if aa is None else aa['ratio'])
        classes=('F','L')if track=='C'else(track,)
        for c in classes:
            sub=mask[c];s=summary(rows.delta.to_numpy(),pred[key],base,losses[key],oracle,sub);row=dict(model=key,source='TIC_FORM_S'if c=='F'else'FED_H41_RESERVES',category='foreign_transactions'if c=='F'else'depository_institutions',active_ratio=s['active']['ratio'],full_ratio=s['full']['ratio'],active_capture=s['active']['oracle_capture_fraction'],active_cells=int(sub.sum()),scope='conditional primary snapshot; no category selection');tables['source'].append(row);tables['category'].append(row)
            ages=np.array([info[str(o)].get(c,{}).get('age',-1)for o in rows.origin]);bins=np.select([ages<=5,ages<=10,ages<=20],['1-5BD','6-10BD','11-20BD'],default='21-30BD')
            for value in np.unique(bins[sub]):
                m=sub&(bins==value);s=summary(rows.delta.to_numpy(),pred[key],base,losses[key],oracle,m);tables['report_age'].append(dict(model=key,class_id=c,age_bin=value,active_ratio=s['active']['ratio'],active_cells=int(m.sum())))
        dump(private/'aggregate_chunks'/f'{key}.json',dict(summary=r,report_bootstrap=reportboot[key],year_bootstrap=yearboot[key]));print(json.dumps(dict(stage='aggregate model',model=key,active=r['active']['ratio'],full=r['full']['ratio'],artifact=str(private/'aggregate_chunks'/f'{key}.json'))),flush=True)
    comparisons={};decisions={}
    for key in ['F1','F2','L1','L2','C1','C2','nonlinear']:
        track=track_for_key(key);a=mask[track];clear=True;comparisons[key]={}
        for control in [track+'A',track+'B']:
            rb=block_bootstrap(blocks[track],losses[control][a],losses[key][a]);yb=year_bootstrap(years,losses[control],losses[key]);ok=rb.get('ratio_95_interval',[0,2])[1]<1 and yb['ratio_95_interval'][1]<1;comparisons[key][control]=dict(report_paired=rb,year_paired=yb,clear=bool(ok));clear=clear and ok
        folds=[v for v in out[key]['fold_active_ratios']if v is not None];decisions[key]=success(out[key],folds,clear,len(folds))
    ranking=['NO','WEAK_YES','YES','STRONG_YES','MOONSHOT'];trackdec={t:max([decisions[t+'1'],decisions[t+'2']],key=lambda v:ranking.index(v)if v in ranking else -1)for t in 'FLC'}
    total=max(trackdec.values(),key=lambda v:ranking.index(v)if v in ranking else -1)
    if total=='NO' and decisions['nonlinear']!='NO':total='NONLINEAR_ONLY_SIGNAL'
    axis='FLOW-02'if trackdec['F']in ranking[2:]else('LIQUIDITY-02'if trackdec['L']in ranking[2:]else'CONTEXT-01')
    weakfull=any(out[k]['active']['ratio']<=.95 and out[k]['full']['ratio']>.995 for k in ['F1','F2','L1','L2','C1','C2'])
    if weakfull and axis=='CONTEXT-01':axis='POSITIONING-COVERAGE-02'
    decision=dict(PRE_RESULT_POSITIONING01_SHA=pre_sha,POSITIONING01_RESULT=total,POSITIONING_RESULT='SOURCE_GATE_FAIL',FLOW_RESULT=trackdec['F'],LIQUIDITY_RESULT=trackdec['L'],COMBINED_RESULT=trackdec['C'],model_gates=decisions,NEXT_RESEARCH_AXIS=axis,READY_FOR_ONE_SHOT_SUBMISSION='NO',no_post_result_source_selection=True,scoring_scope='Research normalized marginal fair CRPS proxy; not official composite',primary_positioning_unanswered=True)
    dump(resultdir/'crossfit_summary.json',dict(pre_result_sha=pre_sha,models=out,fit_audits=audits))
    dump(resultdir/'positioning_summary.json',dict(status='NOT_EVALUATED_SOURCE_GATE_FAIL',models={k:'NOT_EVALUATED'for k in ['P1','P2','P3','P4']},reason='Original CFTC value and actual historical publication timing not fully verified; NY Fed current-vintage history is revised',level_change='NOT_EVALUATED',individual_categories='NOT_EVALUATED',crowding_quintiles='NOT_EVALUATED'))
    for t,n in [('F','flow'),('L','liquidity'),('C','combined')]:dump(resultdir/(n+'_summary.json'),dict(result=trackdec[t],models={k:v for k,v in out.items()if k.startswith(t)},effective_sample_size=effective[t]))
    dump(resultdir/'negative_controls.json',dict(fit_controls={k:out[k]for k in CONTROLS},paired_comparisons=comparisons,guards={k:'PASS'for k in ['E_publication','F_future_report','G_future_OI','H_original_revision','I_geometry']},C_instrument_rotation='NOT_IDENTIFIABLE: one directly mapped flow instrument, one globally exposed macro liquidity instrument; no genuine P direct instruments',D_category_rotation='NOT_IDENTIFIABLE: no admitted P categories and one aggregate category per admitted source',C_D_affect_success='Source-applicable A/B plus paired year/report intervals define clear controls; no informative C/D permutation is asserted. This limits interpretation.',control_masks='Each control compared on the paired primary mask of its own F/L/C class; B older source may expire, retaining exact baseline on inactive rows'))
    dump(resultdir/'report_block_bootstrap.json',dict(method='2000 paired latest-published snapshot release-date connected components; all affected origins/assets/horizons together; coincident publication dates unioned; derived features are report snapshots, not additional pseudo-events; no cell bootstrap',models=reportboot,effective_sample_size=effective))
    dump(resultdir/'year_block_bootstrap.json',dict(method='2000 paired calendar-year blocks; active-only oracle on fixed full ledger',models=yearboot))
    for name,table in tables.items():pd.DataFrame(table).to_csv(resultdir/(name+'_summary.csv'),index=False)
    pd.DataFrame([dict(quintile=q,status='NOT_EVALUATED_SOURCE_GATE_FAIL',reason='No original PIT positioning source')for q in ['Q1','Q2','Q3','Q4','Q5']]).to_csv(resultdir/'crowding_summary.csv',index=False)
    dump(resultdir/'final_decision.json',decision);np.savez_compressed(private/'losses.npz',row_index=ix,loss=loss,baseline=base,oracle=oracle);print(json.dumps(decision),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private',type=Path,required=True);p.add_argument('--location',type=Path,required=True);p.add_argument('--pre-result-sha',required=True);a=p.parse_args();run(a.private,a.location,a.pre_result_sha)

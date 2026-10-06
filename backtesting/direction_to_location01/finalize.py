"""Executive summary: apply only the frozen primary gates; secondary results never determine verdict."""
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from .core import *
from .evaluate import inputs

def concentration(rows,base,candidate):
    gain=base-candidate;out={}
    for field in ['release_id','year','asset','horizon']:
        records=[]
        for key,g in rows.groupby(field):
            ii=g.index.to_numpy();b=float(base[ii].sum());c=float(candidate[ii].sum());den=float(base.sum()-b)
            records.append(dict(block=str(key),cells=len(g),gain=float(gain[ii].sum()),ratio_without_block=float((candidate.sum()-c)/den)))
        positive=sum(max(x['gain'],0) for x in records);shares=[max(x['gain'],0)/positive for x in records] if positive>0 else [0.]*len(records)
        for rec,share in zip(records,shares):rec['share_gross_positive_block_gain']=share
        out[field]=dict(blocks=records,largest_positive_gain_share=max(shares),leave_one_out_ratio_range=[min(x['ratio_without_block'] for x in records),max(x['ratio_without_block'] for x in records)],all_leave_one_out_below_baseline=all(x['ratio_without_block']<1 for x in records))
    nonconcentrated=out['release_id']['largest_positive_gain_share']<=.5 and out['year']['all_leave_one_out_below_baseline']
    return dict(dimensions=out,NONCONCENTRATED=nonconcentrated,never_drop_from_primary=True)

def verdict(primary,annual,controls,bootstrap,conc,direction_evidence):
    ratio=primary['crps_ratio'];capture=primary['oracle_capture'];improved=sum(x['crps_ratio']<1 for x in annual)
    stochastic=[controls[k] for k in CONTROLS];inferior=all(x['median_ratio']>ratio+1e-12 for x in stochastic) and controls['ONE_YEAR_SHIFT']['crps_ratio']>ratio+1e-12
    clear=inferior and all(x['fraction_at_least_as_good']<.05 for x in stochastic)
    release_support=bootstrap['release']['models'][PRIMARY]['crps_ratio_95ci'][1]<1
    year_support=bootstrap['year']['models'][PRIMARY]['crps_ratio_95ci'][1]<=1
    retained=direction_evidence['sign_accuracy']>=.55 and direction_evidence['spearman']>=.10
    absent=direction_evidence['sign_accuracy']<=.5 and direction_evidence['spearman']<=0
    if ratio>=1.01 or not inferior or absent:result='NO'
    elif ratio<=.95 and capture>=.10 and improved>=4 and release_support and year_support and clear and conc['NONCONCENTRATED']:result='STRONG_YES'
    elif ratio<=.97 and capture>=.05 and improved>=3 and release_support and inferior and conc['NONCONCENTRATED']:result='YES'
    elif ratio<.99 and improved>len(annual)-improved and inferior and retained:result='WEAK_YES'
    else:result='INCONCLUSIVE'
    return result,dict(primary_ratio=ratio,primary_oracle_capture=capture,annual_folds_improved=improved,annual_folds_total=len(annual),controls_inferior=inferior,controls_clearly_inferior=clear,release_upper_CI_below_one=release_support,year_upper_CI_at_most_one=year_support,release_direction_retained=retained,nonconcentrated=conc['NONCONCENTRATED'],secondary_used_to_decide=False)

def run(private):
    p,r,f=inputs(private);scores=np.load(p/'all_scores.npz');names=list(scores['names']);j=names.index(PRIMARY);candidate=scores['losses'][j];shift=scores['shifts'][j];summary=json.loads((OUT/'primary_summary.json').read_text());boot=json.loads((OUT/'bootstrap_summary.json').read_text())['blocks'];controls=json.loads((OUT/'negative_controls.json').read_text())['controls'];years=pd.read_csv(OUT/'year_summary.csv');annual=years.loc[years.balance=='cell'].to_dict('records');conc=concentration(r,f['base'],candidate);save(OUT/'concentration_summary.json',conc)
    primary=summary['models'][PRIMARY];result,gates=verdict(primary,annual,controls,boot,conc,summary['release_balanced_primary']['frozen_source_direction'])
    axis={'STRONG_YES':'DIRECTION-TRANSFER-02','YES':'DIRECTION-TRANSFER-02','WEAK_YES':'DIRECTION-ROBUSTNESS-02','INCONCLUSIVE':'DIRECTION-EVIDENCE-AUDIT-02','NO':'NEW-INFORMATION-SEARCH-02'}[result]
    sec=json.loads((OUT/'secondary_sensitivity.json').read_text())['models'];lead=[]
    if result in ['NO','INCONCLUSIVE']:
        if primary['crps_ratio']>=1 and any(sec[n]['crps_ratio']<1 for n in SECONDARY):lead.append('MAGNITUDE_SELECTION_UNRESOLVED')
        if primary['crps_ratio']>=1 and sec['OOD3_DIAGNOSTIC']['crps_ratio']<1 and all(sec[n]['crps_ratio']>=1 for n in SECONDARY):lead.append('OOD_GATING_LEAD_ONLY')
    decision={'DTL01_RESULT':result,'primary_model':PRIMARY,'primary_amplitude':PRIMARY_AMPLITUDE,'primary_gates':gates,'secondary_lead_status':lead or ['SECONDARY_SENSITIVITY_ONLY'],'NEXT':axis,'exactly_one_next_axis':True,'RESEARCH_EXPOSED':True,'INDEPENDENT_OOS':False,'READY_FOR_SUBMISSION':False,'development_called':False,'submission_packaged':False,'PRE_RESULT_DTL01_SHA':verify_pre(p),'source_models_refit':0,'2023_included':True,'secondary_cannot_rescue_primary':True,'scientific_spec_modified_after_scores':False};save(OUT/'final_decision.json',decision)
    g=r.loc[r.year==2023];ii=g.index.to_numpy();old=g.candidate_cell_CRPS.to_numpy();audit2023={**score_summary(g,f['base'][ii],candidate[ii],scores['losses'][5][ii],shift[ii]),'release_balanced':score_summary(g,f['base'][ii],candidate[ii],scores['losses'][5][ii],shift[ii],'release'),'OOD_fraction':float((f['zmax'][ii]>3).mean()),'original_full_SPD_ratio':float(old.sum()/f['base'][ii].sum()),'total_primary_score_delta':float((candidate[ii]-f['base'][ii]).sum()),'fraction_overall_primary_score_delta':float((candidate[ii]-f['base'][ii]).sum()/(candidate-f['base']).sum()),'no_2023_exclusion':True};save(OUT/'year2023_audit.json',audit2023)
    byrelease=r.groupby('release_id').agg(cells=('asset','size'),origins=('origin_date','nunique'));repeated=byrelease.index[byrelease.origins>1]
    save(OUT/'release_dependence.json',{'cells':len(r),'origins':int(r.origin_date.nunique()),'unique_releases':len(byrelease),'origins_per_release':byrelease.origins.describe().to_dict(),'cells_per_release':byrelease.cells.describe().to_dict(),'cells_sharing_releases_across_origins_fraction':float(r.release_id.isin(repeated).mean()),'release_blocks_not_proven_independent':True,'552_not_552_independent_information_events':True})
    status('diagnostics',str(OUT/'final_decision.json'));print('FROZEN PRIMARY VERDICT',result,'NEXT',axis,flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private',type=Path,required=True);v=a.parse_args();run(v.private)

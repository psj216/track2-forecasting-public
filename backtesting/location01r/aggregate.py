"""## Executive summary (read this first)

Aggregate only the complete fixed card universe with LOCATION-01's unchanged
scorer and geometric aggregation. Individual outcomes stay private.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from backtesting.location01.evaluate_card_transfer import summarize
from qfbench2_track_forecasting.ceiling01.scorer_adapter import aggregate
from backtesting.location01r.recovery import dump,digest,PARENT,BRANCH

def extended_summary(records):
    out=summarize(records)
    for key in ('marginal','joint','tail'):
        applicable=[v for v in records if v['baseline'][key]>1e-12]
        perfect=aggregate([v['oracle'][key]/v['baseline'][key] for v in applicable])
        candidate=out[key+'_ratio']
        out[key+'_oracle_ratio']=perfect
        out[key+'_oracle_capture_fraction']=(None if perfect is None or perfect==1 else (1-candidate)/(1-perfect))
        out[key+'_applicable_cards']=len(applicable)
        out[key+'_oracle_mean']=float(np.mean([v['oracle'][key] for v in records]))
    return out

def decision(single,multi,families):
    s=single['models']['M1'];m=multi['models']['M1'];f=families['M1'];joint_ok=lambda x:x is None or x<=1.10
    if m['marginal_ratio']<1 and m['joint_ratio']>1.10 and m['ratio']>=1:
        axis='PATH-01'
    elif s['ratio']<=.90 and m['ratio']<=.90 and m['marginal_ratio']<1 and joint_ok(m['joint_ratio']):
        axis='LOCATION-02'
    elif s['ratio']<=.97 and sum(v['ratio']<1 for v in f.values())>=2 and any(f[k]['ratio']<1 for k in ('T2-F1','T2-F2')):
        axis='CONTEXT-01'
    else:axis='NEW_INFORMATION_REQUIRED'
    coherent=(s['ratio']<1 and m['ratio']<1 and s['marginal_ratio']<1 and m['marginal_ratio']<1
              and joint_ok(s['joint_ratio']) and joint_ok(m['joint_ratio']))
    diagnostic='POSITIVE' if coherent else ('NEGATIVE' if s['ratio']>=1 and m['ratio']>=1 and s['marginal_ratio']>=1 and m['marginal_ratio']>=1 else 'MIXED')
    f1=f['T2-F1']
    if f1['marginal_ratio']>=1:verdict='NO_CARD_LOCATION_TRANSFER'
    elif f1['joint_ratio']>1.10 and f1['ratio']>=1:verdict='LOCATION_SIGNAL_BUT_PATH_REQUIRED'
    elif joint_ok(f1['joint_ratio']) and f1['ratio']<1:verdict='CARD_LOCATION_TRANSFER_POSITIVE'
    else:verdict='MIXED_CARD_LOCATION_TRANSFER'
    return {'executive_summary':'Keep the failed continuous gate distinct from complete exposed-card transfer diagnostics.','status':'COMPLETE','primary_model':'M1','CONTINUOUS_LOCATION_GATE':'NO','TRANSFER_DIAGNOSTIC':diagnostic,'READY_FOR_LOCATION_02':'NO','NEXT_RESEARCH_AXIS':axis,'READY_FOR_ONE_SHOT_SUBMISSION':'NO','F1_SAFETY_VERDICT':verdict,'interpretation':'Research proxy on 24 historically exposed cards. No independent OOS evidence, no text-channel causal ablation, no submission candidate.'}

def run(root,private,pre_sha):
    result=root/'backtesting/location01r/results';manifest=json.loads((result/'snapshot_manifest.json').read_text())
    chunks=[]
    for i in range(24):
        q=private/f'evaluated-{i:02d}.json';assert q.is_file(),f'Missing card {i}'
        d=json.loads(q.read_text());assert d['card_index']==i and d['pre_result_sha']==pre_sha
        assert d['card_id']==manifest['cards'][i]['card_id'] and len(d['records'])==6
        assert [v['model'] for v in d['records']]==[f'M{m}' for m in range(6)]
        assert all(v['guard']['passed'] for v in d['records']), 'TRUE_GEOMETRY_VIOLATION'
        assert digest(private/manifest['cards'][i]['snapshot_file'])==manifest['cards'][i]['snapshot_sha256']
        chunks.append(d)
    records={f'M{m}':[d['records'][m] for d in chunks] for m in range(6)}
    single={'executive_summary':'All thirteen fixed single-cell cards, all frozen channel sequences, no refitting.','status':'TRANSFER_DIAGNOSTIC','cards':13,'primary_model':'M1','models':{k:extended_summary([v for v in vals if v['single']]) for k,vals in records.items()}}
    multi={'executive_summary':'All eleven fixed multicell cards with all components recomputed by the unchanged scorer.','status':'TRANSFER_DIAGNOSTIC','cards':11,'primary_model':'M1','models':{k:extended_summary([v for v in vals if not v['single']]) for k,vals in records.items()}}
    families={k:{fam:extended_summary([v for v in vals if v['family']==fam]) for fam in ('T2-F1','T2-F2','T2-F3','T2-F4')} for k,vals in records.items()}
    assert all(v['cards']==13 for v in single['models'].values()) and all(v['cards']==11 for v in multi['models'].values())
    assert all(v['cards']==6 for model in families.values() for v in model.values())
    dump(result/'single_cell_transfer.json',single);dump(result/'multi_cell_transfer.json',multi)
    pd.DataFrame([{'model':model,'family':fam,**data} for model,ff in families.items() for fam,data in ff.items()]).to_csv(result/'family_transfer.csv',index=False)
    final=decision(single,multi,families);final.update(PRE_RESULT_LOCATION01R_SHA=pre_sha,parent_sha=PARENT,branch=BRANCH)
    dump(result/'final_decision.json',final)
    f1={'executive_summary':'F1 component means and matching-card geometric component ratios; primary M1 chosen before transfer scores.','primary_model':'M1','verdict':final['F1_SAFETY_VERDICT'],'models':{k:v['T2-F1'] for k,v in families.items()},'joint_damage_threshold':1.10}
    dump(result/'f1_safety.json',f1)
    raw=[];public=[]
    for d in chunks:
        for v in d['records']:
            g=v['guard'];o=v['old_guard'];row={'card_id':v['card_id'],'family':v['family'],'single':v['single'],'model':v['model'],'old_guard_status':o['old_guard_status'],'new_guard_status':g['passed'],'strict_reversal_count':g['strict_reversal_count'],'rounded_tie_count':g['rounded_tie_count'],'max_shift_tolerance':max(g['shift_tolerance']),'max_shift_residual':g['max_shift_residual'],'max_centered_residual':g['max_centered_residual'],'candidate_sha256':v['candidate_sha256']}
            public.append(row)
            raw.append({**row,**{f'{role}_{key}':v[role][key] for role in ('baseline','candidate','oracle') for key in ('marginal','joint','tail')},'composite_ratio':v['candidate']['ratio'],'oracle_composite_ratio':v['oracle']['ratio']})
    pd.DataFrame(public).to_csv(result/'transfer_card_summary.csv',index=False)
    pd.DataFrame(raw).to_csv(private/'transfer_card_summary.csv',index=False)
    dump(private/'card_transfer_detail.json',records)
    audit={'executive_summary':'All 24 cards and 144 model-card pairs pass; immutable snapshot hashes and candidate reconstruction were checked for every card.','cards_passed':24,'cards_total':24,'model_checks_passed':144,'true_violations':0,'max_shift_residual':max(v['max_shift_residual'] for v in public),'max_centered_residual':max(v['max_centered_residual'] for v in public),'strict_reversals':sum(v['strict_reversal_count'] for v in public),'snapshot_hashes_unchanged':True,'no_refit':True,'private_card_csv_sha256':digest(private/'transfer_card_summary.csv'),'private_card_detail_sha256':digest(private/'card_transfer_detail.json')}
    dump(result/'transfer_validation.json',audit)
    dump(private/'STATUS.json',{'stage':'transfer_complete','cards':24,'pre_result_sha':pre_sha,'final_decision':final})
    print(json.dumps({'single_M1':single['models']['M1'],'multi_M1':multi['models']['M1'],'decision':final},indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--private',type=Path,required=True);p.add_argument('--pre-sha',required=True);a=p.parse_args();run(a.root,a.private,a.pre_sha)

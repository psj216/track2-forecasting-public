"""## Executive summary (read this first)

Snapshot existing forecasts, reproduce old guard failures, and score only after
the numerical repair is remotely frozen. No fitting or continuous rescoring.
"""
import argparse
import hashlib
import json
import os
import pickle
import subprocess
from pathlib import Path
import numpy as np
from qfbench2_track_forecasting.thesis01.asset_semantics import load_universe
from qfbench2_track_forecasting.location01.feature_own_history import history_state
from qfbench2_track_forecasting.location01.engine import prepare,shift
from backtesting.location01.build_features import card_features

PARENT='4c35ef22e9b1bafe2d9fc009e6b3151e09afb723'
BRANCH='track2/location-01r-transfer-guard'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def array_digest(x):
    x=np.ascontiguousarray(x)
    h=hashlib.sha256(str(x.dtype).encode()+str(x.shape).encode())
    h.update(x.tobytes());return h.hexdigest()

def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n');os.replace(temp,path)

def legacy_guard(before,after):
    # Exact frozen b05f73ace expression, retained only for validation audit.
    before,after=np.asarray(before),np.asarray(after)
    return (np.allclose(before-before[0],after-after[0],rtol=1e-10,atol=1e-10) and
            np.array_equal(np.argsort(before,axis=0),np.argsort(after,axis=0)))

def old_diagnostics(before,after):
    b=before.reshape(len(before),-1);a=after.reshape(len(after),-1)
    order=np.argsort(b,axis=0,kind='stable')
    bs=np.take_along_axis(b,order,axis=0);aa=np.take_along_axis(a,order,axis=0)
    bg=np.diff(bs,axis=0);ag=np.diff(aa,axis=0)
    delta=a-b;residual=delta-np.median(delta,axis=0)
    return {'old_guard_status':bool(legacy_guard(before,after)),
            'baseline_shape':list(before.shape),'candidate_shape':list(after.shape),
            'exact_argsort_mismatch_count':int(np.count_nonzero(np.argsort(b,axis=0)!=np.argsort(a,axis=0))),
            'strict_reversal_count':int(np.count_nonzero(ag<0)),
            'rounded_tie_count':int(np.count_nonzero((bg>0)&(ag==0))),
            'max_centered_error':float(np.max(np.abs((before-before[0])-(after-after[0])))),
            'max_shift_nonuniformity':float(np.max(np.abs(residual)))}

def snapshot(root,old_private,card_private,private):
    result=root/'backtesting/location01r/results'
    old=json.loads((root/'backtesting/location01/results/transfer_blocker_audit.json').read_text())
    schema=json.loads((old_private/'schema.json').read_text())
    with (old_private/'transfer_models.pkl').open('rb') as f:models=pickle.load(f)
    cards=json.loads((card_private/'cards.json').read_text())
    series,kinds,_=load_universe(root);state=history_state(series,kinds);cross,summaries=prepare(state)
    entries=[];failures=[];private.mkdir(parents=True,exist_ok=True)
    for index,card in enumerate(cards):
        with np.load(card_private/card['file']) as data:baseline=data['baseline']
        x=card_features(card,baseline,state,cross,summaries,schema);sd=np.std(baseline,axis=0,ddof=0)
        deltas=[];candidates=[];caps=[];audits=[]
        for m in range(6):
            delta,cap=(np.zeros(len(x)),0) if m==0 else models[card['id']][m].predict(x)
            candidate=shift(baseline,np.asarray(delta).reshape(sd.shape),sd)
            deltas.append(delta);candidates.append(candidate);caps.append(cap)
            audits.append({'model':f'M{m}',**old_diagnostics(baseline,candidate)})
        failed=next((a for a in audits if not a['old_guard_status']),None)
        if failed:failures.append({'card_id':card['id'],**failed})
        q=private/f'snapshot-{index:02d}.npz'
        np.savez_compressed(q,baseline=baseline,features=x,delta=np.asarray(deltas),candidate=np.asarray(candidates),caps=np.asarray(caps))
        entry={'card_index':index,'card_id':card['id'],'family':card['family'],'cells':card['cells'],
               'snapshot_file':q.name,'snapshot_sha256':digest(q),'source_card_sha256':digest(card_private/card['file']),
               'baseline_sha256':array_digest(baseline),'feature_sha256':array_digest(x),
               'delta_sha256':array_digest(np.asarray(deltas)),'candidate_sha256':array_digest(np.asarray(candidates)),
               'old_guard_all_models_pass':all(a['old_guard_status'] for a in audits)}
        entries.append(entry);dump(private/f'snapshot-audit-{index:02d}.json',{'card_id':card['id'],'models':audits})
        print(f'snapshot {index+1}/24 {card["id"]} saved={q.name}',flush=True)
    totals={'blocked_cards':len(failures),'rounded_ties':sum(a['rounded_tie_count'] for a in failures),
            'strict_reversals':sum(a['strict_reversal_count'] for a in failures),
            'max_centered_error':max(a['max_centered_error'] for a in failures),
            'max_shift_nonuniformity':max(a['max_shift_nonuniformity'] for a in failures)}
    expected={a['card_id']:a for a in old['failure_details']}
    assert set(expected)=={a['card_id'] for a in failures}
    for a in failures:
        e=expected[a['card_id']]
        assert a['model']==e['first_failed_model'] and a['rounded_tie_count']==e['distinct_adjacent_values_rounded_to_ties']
        assert a['strict_reversal_count']==e['strict_order_reversals'] and a['max_centered_error']==e['max_centered_error']
    assert totals['blocked_cards']==13 and totals['rounded_ties']==94 and totals['strict_reversals']==0
    assert totals['max_centered_error']==8.881784197001252e-16
    dump(result/'guard_reproduction.json',{'executive_summary':'All 13 frozen first failures reproduced exactly before repair, without opening transfer aggregates.','old_blocker_reproduced':True,'totals':totals,'first_failures':failures})
    dump(result/'snapshot_manifest.json',{'executive_summary':'Immutable existing-model predictions and unchanged candidate arrays frozen before aggregate scoring.','parent_sha':PARENT,'transfer_models_sha256':digest(old_private/'transfer_models.pkl'),'no_refit':True,'cards':entries})
    dump(private/'STATUS.json',{'stage':'old_failure_reproduced','completed_cards':24,'aggregate_scores_opened':False})
    print('OLD_FAILURE_REPRODUCED',json.dumps(totals),flush=True)

def validate(root,private):
    from qfbench2_track_forecasting.location01r.guard import translation_audit
    manifest=json.loads((root/'backtesting/location01r/results/snapshot_manifest.json').read_text())
    records=[];before_hashes=[]
    for card in manifest['cards']:
        q=private/card['snapshot_file'];assert digest(q)==card['snapshot_sha256'];before_hashes.append(digest(q))
        with np.load(q) as data:
            for m in range(6):
                info=translation_audit(data['baseline'],data['candidate'][m]);assert info['passed'],(card['card_id'],m,info)
                records.append({'card_id':card['card_id'],'model':f'M{m}',**info})
        assert digest(q)==before_hashes[-1]
        print(f'guard validation {card["card_index"]+1}/24 no scoring',flush=True)
    dump(private/'pretransfer_guard_validation.json',records)
    out={'executive_summary':'All frozen snapshots pass the repaired guard before transfer score aggregation; inputs are unchanged.','cards':24,'model_card_checks':144,'passed':144,'failed':0,'old_blocked_cards_recovered':13,'old_completed_cards_preserved':11,'true_violations':0,'snapshot_hashes_unchanged':True,
         'max_shift_residual':max(a['max_shift_residual'] for a in records),
         'max_centered_residual':max(a['max_centered_residual'] for a in records),
         'strict_reversals':sum(a['strict_reversal_count'] for a in records),
         'private_validation_sha256':digest(private/'pretransfer_guard_validation.json')}
    dump(root/'backtesting/location01r/results/guard_validation.json',out);print(json.dumps(out),flush=True)

def evaluate(root,old_private,card_private,private,start,end,pre_sha):
    from backtesting.location01.evaluate_multicell import recompute
    from qfbench2_track_forecasting.location01r.guard import translation_audit
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==pre_sha
    assert subprocess.check_output(['git','rev-parse','origin/'+BRANCH],cwd=root,text=True).strip()==pre_sha
    manifest=json.loads((root/'backtesting/location01r/results/snapshot_manifest.json').read_text())
    assert digest(old_private/'transfer_models.pkl')==manifest['transfer_models_sha256']
    cards=json.loads((card_private/'cards.json').read_text())
    for i in range(start,end):
        card=cards[i];entry=manifest['cards'][i];q=private/f'evaluated-{i:02d}.json'
        if q.exists():print(f'resume saved card {i+1}/24',flush=True);continue
        assert digest(private/entry['snapshot_file'])==entry['snapshot_sha256']
        assert digest(card_private/card['file'])==entry['source_card_sha256']
        with np.load(private/entry['snapshot_file']) as data:
            baseline=data['baseline'];deltas=data['delta'];candidate=data['candidate'];caps=data['caps']
        with np.load(card_private/card['file']) as data:
            np.testing.assert_array_equal(baseline,data['baseline']);truth=data['truth']
        records=[]
        for m in range(6):
            info=translation_audit(baseline,candidate[m]);old=old_diagnostics(baseline,candidate[m])
            if not info['passed']:
                dump(private/'STATUS.json',{'stage':'TRUE_GEOMETRY_VIOLATION','card_id':card['id'],'model':f'M{m}','audit':info})
                raise AssertionError('TRUE_GEOMETRY_VIOLATION: do not drop card')
            rebuilt=shift(baseline,deltas[m].reshape(baseline.shape[1:]),np.std(baseline,axis=0,ddof=0))
            np.testing.assert_array_equal(rebuilt,candidate[m])
            base,pred,oracle=recompute(baseline,truth,deltas[m])
            records.append({'card_id':card['id'],'family':card['family'],'single':card['cells']==1,'model':f'M{m}',
                            'baseline':base,'candidate':pred,'oracle':oracle,'safety_caps':int(caps[m]),
                            'guard':info,'old_guard':old,'candidate_sha256':array_digest(candidate[m])})
        dump(q,{'card_index':i,'card_id':card['id'],'records':records,'pre_result_sha':pre_sha})
        dump(private/'STATUS.json',{'stage':'transfer_scoring','last_saved_card':i+1,'total_cards':24,'pre_result_sha':pre_sha})
        print(f'transfer {i+1}/24 saved={q.name} all 6 model guards pass',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['snapshot','validate','evaluate']);p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--old-private',type=Path,required=True);p.add_argument('--card-private',type=Path,required=True);p.add_argument('--private',type=Path,required=True);p.add_argument('--start',type=int,default=0);p.add_argument('--end',type=int,default=24);p.add_argument('--pre-sha');a=p.parse_args()
    if a.stage=='snapshot':snapshot(a.root,a.old_private,a.card_private,a.private)
    elif a.stage=='validate':validate(a.root,a.private)
    else:evaluate(a.root,a.old_private,a.card_private,a.private,a.start,a.end,a.pre_sha)

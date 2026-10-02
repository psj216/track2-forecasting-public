"""## Executive summary (read this first)

Apply already frozen continuous as-of models to 24 historical proxy cards.
Do not fit any model here. Card outcomes are evaluation truth only.
"""
import argparse
import json
import pickle
from pathlib import Path
import numpy as np
import pandas as pd
from qfbench2_track_forecasting.thesis01.asset_semantics import load_universe
from qfbench2_track_forecasting.location01.feature_own_history import history_state
from qfbench2_track_forecasting.location01.engine import prepare
from qfbench2_track_forecasting.ceiling01.scorer_adapter import aggregate
from .build_features import card_features
from .build_location_ledger import dump,digest
from .evaluate_multicell import recompute
from .diagnostics import capture

def summarize(records):
    perfect=aggregate([v['oracle']['ratio'] for v in records])
    candidate=aggregate([v['candidate']['ratio'] for v in records])
    out={'cards':len(records),'baseline_composite':1.,'candidate_composite':candidate,
         'perfect_location_composite':perfect,'ratio':candidate,
         'oracle_capture_fraction':capture(candidate,perfect)}
    for key in ('marginal','joint','tail'):
        applicable=[v for v in records if v['baseline'][key]>1e-12]
        out[f'{key}_ratio']=aggregate([v['candidate'][key]/v['baseline'][key] for v in applicable])
        out[f'{key}_baseline_mean']=float(np.mean([v['baseline'][key] for v in records]))
        out[f'{key}_candidate_mean']=float(np.mean([v['candidate'][key] for v in records]))
    return out

def evaluate(root,private,card_private):
    schema=json.loads((private/'schema.json').read_text())
    with (private/'transfer_models.pkl').open('rb') as f:models=pickle.load(f)
    cards=json.loads((card_private/'cards.json').read_text())
    series,kinds,_=load_universe(root);state=history_state(series,kinds)
    cross,summaries=prepare(state);records={f'M{m}':[] for m in range(6)};caps={f'M{m}':0 for m in range(6)}
    for card in cards:
        data=np.load(card_private/card['file']);baseline=data['baseline'];truth=data['truth']
        x=card_features(card,baseline,state,cross,summaries,schema)
        for m in range(6):
            delta=np.zeros(len(x)) if m==0 else models[card['id']][m].predict(x)[0]
            if m: caps[f'M{m}']+=models[card['id']][m].predict(x)[1]
            base,candidate,oracle=recompute(baseline,truth,delta)
            records[f'M{m}'].append({'card_id':card['id'],'family':card['family'],
                'single':card['cells']==1,'baseline':base,'candidate':candidate,'oracle':oracle})
        data.close()
    single={m:summarize([v for v in vv if v['single']]) for m,vv in records.items()}
    multi={m:summarize([v for v in vv if not v['single']]) for m,vv in records.items()}
    families=[]
    for m,vv in records.items():
        for family in ('T2-F1','T2-F2','T2-F3','T2-F4'):
            ff=[v for v in vv if v['family']==family]
            families.append({'model':m,'family':family,**summarize(ff)})
    result=root/'backtesting/location01/results'
    dump(result/'single_cell_transfer.json',{'status':'TRANSFER_DIAGNOSTIC','cards':13,
         'models':single,'no_card_outcome_refit':True,'model_sha256':digest(private/'transfer_models.pkl'),
         'safety_caps':caps,'matched_cards':len(cards)})
    dump(result/'multi_cell_transfer.json',{'status':'TRANSFER_DIAGNOSTIC','cards':11,
         'models':multi,'copula_rank_geometry':'V5.1 unchanged; all model/card geometry guards passed',
         'F1':{m:summarize([v for v in vv if v['family']=='T2-F1']) for m,vv in records.items()}})
    pd.DataFrame(families).to_csv(result/'family_transfer.csv',index=False)
    # No individual card score or truth is written to Git.
    dump(private/'card_transfer_detail.json',records)
    dump(result/'card_transfer_model_audit.json',json.loads((private/'transfer_model_audit.json').read_text()))
    return single,multi,families

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path.cwd())
    p.add_argument('--private',type=Path,required=True);p.add_argument('--card-private',type=Path,required=True)
    a=p.parse_args();evaluate(a.root,a.private,a.card_private)

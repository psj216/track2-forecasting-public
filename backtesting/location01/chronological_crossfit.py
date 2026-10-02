"""## Executive summary (read this first)

Fit four purged outer folds and all precommitted channel models.
Never tune on test CRPS. Freeze card-as-of models before opening card outcomes.
"""
import argparse
import json
import pickle
from pathlib import Path
import numpy as np
import pandas as pd
from qfbench2_track_forecasting.location01.model import FOLDS,LocationModel,purged_mask,choose_alpha
from .negative_controls import CONTROLS,permute_labels,wrong_date_features
from .build_location_ledger import dump

def run(private,card_private):
    rows=pd.read_parquet(private/'ledger.parquet');x=np.load(private/'features.npy')
    schema=json.loads((private/'schema.json').read_text()); y=rows.delta.to_numpy()
    wrong,donors=wrong_date_features(x,rows,schema)
    outputs={k:np.full((6,len(rows)),np.nan) for k in ('ridge','nonlinear',*CONTROLS)}
    folds=np.zeros(len(rows),int);audit=[]
    for fold,(cutoff,start,end) in enumerate(FOLDS,1):
        boundary=f'{start}-01-01'; train=purged_mask(rows,boundary)
        test=((rows.origin>=boundary)&(rows.origin<f'{end+1}-01-01')).to_numpy()
        folds[test]=fold
        entry={'fold':fold,'train_cutoff':cutoff,'test':[start,end],
               'train_rows':int(train.sum()),'test_rows':int(test.sum()),
               'purged_rows':int(((rows.origin<boundary).to_numpy() & ~train).sum()),
               'max_training_maturity':rows.loc[train,'target_end'].max(),
               'latest_training_origin':rows.loc[train,'origin'].max(),'models':{}}
        for m in range(6):
            if m==0:
                for key in outputs:outputs[key][m,test]=0.
                continue
            alpha,details=choose_alpha(x[train],y[train],schema,rows.loc[train].reset_index(drop=True),m,cutoff)
            detail={'alpha':alpha,'selection':details,'caps':{}}
            for key in outputs:
                xx=wrong if key=='B_wrong_feature_date' else x
                yy=permute_labels(rows.loc[train],y[train],key) if key in CONTROLS else y[train]
                a=alpha
                if key in CONTROLS:
                    transform=lambda rr,labels:permute_labels(rr,labels,key)
                    a,_=choose_alpha(xx[train],y[train],schema,rows.loc[train].reset_index(drop=True),m,cutoff,
                                     None if key=='B_wrong_feature_date' else transform)
                fitted=LocationModel(m,key=='nonlinear').fit(xx[train],yy,schema,a)
                prediction,caps=fitted.predict(xx[test]); outputs[key][m,test]=prediction
                detail['caps'][key]=caps
            entry['models'][f'M{m}']=detail
            print(f'crossfit fold {fold} M{m} complete',flush=True)
        audit.append(entry)
    np.savez_compressed(private/'predictions.npz',fold=folds,**outputs)
    dump(private/'crossfit_audit.json',audit)
    # Each card's historical model is fitted only on continuous ledger labels
    # mature before that card's origin. No card outcomes are loaded here.
    # All M1-M5 are frozen; no best-score refitting or transfer tuning occurs.
    cards=json.loads((card_private/'cards.json').read_text());snapshots={};transfer_audit=[]
    for card in cards:
        boundary=card['origin'];train=purged_mask(rows,boundary)
        models={}; info={'card_id':card['id'],'asof':boundary,'training_rows':int(train.sum()),
            'card_labels_used':0,'status':'MATCHED_CONTINUOUS_ASOF_MODEL',
            'max_training_maturity':rows.loc[train,'target_end'].max() if train.any() else None,'models':{}}
        for m in range(1,6):
            if train.sum()<100:
                fitted=LocationModel(0).fit(x[train],y[train],schema)
                info['status']='COLD_START_ZERO'
            else:
                alpha,selection=choose_alpha(x[train],y[train],schema,
                    rows.loc[train].reset_index(drop=True),m,int(boundary[:4])-1)
                fitted=LocationModel(m).fit(x[train],y[train],schema,alpha)
                info['models'][f'M{m}']={'alpha':alpha,'selection':selection}
            models[m]=fitted
        snapshots[card['id']]=models;transfer_audit.append(info)
        print(f'frozen transfer model {card["id"]}',flush=True)
    with (private/'transfer_models.pkl').open('wb') as f:pickle.dump(snapshots,f)
    dump(private/'transfer_model_audit.json',transfer_audit)
    return audit

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private',type=Path,required=True)
    p.add_argument('--card-private',type=Path,required=True);a=p.parse_args();run(a.private,a.card_private)

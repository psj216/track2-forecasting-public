"""## Executive summary (read this first)
Freeze each continuous-history expert before opening card labels, saving every card immediately.
"""
import argparse,json,pickle,time
from pathlib import Path
import numpy as np,pandas as pd
from qfbench2_track_forecasting.expectation01.model import ExpectationModel,choose_alpha,purged_mask
from qfbench2_track_forecasting.context01.expert_transfer import expectation_query,quantity_query
from qfbench2_track_forecasting.context01.context_router import EXPERTS
from .freeze_annotations import dump,digest,verify
def prepare_inputs(root,location,expectation,quantity):
 from backtesting.expectation01.align_location_ledger import verify as verify_location
 verify_location(location)
 for folder,p in [('expectation01',expectation),('positioning01',quantity)]:
  m=json.loads((root/'backtesting'/folder/'results/feature_manifest.json').read_text());assert digest(p/'features_primary.npy')==m['features']['primary'] and digest(p/'schema.json')==m['schema_sha256']
 rows=pd.read_parquet(location/'ledger.parquet');e=np.load(expectation/'features_primary.npy',mmap_mode='r');q=np.load(quantity/'features_primary.npy',mmap_mode='r');es=json.loads((expectation/'schema.json').read_text())['columns'];qs=json.loads((quantity/'schema.json').read_text())['columns']
 return rows,e,q,es,qs
def run(root,private,location,expectation,quantity,card_index):
 verify(root);cards=json.loads((root/'backtesting/context01/results/card_manifest.json').read_text())['cards'];card=cards[card_index];out=private/'experts'/('card'+str(card_index).zfill(2)+'.npz');meta=out.with_suffix('.json')
 if out.exists()and meta.exists():
  assert digest(out)==json.loads(meta.read_text())['prediction_sha256'];print('SAVED '+str(out),flush=True);return
 rows,e,q,es,qs=prepare_inputs(root,location,expectation,quantity);query_rows=[r for r in json.loads((private/'rows.json').read_text())['rows']if r['card_id']==card['id']]
 snapshots=json.loads((expectation/'survey_snapshots.json').read_text());events=json.loads((expectation/'events.json').read_text())['events'];releases=json.loads((quantity/'enriched_releases.json').read_text());ex=expectation_query(query_rows,snapshots,events,es);qx=quantity_query(query_rows,releases,qs)
 train=purged_mask(rows,card['origin']);assert (pd.to_datetime(rows.loc[train,'target_end'])<pd.Timestamp(card['origin'])).all();tr=rows.loc[train].reset_index(drop=True);y=tr.delta.to_numpy();pred=[];raws=[];available=[];audits=[];models={};beg=time.monotonic()
 for name in EXPERTS:
  sourcecols=es if name not in('F','L')else qs;stage=4 if name not in('F','L') else 2;selected=[i for i,c in enumerate(sourcecols)if c['stage']<=stage and(c.get('family')==name if name not in('F','L')else c.get('class_id')==name)];cols=[sourcecols[i]for i in selected];x=np.asarray((e if stage==4 else q)[train][:,selected]);test=(ex if stage==4 else qx)[:,selected]
  alpha,cv=choose_alpha(x,y,cols,tr,stage,int(card['origin'][:4])-1);fit=ExpectationModel(stage).fit(x,y,cols,alpha);raw=fit.predict_raw(test);pred.append(np.clip(raw,-10,10));raws.append(raw);available.append(np.any(test!=0,axis=1));models[name]=dict(model=fit,original_columns=selected)
  audits.append(dict(expert=name,alpha=alpha,inner_cv=cv,training_cells=len(tr),training_active_cells=int(np.any(x!=0,axis=1).sum()),train_max_origin=str(tr.origin.max()),train_max_target_end=str(tr.target_end.max()),query_active_cells=int(np.any(test!=0,axis=1).sum()),cap_hits=int((abs(raw)>10).sum()),source_feature_columns=len(selected),card_labels_consumed=False,fit_spec='Inherited source-family A4 Ridge or F2/L2 Ridge; zero-only omitted columns are algebraically inert; fixed chronological delta-MSE alpha selection'))
  print(json.dumps(dict(stage='matched expert',card=card_index+1,total_cards=24,expert=name,elapsed=round(time.monotonic()-beg,1),artifact=str(out))),flush=True)
 out.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(out,prediction=np.array(pred),raw_prediction=np.array(raws),available=np.array(available));pickle.dump(models,out.with_suffix('.pkl').open('wb'));dump(meta,dict(card_id=card['id'],origin=card['origin'],experts=audits,prediction_sha256=digest(out),model_sha256=digest(out.with_suffix('.pkl')),card_truth_not_loaded=True,annotation_manifest_sha256=digest(root/'backtesting/context01/results/annotation_manifest.json')))
def finalize(root,private,location,expectation,quantity):
 verify(root);entries=[]
 for i in range(24):
  f=private/'experts'/('card'+str(i).zfill(2)+'.json');a=json.loads(f.read_text());assert digest(f.with_suffix('.npz'))==a['prediction_sha256'];entries.append(a)
 dump(root/'backtesting/context01/results/expert_transfer_manifest.json',dict(status='24_MATCHED_ASOF_EXPERT_SETS_FROZEN_BEFORE_CARD_OUTCOMES',cards=entries,admitted_experts=list(EXPERTS),card_label_fit=False,target_maturity='Strictly target_end<card origin plus inherited189BDmaximum-origin embargo',preprocessing='Only continuous training feature values; no card labels; active-only scaling with_mean=False; interceptFalse',source_manifests={n:digest(root/'backtesting'/n/'results/feature_manifest.json')for n in ['expectation01','positioning01']},source_field_limit='H41 field-specific preservation, not untouched historical whole files',transfer_target='Inherited continuous numeric-baseline location delta applied in standardized units to B_TEXT SD; no card-outcome recalibration',unseen_horizons='Inherited exact horizon interactions remain zero at unmatched64/127etc; no snapping or feature retuning'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--private',type=Path,required=True);p.add_argument('--location',type=Path,required=True);p.add_argument('--expectation',type=Path,required=True);p.add_argument('--quantity',type=Path,required=True);p.add_argument('--card-index',type=int);p.add_argument('--finalize',action='store_true');a=p.parse_args()
 if a.finalize:finalize(a.root,a.private,a.location,a.expectation,a.quantity)
 else:run(a.root,a.private,a.location,a.expectation,a.quantity,a.card_index)

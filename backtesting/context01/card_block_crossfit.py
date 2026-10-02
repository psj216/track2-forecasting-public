"""## Executive summary (read this first)
Score no cards during fitting; save each entire held-out card/family immediately after verified PRE.
"""
import argparse,json,pickle,subprocess,time
from pathlib import Path
import numpy as np,pandas as pd
from qfbench2_track_forecasting.context01.semantic_model import fit_fold
from qfbench2_track_forecasting.context01.deterministic_annotator import matrix
from qfbench2_track_forecasting.context01.residual_target import residual
from .freeze_annotations import verify,digest,dump
from .negative_controls import controlled_annotations
KEYS=['B'+str(i)for i in range(1,6)]+['CTRL_'+c+'_B'+str(i)for c in 'ABD'for i in range(1,6)]
def checked_labels(root,private,card_private,pre):
 verify(root);receipt=json.loads((private/'pre_result_remote_verified.json').read_text());assert receipt['PRE_RESULT_CONTEXT01_SHA']==pre and receipt['remote_verified'] and subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==pre
 cards=json.loads((root/'backtesting/context01/results/card_manifest.json').read_text())['cards'];y=[]
 for c in cards:
  assert digest(card_private/c['file'])==c['sha256']
  with np.load(card_private/c['file'])as z:truth=z['truth']
  text=np.load(private/'baselines'/(c['id']+'_baseline.npy'));y.extend(residual(text,truth).ravel().tolist())
 return cards,np.array(y)
def design(root,private,control=None):
 cards=json.loads((root/'backtesting/context01/results/card_manifest.json').read_text())['cards'];annotations=json.loads((root/'backtesting/context01/results/context_annotations.json').read_text())['cards']
 if control:annotations=controlled_annotations(cards,annotations,control)
 x,rows,cols=matrix(cards,annotations)
 if control is None:assert np.array_equal(x,np.load(private/'context_features.npy'))
 return cards,x,rows,cols
def run(root,private,card_private,pre,mode,index):
 cards,y=checked_labels(root,private,card_private,pre);_,x,rows,cols=design(root,private);ids=np.array([r['card_id']for r in rows]);families=np.array([r['family']for r in rows]);protocol=json.loads((root/'backtesting/context01/frozen_protocol.json').read_text())
 if mode=='loco':test=ids==cards[index]['id'];train=~test;label=cards[index]['id']
 elif mode=='family':label=['T2-F1','T2-F2','T2-F3','T2-F4'][index];test=families==label;train=~test
 else:
  split=protocol['chronological_splits'][index];label=split['boundary'];test=np.isin(ids,split['test_cards']);train=np.isin(ids,split['train_cards'])
 if not train.any():raise ValueError('Empty frozen training split')
 assert not(set(ids[train])&set(ids[test]));out=private/'crossfit'/f'{mode}_{index:02d}.npz';meta=out.with_suffix('.json')
 if out.exists()and meta.exists():assert digest(out)==json.loads(meta.read_text())['sha256'];print('SAVED '+str(out),flush=True);return
 result={};audit={};beg=time.monotonic()
 for key in KEYS:
  stage=int(key[-1]);control=key.split('_')[1]if key.startswith('CTRL')else None
  xx=x if control is None else design(root,private,control)[1];selected=[i for i,s in enumerate(cols)if s['stage']<=stage];raw,fit,alpha,cv=fit_fold(xx[:,selected],y,ids,train,test);result[key]=np.clip(raw,-10,10);audit[key]=dict(alpha=alpha,inner_cv=cv,cap_hits=int((abs(raw)>10).sum()),features=len(selected),fit_intercept=False,scaler='Training-only StandardScaler with_mean=False',train_cards=len(set(ids[train])),test_cards=len(set(ids[test])),training_card_ids=sorted(set(ids[train])),held_out_card_ids=sorted(set(ids[test])))
  out.parent.mkdir(parents=True,exist_ok=True);pickle.dump(dict(fit=fit,columns=selected),out.with_name(out.stem+'_'+key+'.pkl').open('wb'));print(json.dumps(dict(stage='semantic crossfit',mode=mode,heldout=label,model=key,elapsed=round(time.monotonic()-beg,1),artifact=str(out))),flush=True)
 np.savez_compressed(out,row_index=np.flatnonzero(test),**result);dump(meta,dict(pre_result_sha=pre,mode=mode,heldout=label,models=audit,sha256=digest(out),no_same_card_leakage=True,card_labels='Training residual targets only; never annotation/router/source preprocessing',elapsed=time.monotonic()-beg))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--private',type=Path,required=True);p.add_argument('--card-private',type=Path,required=True);p.add_argument('--pre-result-sha',required=True);p.add_argument('--mode',choices=['loco','family','chrono'],required=True);p.add_argument('--index',type=int,required=True);a=p.parse_args();run(a.root,a.private,a.card_private,a.pre_result_sha,a.mode,a.index)

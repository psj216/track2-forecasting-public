"""## Executive summary (read this first)
Recompute all baseline/text/location components on each card only after PRE validation.
"""
import argparse,json,pickle,time
from pathlib import Path
import numpy as np
from qfbench2_track_forecasting.ceiling01.scorer_adapter import components,score
from qfbench2_track_forecasting.ceiling01.joint_oracle import apply as joint_oracle
from qfbench2_track_forecasting.context01.engine import apply,geometry_guard
from qfbench2_track_forecasting.context01.text_effect import location_only,standardized_shift
from qfbench2_track_forecasting.context01.residual_target import residual
from qfbench2_track_forecasting.context01.context_router import EXPERTS,route
from .card_block_crossfit import checked_labels,KEYS
from .negative_controls import controlled_annotations
from .freeze_annotations import dump,digest
MAIN_MODELS=['B0','B1','B2','B3','B4','B5','R0','R1','R2','R3']
ROUTE_CONTROLS=['CTRL_'+c+'_R'+str(i)for c in 'ABCD'for i in range(1,4)]
MODELS=MAIN_MODELS+[k for k in KEYS if k.startswith('CTRL')]+ROUTE_CONTROLS+['B_NUMERIC','TEXT_LOCATION']
def predictions(private,cards,rows,mode):
 ids=np.array([r['card_id']for r in rows]);out={k:np.zeros(len(rows))for k in KEYS};found=np.zeros(len(rows),bool);audits=[]
 for f in sorted((private/'crossfit').glob(mode+'_*.npz')):
  audit=json.loads(f.with_suffix('.json').read_text());assert digest(f)==audit['sha256'];audits.append(audit)
  with np.load(f)as z:
   ix=z['row_index'];assert not found[ix].any();found[ix]=True
   for k in out:out[k][ix]=z[k]
 if mode!='chrono'and not found.all():raise ValueError('Incomplete '+mode+' predictions')
 return out,found,audits
def run(root,private,card_private,pre,index,mode='loco'):
 cards,_=checked_labels(root,private,card_private,pre);card=cards[index];rows=json.loads((private/'rows.json').read_text())['rows'];out=private/'scored'/f'{mode}_card{index:02d}.json'
 if out.exists():print('SAVED '+str(out),flush=True);return
 fitted,found,audits=predictions(private,cards,rows,mode);ix=np.flatnonzero(np.array([r['card_id']for r in rows])==card['id'])
 if not found[ix].all():
  if mode=='chrono':return
  raise ValueError('Card prediction missing')
 text=np.load(private/'baselines'/(card['id']+'_baseline.npy'));numeric=np.load(private/'baselines'/(card['id']+'_numeric.npy'))
 with np.load(card_private/card['file'])as z:truth=z['truth']
 baseline=components(text,truth);perfect=text+(truth-np.median(text,axis=0));assert geometry_guard(text,perfect);oracle=score(perfect,truth,baseline)
 with np.load(private/'experts'/f'card{index:02d}.npz')as z:
  expert={k:z['prediction'][j]for j,k in enumerate(EXPERTS)};available={k:z['available'][j]for j,k in enumerate(EXPERTS)}
 annotations=json.loads((root/'backtesting/context01/results/context_annotations.json').read_text())['cards'];assets=[r['asset']for r in np.array(rows,dtype=object)[ix]];one,mean,coverage,choices=route(annotations[card['id']]['economic_topics'],assets,expert,available);_,rotated,_,_=route(annotations[card['id']]['economic_topics'],assets,expert,available,permuted=True)
 delta={k:v[ix]for k,v in fitted.items()};delta.update(B0=np.zeros(len(ix)),R0=np.zeros(len(ix)),R1=one,R2=mean,R3=.5*(delta['B5']+mean))
 rotated_one,rotated,_,_=route(annotations[card['id']]['economic_topics'],assets,expert,available,permuted=True)
 for control in 'ABD':
  controlled=controlled_annotations(cards,annotations,control);co,cm,_,_=route(controlled[card['id']]['economic_topics'],assets,expert,available)
  delta['CTRL_'+control+'_R1']=co;delta['CTRL_'+control+'_R2']=cm;delta['CTRL_'+control+'_R3']=.5*(delta['CTRL_'+control+'_B5']+cm)
 delta.update(CTRL_C_R1=rotated_one,CTRL_C_R2=rotated,CTRL_C_R3=.5*(delta['B5']+rotated))
 scores={};beg=time.monotonic()
 for key in MODELS:
  candidate=numeric if key=='B_NUMERIC'else(location_only(text,numeric)if key=='TEXT_LOCATION'else apply(text,delta[key]))
  if key=='TEXT_LOCATION':assert geometry_guard(numeric,candidate)
  scores[key]=score(candidate,truth,baseline)
 if mode=='loco'and card['cells']>1:
  # Feasible hindsight permutation only. Never applied to learned candidates.
  joint,jointaudit=joint_oracle(perfect,truth,proposals=12000,seed=1901);jointscore=score(joint,truth,baseline)
 else:jointscore=None;jointaudit=None
 record=dict(card_id=card['id'],family=card['family'],origin=card['origin'],cells=card['cells'],single=card['cells']==1,baseline=baseline,models=scores,oracle=oracle,location_joint_oracle=jointscore,joint_oracle_audit=jointaudit,residual_delta=residual(text,truth).ravel().tolist(),prediction={k:v.tolist()for k,v in delta.items()},text_effect=dict(z_shift=standardized_shift(text,numeric).ravel().tolist(),numeric_oracle_delta=residual(numeric,truth).ravel().tolist(),numeric_perfect_location=score(numeric+(truth-np.median(numeric,axis=0)),truth,baseline)),route=dict(active_cells=int(coverage.sum()),active=coverage.tolist(),eligible=choices),mode=mode,pre_result_sha=pre,draw_geometry='PASS; learned text-baseline shifts and perfect residual shift preserve paired centered draws',elapsed=time.monotonic()-beg)
 dump(out,record);print(json.dumps(dict(stage='card scoring',mode=mode,card=index+1,total=24,elapsed=round(time.monotonic()-beg,1),artifact=str(out))),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--private',type=Path,required=True);p.add_argument('--card-private',type=Path,required=True);p.add_argument('--pre-result-sha',required=True);p.add_argument('--index',type=int,required=True);p.add_argument('--mode',choices=['loco','family','chrono'],default='loco');a=p.parse_args();run(a.root,a.private,a.card_private,a.pre_result_sha,a.index,a.mode)

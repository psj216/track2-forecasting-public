"""## Executive summary (read this first)
After verified PRE, choose a whole frozen card, crossfit small routers, and rescore original components.
"""
import argparse,json,pickle,subprocess,time
from pathlib import Path
import numpy as np
from sklearn.metrics import accuracy_score,balanced_accuracy_score,brier_score_loss,log_loss,roc_auc_score
from scipy.stats import pearsonr,spearmanr
from backtesting.context01.freeze_annotations import dump,digest
from qfbench2_track_forecasting.ceiling01.scorer_adapter import aggregate,score
from .models import MODELS,predict,route,folds,training_shuffle
PARENT='d3618dcd9aae4ac118a5c12c0fe8f3709a72f296'
def inputs(root,private,guard=True):
 m=json.loads((root/'backtesting/text_route_audit02/results/feature_manifest.json').read_text());assert digest(private/'features.npz')==m['feature_sha256']
 if guard:
  receipt=json.loads((private/'pre_remote_receipt.json').read_text());assert receipt['remote_verified']and subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==receipt['PRE_RESULT_SHA']
  for name,h in receipt['frozen_hashes'].items():assert digest(root/name)==h,name
 cards=json.loads((private/'cards.json').read_text())['cards'];records=json.loads((private/'frozen_parent_records.json').read_text())['records'];x={k:v for k,v in np.load(private/'features.npz').items()};ratios=np.array([r['models']['R2']['ratio']for r in records]);y=(ratios<1).astype(int);g=np.log(ratios)
 return cards,records,x,y,g

def stats(records,chosen):
 chosen=np.asarray(chosen,bool);assert chosen.shape==(len(records),);ratio=[r['models']['R2']['ratio']if z else 1. for r,z in zip(records,chosen)];out=dict(cards=len(records),composite=aggregate(ratio),arithmetic=float(np.mean(ratio)),routed_R2=int(chosen.sum()),application_fraction=float(chosen.mean()))
 for k in ['marginal','joint','tail']:
  out[k]=aggregate([(r['models']['R2'][k]if z else r['baseline'][k])/r['baseline'][k]for r,z in zip(records,chosen)if r['baseline'][k]>1e-12])
 return out

def grouped(cards,records,chosen):
 def sub(mask):return stats([r for r,t in zip(records,mask)if t],np.asarray(chosen)[mask])
 single=np.array([c['cells']==1 for c in cards]);out=stats(records,chosen);out['single']=sub(single);out['multi']=sub(~single);out['family']={f:sub(np.array([c['family']==f for c in cards]))for f in ['T2-F'+str(i)for i in range(1,5)]}
 return out

def classification(y,p,chosen,g,gain=None):
 o=dict(route_accuracy=float(accuracy_score(y,chosen)),balanced_accuracy=float(balanced_accuracy_score(y,chosen)),route_positive_cards=int(y.sum()),gain_regression=None)
 if gain is None:o.update(brier=float(brier_score_loss(y,p)),log_loss=float(log_loss(y,np.clip(p,1e-12,1-1e-12),labels=[0,1])),roc_auc=float(roc_auc_score(y,p))if len(set(y))==2 else None)
 else:o.update(brier=None,log_loss=None,roc_auc=None,gain_regression=dict(mse=float(np.mean((g-gain)**2)),pearson=float(pearsonr(g,gain).statistic)if np.std(gain)>1e-12 else None,spearman=float(spearmanr(g,gain).statistic)if np.std(gain)>1e-12 else None))
 return o

def oracle(root,private):
 cards,records,x,y,g=inputs(root,private);summary=grouped(cards,records,y);summary.update(routing_headroom=1-summary['composite'],oracle_choices='Whole-card E0 or E1; strict full composite comparison; ties choose E0',descriptive_only=True,headroom_by_group={k:1-summary[k]['composite']for k in ['single','multi']},family_headroom={f:1-v['composite']for f,v in summary['family'].items()})
 dump(root/'backtesting/text_route_audit02/results/oracle_route_summary.json',summary);dump(private/'route_targets.json',dict(y=y.tolist(),gain=g.tolist(),R2_ratios=np.exp(g).tolist(),card_ids=[c['id']for c in cards]));print(json.dumps(dict(stage='oracle',composite=summary['composite'],headroom=summary['routing_headroom'])),flush=True)

def crossfit(root,private,mode,index,card_private):
 cards,records,x,y,g=inputs(root,private);label,train,test=folds(cards,mode)[index];out=private/'crossfit'/f'{mode}_{index:02d}.json'
 if out.exists():return
 assert not(set(train)&set(test));models={};beg=time.monotonic()
 for key,(feature,kind)in MODELS.items():
  p,gain,fit=predict(x[feature],y,g,train,test,kind);chosen=route(p,kind);components=[]
  for j,on in zip(test,chosen):
   with np.load(private/'frozen_forecasts'/f'card{j:02d}.npz')as z:draw=z['E1'if on else'E0']
   with np.load(card_private/cards[j]['file'])as z:truth=z['truth']
   actual=score(draw,truth,records[j]['baseline']);expected=records[j]['models']['R2'if on else'B0'];assert actual==expected,(key,int(j));components.append(actual)
  models[key]=dict(probability=p.tolist()if kind=='logistic'else None,gain_prediction=None if gain is None else gain.tolist(),chosen_R2=chosen.tolist(),rescored=components,feature=feature,kind=kind)
  out.parent.mkdir(parents=True,exist_ok=True);pickle.dump(fit,out.with_name(out.stem+'_'+key+'.pkl').open('wb'))
 maj=int(y[train].mean()>.5);models['MAJORITY']=dict(probability=[float(maj)]*len(test),gain_prediction=None,chosen_R2=[bool(maj)]*len(test),training_cards=len(train))
 dump(out,dict(mode=mode,index=index,label=label,train=train.tolist(),test=test.tolist(),models=models,train_only_preprocessing=True,elapsed=time.monotonic()-beg));print(json.dumps(dict(stage='crossfit',mode=mode,fold=index+1,heldout=label,artifact=str(out))),flush=True)

def control_chunk(root,private,kind,start,stop):
 cards,records,x,y,g=inputs(root,private);out=private/'controls'/f'{kind}_{start:04d}_{stop:04d}.npz'
 if out.exists():return
 values=[];choices=[];beg=time.monotonic();splits=folds(cards,'loco')
 for i in range(start,stop):
  rng=np.random.default_rng((2202 if kind=='label'else 2203)+i);perm=rng.permutation(24);yy=y[perm]if kind=='label'else y;gg=g[perm]if kind=='label'else g;xx=x['ST0']if kind=='label'else np.column_stack([x['S0'],x['T0'][perm]]);selected=np.zeros(24,bool)
  for _,tr,te in splits:
   training_y,training_g=training_shuffle(y,g,tr,rng)if kind=='label'else(yy,gg)
   p,_,_=predict(xx,training_y,training_g,tr,te);selected[te]=route(p)
  values.append(stats(records,selected)['composite']);choices.append(selected)
  if(i-start+1)%25==0:print(json.dumps(dict(stage='controls',kind=kind,completed=i+1,total=2000,elapsed=round(time.monotonic()-beg,1),artifact=str(out))),flush=True)
 out.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(out,composite=values,route=choices);dump(out.with_suffix('.json'),dict(kind=kind,start=start,stop=stop,seed_base=2202 if kind=='label'else 2203,sha256=digest(out)))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--private',type=Path,required=True);p.add_argument('--stage',choices=['oracle','crossfit','controls'],required=True);p.add_argument('--mode',choices=['loco','family'],default='loco');p.add_argument('--index',type=int,default=0);p.add_argument('--card-private',type=Path);p.add_argument('--kind',choices=['label','text']);p.add_argument('--start',type=int,default=0);p.add_argument('--stop',type=int,default=100);a=p.parse_args()
 if a.stage=='oracle':oracle(a.root,a.private)
 elif a.stage=='crossfit':crossfit(a.root,a.private,a.mode,a.index,a.card_private)
 else:control_chunk(a.root,a.private,a.kind,a.start,a.stop)

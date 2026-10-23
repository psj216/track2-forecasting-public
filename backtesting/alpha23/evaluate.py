"""Executive summary: separate label-side paired UST evaluation with unchanged official loss imports."""
import sys,pathlib,json,hashlib,tomllib
import numpy as np,pandas as pd
sys.path.insert(0,str(pathlib.Path(__file__).parent/'reused'))
from loss_helpers import metrics,matrix
from m0 import reconstruct,scales
from qfbench2_track_forecasting.grid import grid_from_card
from policy_signal import features as policy_features

def aggregate(rows):
 out={'origins':len(rows)}
 for n in ['ff03','full','ablation','m0']:
  out[n]={'score':float(np.mean([r[n]['score'] for r in rows])),'normalized':{k:float(np.mean([r[n]['normalized'][k] for r in rows])) for k in ['marginal','joint','tail']},'raw':{k:float(np.mean([r[n]['raw'][k] for r in rows])) for k in ['marginal','joint','tail']},'coverage90':float(np.mean([r[n]['coverage90'] for r in rows])),'coverage98':float(np.mean([r[n]['coverage98'] for r in rows]))}
 out['ff03_minus_full']=out['ff03']['score']-out['full']['score'];out['ablation_minus_full']=out['ablation']['score']-out['full']['score'];return out

def run(root,artifacts,out):
 root=pathlib.Path(root);artifacts=pathlib.Path(artifacts);out=pathlib.Path(out);p=pd.read_parquet(root/'data/curve.parquet');rows=[];missing=[];unitmanifest=json.loads((root/'inputs/input-manifest.json').read_text())
 for ent in unitmanifest['inputs']:
  name=ent['id'];unit=root/'inputs'/name;date=pd.Timestamp(ent['origin']);card=tomllib.loads((unit/'card.toml').read_text());cells=grid_from_card(card).cells()
  files=list(artifacts.glob('**/'+name+'/forecast.parquet'));assert len(files)==1,(name,len(files));f=files[0];receipt=json.loads(f.with_name('receipt.json').read_text());assert receipt['ff03_exit']==receipt['candidate_exit']==0
  assert ent['files']==receipt['input_hashes'],('input bytes differ',name)
  for fn,digest in receipt['output_hashes'].items():assert hashlib.sha256(f.with_name(fn).read_bytes()).hexdigest()==digest
  absent=[(a,h) for a,h in cells if date+pd.offsets.BDay(h) not in p.index or pd.isna(p.loc[date+pd.offsets.BDay(h),a])]
  if absent:missing.append({'id':name,'missing':absent});continue
  y=np.array([p.loc[date+pd.offsets.BDay(h),a] for a,h in cells]);anchor=np.array([p.loc[date,a] for a,h in cells]);d=reconstruct(unit);scale=scales(d.mean,d.covariance)
  models={'ff03':matrix(f,cells),'full':np.load(f.with_name('full.npy')),'ablation':np.load(f.with_name('ablation.npy')),'m0':d.samples}
  # Adapter arrays follow the same declared asset-major grid; assert before scoring.
  assert cells==tuple((a,h) for a in card['targets']['asset_ids'] for h in [1,2,3,4])
  assert models['ff03'].shape==models['full'].shape==models['ablation'].shape==(1000,36)
  rec={'id':name,'origin':ent['origin'],'event':bool(policy_features(pd.DatetimeIndex([date]),[]).iloc[0].policy_scheduled_event4),'scales':scale,'subsets':{},'direction':{},'center_rmse':{},'timing':{'ff03':receipt['ff03_wall_seconds'],'full_and_ablation':receipt['candidate_wall_seconds']}}
  for n,x in models.items():
   assert np.isfinite(x).all();rec[n]=metrics(x,y,scale);rec['direction'][n]=float(np.mean(np.sign(x.mean(axis=0)-anchor)==np.sign(y-anchor)));rec['center_rmse'][n]=float(np.sqrt(np.mean((x.mean(axis=0)-y)**2)))
  for key,ix in [(f'asset:{a}',[i for i,c in enumerate(cells) if c[0]==a]) for a in card['targets']['asset_ids']]+[(f'horizon:{h}',[i for i,c in enumerate(cells) if c[1]==h]) for h in [1,2,3,4]]:
   ss=scales(d.mean[ix],d.covariance[np.ix_(ix,ix)]);rec['subsets'][key]={n:metrics(x[:,ix],y[ix],ss)['score'] for n,x in models.items()}
  rows.append(rec);out.write_text(json.dumps({'partial':True,'summary':aggregate(rows),'cards':rows,'missing':missing},indent=2))
  if len(rows)%10==0:print('scored',len(rows),flush=True)
 gains=np.array([r['ff03']['score']-r['full']['score'] for r in rows]);pol=np.array([r['ablation']['score']-r['full']['score'] for r in rows]);rng=np.random.default_rng(23023);bs=[];bp=[]
 for _ in range(2000):
  ix=np.concatenate([(i+np.arange(4))%len(rows) for i in rng.integers(0,len(rows),size=(len(rows)+3)//4)])[:len(rows)];bs.append(gains[ix].mean());bp.append(pol[ix].mean())
 grouped={}
 for key in sorted(set(r['origin'][:4] for r in rows)):grouped['year:'+key]=aggregate([r for r in rows if r['origin'].startswith(key)])
 for key in sorted(set(r['origin'][:4]+'Q'+str(pd.Timestamp(r['origin']).quarter) for r in rows)):grouped[key]=aggregate([r for r in rows if r['origin'][:4]+'Q'+str(pd.Timestamp(r['origin']).quarter)==key])
 for event in [True,False]:
  rr=[r for r in rows if r['event']==event]
  if rr:grouped['event:'+str(event)]=aggregate(rr)
 result={'executive_summary':'Paired same-byte-input original FF03 Docker vs independent trained full/ablation. Current-vintage exploratory, not authenticated Final score.','summary':aggregate(rows),'requested':unitmanifest['requested_origins'],'forecasted':len(unitmanifest['inputs']),'missing_origins':unitmanifest['missing_origin_observations'],'missing_targets':missing,'ci95_gain':np.quantile(bs,[.025,.975]).tolist(),'ci95_policy_gain':np.quantile(bp,[.025,.975]).tolist(),'best_origin_removed_gain':float(np.delete(gains,np.argmax(gains)).mean()),'worst_origin_gain':float(gains.min()),'grouped':grouped,'cards':rows}
 out.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='cards'},indent=2))
if __name__=='__main__':run(*sys.argv[1:])

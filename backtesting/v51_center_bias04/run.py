"""Executive summary: bounded, restartable audit of byte-frozen baseline distributions."""
import argparse,json,time
import numpy as np,pandas as pd
from numpy.lib.format import open_memmap
from qfbench2_common.scoring.crps import crps_ensemble
from .core import *

def load():return pd.read_parquet(private()/'center_error_ledger.parquet')
def score(rows,indices,delta):
 draws=np.load(private()/'draws.npy',mmap_mode='r');ii=np.asarray(indices);shift=np.broadcast_to(delta,len(ii));out=np.empty(len(ii))
 for n in np.unique(rows.iloc[ii].n_draws):
  jj=np.flatnonzero(rows.iloc[ii].n_draws.to_numpy()==n)
  for start in range(0,len(jj),512):
   k=jj[start:start+512];v=ii[k];ref=rows.iloc[v]
   out[k]=crps_ensemble(np.asarray(draws[:int(n),v])+shift[k]*ref['sd'].to_numpy(),ref.truth.to_numpy())/ref.scale.to_numpy()
 return out

def construct(start,stop):
 verify();rows=pd.read_parquet(private()/'canonical/ledger.parquet');assert rows.target_end.max()<='2024-12-18';assert rows.sd.gt(0).all()
 N=len(rows);fp=private()/'draws.npy';draws=open_memmap(fp,mode='r+' if fp.exists() else 'w+',dtype='float64',shape=(1000,N));manifest=json.loads((ROOT/'backtesting/location01/results/ledger_manifest.json').read_text());hashes=manifest['baseline_cache_sha256'];origins=sorted(rows.origin.unique());t=time.monotonic()
 folder=private()/'construction';folder.mkdir(exist_ok=True)
 for block in range(start,min(stop,len(origins)),25):
  file=folder/f'{block:04d}.npz'
  if file.exists():continue
  select=origins[block:min(block+25,len(origins))];ii=np.flatnonzero(rows.origin.isin(select));chunks=[]
  for stamp,frame in rows.iloc[ii].groupby('origin',sort=True):
   path=private()/'canonical/origins'/f'{stamp}.npz';assert digest(path)==hashes[str(path.name)]
   with np.load(path) as z:
    for asset,a in frame.groupby('asset',sort=True):
     ids=a.index.to_numpy();x=z[asset][:,[HORIZONS.index(int(h))for h in a.horizon]]
     assert np.allclose(np.median(x,axis=0),a['median'],rtol=1e-13,atol=1e-14);assert np.allclose(x.std(axis=0),a.sd,rtol=1e-13,atol=1e-14)
     draws[:,ids]=np.nan;draws[:len(x),ids]=x
  draws.flush()
  zero=score(rows,ii,0.);perfect=score(rows,ii,(rows.iloc[ii].truth.to_numpy()-rows.iloc[ii]['median'].to_numpy())/rows.iloc[ii].sd.to_numpy());up=score(rows,ii,.05);down=score(rows,ii,-.05)
  np.savez_compressed(file,indices=ii,baseline=zero,perfect=perfect,up=up,down=down)
  print('construction',min(block+25,len(origins)),'/',len(origins),'elapsed',round(time.monotonic()-t,1),'origin',select[-1],'output',file,flush=True)
 status('construction_progress',str(file),pending_stages=['construction_remaining','bias','crossfit','oracles','controls','bootstrap','decision','tests','publication','recovery'])

def merge():
 verify();rows=pd.read_parquet(private()/'canonical/ledger.parquet');N=len(rows);arrays={k:np.full(N,np.nan)for k in ['baseline','perfect','up','down']};covered=np.zeros(N,int)
 for f in sorted((private()/'construction').glob('*.npz')):
  z=np.load(f);ii=z['indices'];covered[ii]+=1
  for k in arrays:arrays[k][ii]=z[k]
 assert np.all(covered==1);assert all(np.isfinite(x).all()for x in arrays.values())
 np.savez_compressed(private()/'base_losses.npz',**arrays)
 rows['asset_group']=rows['group'];rows['year']=pd.to_datetime(rows.origin).dt.year;rows['era']=rows.year.map(era);rows['raw_center_error']=rows.truth-rows['median'];rows['standardized_center_error']=rows.raw_center_error/rows.sd;rows['direction']=np.sign(rows.raw_center_error);rows['baseline_CRPS']=arrays['baseline'];rows['V5.1_median']=rows['median'];rows['V5.1_SD']=rows.sd
 rows.to_parquet(private()/'center_error_ledger.parquet',index=False)
 # Future-informed residuals used only by the isolated oracle stage.
 d=np.load(private()/'draws.npy',mmap_mode='r');z=open_memmap(private()/'residuals.npy',mode='w+',dtype='float64',shape=d.shape)
 for a in range(0,N,1024):b=min(a+1024,N);z[:,a:b]=(rows.truth.to_numpy()[a:b]-d[:,a:b])/rows.sd.to_numpy()[a:b]
 z.flush();save(OUT/'center_error_ledger_manifest.json',dict(executive_summary='Private realized targets; public aggregates only.',path='private/center_error_ledger.parquet',SHA256=digest(private()/'center_error_ledger.parquet'),cells=N,draws_reused_exactly=True,target_reconstructed=False,SD_floor_cells=int((rows.sd<1e-8).sum()),original_label_max_difference=float(np.max(np.abs(rows.delta-rows.standardized_center_error))),original_semantics='LOCATION01 target/oracle_label unchanged; level endpoint; accumulated daily return/log-return; original scale denominator retained.'))
 status('baseline_error_construction','center_error_ledger_manifest.json')

def chronological():
 verify();rows=load();base=np.load(private()/'base_losses.npz');N=len(rows);losses={k:np.full(N,np.nan)for k in PREDICTIVE};folds=np.zeros(N,int);shifts={k:np.full(N,np.nan)for k in PREDICTIVE};records=[];params={}
 folder=private()/'folds';folder.mkdir(exist_ok=True)
 for fold,tr,te,boundary in partitions(rows):
  f=folder/f'{fold}.npz';g=folder/f'{fold}.json'
  if f.exists() and g.exists():z=np.load(f);p=json.loads(g.read_text());p['horizon_sign']={int(k):v for k,v in p['horizon_sign'].items()}
  else:
   p=train_bias(rows,tr);ss=predicted_shifts(rows,te,p);ll={}
   for k in PREDICTIVE:
    if k=='GLOBAL_MEDIAN_SHIFT':ll[k]=score(rows,te,ss[k])
    else:ll[k]=np.where(ss[k]>0,base['up'][te],np.where(ss[k]<0,base['down'][te],base['baseline'][te]))
   np.savez_compressed(f,train=tr,test=te,**ll,**{'shift_'+k:v for k,v in ss.items()});save(g,p);z=np.load(f)
  params[fold]=p;assert np.array_equal(z['train'],tr)and np.array_equal(z['test'],te);folds[te]=fold
  for k in PREDICTIVE:losses[k][te]=z[k];shifts[k][te]=z['shift_'+k]
  tb=bias(rows.iloc[te]);records.append(dict(fold=fold,boundary=boundary,train_cells=len(tr),test_cells=len(te),train_last_origin=rows.iloc[tr].origin.max(),train_last_maturity=rows.iloc[tr].target_end.max(),test_start=rows.iloc[te].origin.min(),test_end=rows.iloc[te].origin.max(),train_sign=p['global_sign'],train_mean_sign=p['global_mean_sign'],test_median_sign=float(np.sign(tb['median_raw_error'])),test_mean_sign=float(np.sign(tb['mean_raw_error'])),test_majority_sign=float(np.sign(tb['positive_fraction']-tb['negative_fraction'])),same_median=p['global_sign']==np.sign(tb['median_raw_error']),same_mean=p['global_mean_sign']==np.sign(tb['mean_raw_error']),same_majority=p['global_sign']==np.sign(tb['positive_fraction']-tb['negative_fraction']),requested_median=p['median_requested'],capped_median=p['median_capped'],**{k:ratio(losses[k][te],base['baseline'][te])for k in PREDICTIVE}));print('fold',fold,'complete',len(te),flush=True)
 np.savez_compressed(private()/'chronological.npz',fold=folds,**losses,**{'shift_'+k:v for k,v in shifts.items()});save(private()/'fold_params.json',params);csv('chronological_bias_persistence.csv',records)
 mask=folds>0
 for k,name in zip(PREDICTIVE,['global_sign005_summary.json','asset_sign005_summary.json','horizon_sign005_summary.json','global_median_shift_summary.json']):
  summary=dict(executive_summary='RESEARCH_DIAGNOSTIC_ONLY. Complete chronological 2010–2024 test ledger; no candidate.',model=k,cells=int(mask.sum()),origins=int(rows[mask].origin.nunique()),ratio=ratio(losses[k][mask],base['baseline'][mask]),folds_improved=sum(a[k]<1 for a in records),fraction_improved=float(np.mean(losses[k][mask]<base['baseline'][mask])),requested_magnitude_by_fold=[a['requested_median']for a in records]if k=='GLOBAL_MEDIAN_SHIFT'else None)
  save(OUT/name,summary)
 status('chronological_predictive_bias','chronological_bias_persistence.csv')

def oracles(universe,kind):
 verify();from .oracle import minimum_location
 rows=load();ev=np.load(private()/'chronological.npz')['fold']>0;sel=np.ones(len(rows),bool)if universe=='full'else ev
 groups={'GLOBAL_ORACLE_BIAS':np.repeat('global',len(rows)),'YEAR_ORACLE_BIAS':rows.year.astype(str).to_numpy(),'ASSET_ORACLE_BIAS':rows.asset.to_numpy(),'HORIZON_ORACLE_BIAS':rows.horizon.astype(str).to_numpy(),'ASSET_HORIZON_ORACLE_BIAS':(rows.asset+'|'+rows.horizon.astype(str)).to_numpy()}[kind]
 z=np.load(private()/'residuals.npy',mmap_mode='r');folder=private()/'oracles'/universe/kind;folder.mkdir(parents=True,exist_ok=True);allg=np.unique(groups[sel]);t=time.monotonic()
 for j,key in enumerate(allg):
  f=folder/f'{j:03d}.npz';g=folder/f'{j:03d}.json'
  if f.exists()and g.exists():continue
  ii=np.flatnonzero(sel&(groups==key));ref=rows.iloc[ii];delta,audit=minimum_location(np.asarray(z[:,ii]),ref.sd.to_numpy(),ref.scale.to_numpy(),ref.n_draws.to_numpy());loss=score(rows,ii,delta);np.savez_compressed(f,indices=ii,loss=loss);save(g,dict(group=str(key),cells=len(ii),oracle_delta=delta,**audit));print('oracle',universe,kind,j+1,'/',len(allg),'elapsed',round(time.monotonic()-t,1),'output',f,flush=True)
 loss=np.full(len(rows),np.nan)
 for f in sorted(folder.glob('*.npz')):a=np.load(f);loss[a['indices']]=a['loss']
 assert np.isfinite(loss[sel]).all();np.save(private()/f'oracle_{universe}_{kind}.npy',loss);status('oracle_'+universe+'_'+kind,str(folder))

def controls(kind,start,stop):
 verify();rows=load();cc=np.load(private()/'chronological.npz');mask=cc['fold']>0;base=np.load(private()/'base_losses.npz');view=rows.loc[mask,['origin','asset','horizon','year']].copy();view['fold']=cc['fold'][mask];params=json.loads((private()/'fold_params.json').read_text());params={int(k):{**v,'horizon_sign':{int(a):b for a,b in v['horizon_sign'].items()}}for k,v in params.items()};sg=np.sign(cc['shift_GLOBAL_BIAS_SIGN005'][mask]);folder=private()/'controls'/str(kind);folder.mkdir(parents=True,exist_ok=True)
 for a in range(start,stop,100):
  f=folder/f'{a:04d}.npz'
  if f.exists():continue
  results=[]
  for rep in range(a,min(a+100,stop)):
   s=random_directions(view,params,sg,kind,rep);loss=np.where(s>0,base['up'][mask],np.where(s<0,base['down'][mask],base['baseline'][mask]));results.append(ratio(loss,base['baseline'][mask]))
  np.savez_compressed(f,rep=np.arange(a,min(a+100,stop)),ratios=results);print('controls',kind,min(a+100,stop),'/2000',f,flush=True)
 status('controls_progress',str(f))

def block_components(rows,base,cc,groups):
 ev=cc['fold']>0;g=pd.Series(groups);code=pd.factorize(g,sort=True)[0];B=int(code.max()+1);matrix=np.zeros((B,10));values=[np.ones(len(rows)),(rows.direction>0).to_numpy(float),rows.standardized_center_error.to_numpy(),np.where(ev,base['baseline'],0),np.where(ev,cc['GLOBAL_BIAS_SIGN005'],0),np.where(ev,cc['GLOBAL_MEDIAN_SHIFT'],0),np.where(ev,base['perfect'],0),np.nan_to_num(np.load(private()/'oracle_eval_GLOBAL_ORACLE_BIAS.npy')),np.where(ev,cc['ASSET_BIAS_SIGN005'],0),np.where(ev,cc['HORIZON_BIAS_SIGN005'],0)]
 for k,v in enumerate(values):matrix[:,k]=np.bincount(code,weights=v,minlength=B)
 return matrix

def bootstrap(kind,start,stop):
 verify();rows=load();base=np.load(private()/'base_losses.npz');cc=np.load(private()/'chronological.npz');groups=rows[kind].to_numpy();m=block_components(rows,base,cc,groups);folder=private()/'bootstrap'/kind;folder.mkdir(parents=True,exist_ok=True)
 for a in range(start,stop,250):
  f=folder/f'{a:04d}.npz'
  if f.exists():continue
  results=[]
  for rep in range(a,min(a+250,stop)):
   rng=np.random.default_rng(np.random.SeedSequence([SEED,2,{'origin':0,'year':1,'asset':2}[kind],rep]));v=m[rng.integers(len(m),size=len(m))].sum(axis=0)
   results.append([v[1]/v[0],v[2]/v[0],v[4]/v[3],v[5]/v[3],(v[3]-v[7])/(v[3]-v[6]),(v[3]-v[4])/(v[3]-v[6]),v[8]/v[3],v[9]/v[3]])
  np.savez_compressed(f,rep=np.arange(a,min(a+250,stop)),values=results);print('bootstrap',kind,min(a+250,stop),'/5000',f,flush=True)
 status('bootstrap_progress',str(f))

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('stage',choices=['construct','merge','chronological','oracle','controls','bootstrap']);a.add_argument('--start',type=int,default=0);a.add_argument('--stop',type=int,default=1250);a.add_argument('--universe',choices=['full','eval']);a.add_argument('--kind');x=a.parse_args()
 if x.stage=='construct':construct(x.start,x.stop)
 elif x.stage=='merge':merge()
 elif x.stage=='chronological':chronological()
 elif x.stage=='oracle':oracles(x.universe,x.kind)
 elif x.stage=='controls':controls(int(x.kind),x.start,x.stop)
 else:bootstrap(x.kind,x.start,x.stop)

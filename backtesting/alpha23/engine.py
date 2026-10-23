"""Executive summary: independent ridge conditional means, learned risk and shrunk joint Student-t draws."""
import json,pathlib,sys,hashlib,time
import numpy as np
import pandas as pd
from feature_builder import build,ASSETS

def design(x,center=None,scale=None):
 center=x.mean(axis=0) if center is None else center;scale=x.std(axis=0) if scale is None else scale;scale=np.where(scale<1e-8,1,scale)
 return np.c_[np.ones(len(x)),np.clip((x-center)/scale,-10,10)],center,scale

def ridge(x,y,alpha):
 penalty=np.eye(x.shape[1])*alpha;penalty[0,0]=0
 return np.linalg.solve(x.T@x+penalty,x.T@y)

def dataset(p,docs):
 x,sd=build(p,docs);target=np.stack([p.reindex(p.index+pd.offsets.BDay(h)).values-p.values for h in range(1,5)],axis=2).reshape(len(p),36)
 scale=(sd.values[:,:,None]*np.sqrt(np.arange(1,5))[None,None,:]).reshape(len(p),36)
 good=np.isfinite(x.values).all(axis=1)&np.isfinite(target).all(axis=1)&np.isfinite(scale).all(axis=1)
 return x.loc[good],target[good]/scale[good],scale[good]

def train(data,out):
 data=pathlib.Path(data);out=pathlib.Path(out);out.mkdir(exist_ok=True,parents=True)
 p=pd.read_parquet(data/'curve.parquet').loc[:'2023-12-31'].dropna();docs=json.loads((data/'documents.json').read_text());docs=[d for d in docs if d['active']<='2023-12-31']
 allx,ally,alls=dataset(p,docs);select=allx.index>='2001-01-01';x=allx.loc[select];y=ally[select];scales=alls[select]
 dates=x.index;fit=(dates+pd.offsets.BDay(4)<=pd.Timestamp('2020-12-31'));val=(dates>=pd.Timestamp('2021-01-01'))&(dates+pd.offsets.BDay(4)<=pd.Timestamp('2023-12-31'))
 assert fit.sum()>1000 and val.sum()>100
 np.savez_compressed(data/'training-matrices.npz',X=x.values,Y=y,scale=scales,dates=dates.values,columns=np.array(x.columns))
 receipt={'executive_summary':'Actual purged chronological training; final fit ends2023; validation-only penalty choice and risk fitting.','fit_origins':int(fit.sum()),'validation_origins':int(val.sum()),'final_fit_origins':len(x),'samples_by_year':{str(k):int(v) for k,v in pd.Series(1,index=dates).groupby(dates.year).sum().items()},'feature_count':len(x.columns),'models':{},'training_matrix_sha256':hashlib.sha256((data/'training-matrices.npz').read_bytes()).hexdigest(),'max_feature_date':str(dates.max().date()),'max_target_date':str((dates.max()+pd.offsets.BDay(4)).date())}
 for name,cols in [('full',list(x.columns)),('ablation',[c for c in x if not c.startswith('policy_')])]:
  a=x[cols].values;z,center,sd=design(a[fit]);zv,_,_=design(a[val],center,sd);choices=[]
  for penalty in [100,1000,10000]:
   b=ridge(z,y[fit],penalty);loss=float(np.mean((y[val]-zv@b)**2));choices.append({'alpha':penalty,'normalized_mse':loss})
  best=min(choices,key=lambda r:(r['normalized_mse'],-r['alpha']))['alpha'];initial=ridge(z,y[fit],best);res=y[val]-zv@initial
  zall,center,sd=design(a);mean=ridge(zall,y,best)
  # Risk trained on chronological held-out errors, with no2025/26 labels.
  risk=ridge(zall[val],np.log(res**2+1e-6),1000);raw=np.exp(np.clip(zall[val]@risk,-12,12));correction=np.mean(res**2/raw,axis=0)
  var=np.clip(raw*correction,.05,25);u=res/np.sqrt(var);cov=np.cov(u,rowvar=False);cov=.8*cov+.2*np.diag(np.diag(cov));cov+=np.eye(36)*1e-8
  model={'executive_summary':'Frozen independent ALPHA23 '+name,'assets':ASSETS,'horizons':[1,2,3,4],'columns':cols,'center':center.tolist(),'scale':sd.tolist(),'mean':mean.tolist(),'risk':risk.tolist(),'risk_correction':correction.tolist(),'covariance':cov.tolist(),'train_cutoff':'2023-12-31','seed':17,'df':7,'penalty':best}
  path=out/(name+'.json');path.write_text(json.dumps(model,separators=(',',':')))
  receipt['models'][name]={'validation':choices,'selected_alpha':best,'model_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'policy_columns':sum(c.startswith('policy_') for c in cols),'constant_policy_columns':[c for c in cols if c.startswith('policy_') and x[c].std()<1e-8]}
  print('trained',name,'origins',len(x),'alpha',best,flush=True)
 (out/'training-receipt.json').write_text(json.dumps(receipt,indent=2))

def predict(p,docs,asof,model,n=1000,seed=17):
 asof=pd.Timestamp(asof);p=p.loc[p.index<=asof].reindex(columns=ASSETS).dropna();docs=[d for d in docs if pd.Timestamp(d['active'])<=asof]
 assert asof>pd.Timestamp(model['train_cutoff']) and n>=200 and p.index.max()<=asof
 x,sd=build(p,docs);a=x[model['columns']].iloc[-1:].values;assert np.isfinite(a).all()
 z,_,_=design(a,np.array(model['center']),np.array(model['scale']));mu=(z@np.array(model['mean'])).ravel();variance=np.clip(np.exp(np.clip(z@np.array(model['risk']),-12,12))*np.array(model['risk_correction']),.05,25).ravel()
 scale=(sd.iloc[-1].values[:,None]*np.sqrt(np.arange(1,5))[None,:]).ravel();rng=np.random.default_rng(seed);noise=rng.normal(size=(n,36))@np.linalg.cholesky(np.array(model['covariance'])).T;noise*=np.sqrt(5/rng.chisquare(7,size=(n,1)))
 out=np.repeat(p.iloc[-1].values,4)+scale*(mu+noise*np.sqrt(variance));assert np.isfinite(out).all()
 return out,{'feature_date':str(p.index[-1].date()),'documents':len(docs),'latest_active_document':max((d['active'] for d in docs),default=None),'training_cutoff':model['train_cutoff']}
if __name__=='__main__':train(*sys.argv[1:])

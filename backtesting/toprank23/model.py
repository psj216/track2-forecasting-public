"""Executive summary: one frozen pooled conditional Student-t joint-path model; no labels at inference."""
import json, pathlib, sys, hashlib, tomllib
import numpy as np
import pandas as pd

def features(p):
    r=np.log(p).diff(); s=r.rolling(60).std().clip(lower=1e-8)
    x=pd.concat([r/s, r.rolling(5).sum()/s/np.sqrt(5),r.rolling(20).sum()/s/np.sqrt(20),r.rolling(60).sum()/s/np.sqrt(60),np.log(r.rolling(20).std()/s)],axis=1)
    x.columns=['r1','r5','r20','r60','volratio']
    return x.clip(-10,10),s,r

def ridge(x,y):
    penalty=np.eye(x.shape[1])*100; penalty[0,0]=0
    return np.linalg.solve(x.T@x+penalty,x.T@y)

def fit(path,out):
    p=pd.read_parquet(path); assert p.index.max()<=pd.Timestamp('2023-12-31')
    xx=[];yy=[]
    for a in p:
        v=p[a].dropna(); x,s,r=features(v)
        data=x.assign(y=r.shift(-1)/s).replace([np.inf,-np.inf],np.nan).dropna()
        data=data.loc[data.index>='2005-01-01'];xx.append(data.iloc[:,:5].values);yy.append(data.y.values)
    x=np.concatenate(xx);y=np.concatenate(yy);x=np.c_[np.ones(len(x)),x]
    b=ridge(x,y);res=y-np.clip(x@b,-.5,.5);g=ridge(x,np.log(res**2+1e-6))
    correction=float(np.mean(res**2/np.exp(x@g)))
    obj={'executive_summary':'Frozen training coefficients, no 2025 labels.','mean':b.tolist(),'logvariance':g.tolist(),'correction':correction,'training_rows':len(y),'training_end':str(p.index.max()),'training_sha256':hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()}
    pathlib.Path(out).write_text(json.dumps(obj,indent=2));print(obj)

def predict(unit,weights):
    unit=pathlib.Path(unit);card=tomllib.loads((unit/'card.toml').read_text());assets=card['targets']['asset_ids']; hs=card['targets']['horizons']
    assert card['targets']['target_type']=='level' and card['targets']['target_frequency']=='daily'
    p=pd.read_parquet(unit/'em_fx_ecb_daily.parquet');p['date']=pd.to_datetime(p.date)
    p=p[p.date<=pd.Timestamp(card['provenance']['data_cutoff'])].pivot(index='date',columns='asset',values='value').reindex(columns=assets).dropna()
    assert (p>0).all().all() and len(p)>121
    mus=[];sigmas=[]
    for a in assets:
        x,s,r=features(p[a]);z=np.r_[1,x.iloc[-1].values];assert np.isfinite(z).all()
        mus.append(np.clip(z@np.array(weights['mean']),-.5,.5)*s.iloc[-1])
        sigmas.append(s.iloc[-1]*np.sqrt(np.clip(np.exp(z@np.array(weights['logvariance']))*weights['correction'],.25,4)))
    corr=np.log(p).diff().tail(120).corr().values*.8+np.eye(len(assets))*.2
    chol=np.linalg.cholesky(corr);rng=np.random.default_rng(17)
    z=rng.normal(size=(1000,max(hs),len(assets)))@chol.T
    z*=np.sqrt(5/rng.chisquare(7,size=(1000,max(hs),1)))
    paths=p.iloc[-1].values*np.exp(np.cumsum(np.array(mus)+z*np.array(sigmas),axis=1))
    values=paths[:,np.array(hs)-1,:].transpose(0,2,1).reshape(1000,-1)
    assert np.isfinite(values).all();return values,[(a,h) for a in assets for h in hs]

if __name__=='__main__':
    if sys.argv[1]=='train':fit(*sys.argv[2:])
    else:
        root=pathlib.Path(sys.argv[2]);w=json.loads(pathlib.Path(sys.argv[3]).read_text());out=pathlib.Path(sys.argv[4]);out.mkdir(exist_ok=True,parents=True)
        receipts=[]
        for i,unit in enumerate(sorted(root.glob('inputs-*/*/card.toml'))):
            unit=unit.parent;x,c=predict(unit,w);assert np.array_equal(x,predict(unit,w)[0]);np.save(out/(unit.name+'.npy'),x)
            receipts.append({'id':unit.name,'cells':c,'shape':list(x.shape),'sha256':hashlib.sha256(x.tobytes()).hexdigest(),'repeat_identical':True})
            (out/'manifest.json').write_text(json.dumps(receipts,indent=2))
            if i%10==0:print('forecast',i+1,flush=True)

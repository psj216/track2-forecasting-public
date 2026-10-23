"""Executive summary: supervised conditional joint-path sampling, fixed before evaluation."""
import hashlib,json,pathlib,pickle,sys,tomllib,time
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
GROUPS={'ECB_EM':['MXN','BRL','ZAR','KRW','INR'],'ECB_G10':['EUR','JPY','CHF']}

def state(p):
    r=np.log(p).diff();sd=r.rolling(60).std().clip(lower=1e-8)
    xs=[r/sd,r.rolling(5).sum()/sd/np.sqrt(5),r.rolling(20).sum()/sd/np.sqrt(20),r.rolling(60).sum()/sd/np.sqrt(60),np.log(r.rolling(20).std()/sd)]
    return np.concatenate([v.to_numpy() for v in xs],axis=1).clip(-10,10),sd.to_numpy()

def training_arrays(p):
    assert p.index.max()<=pd.Timestamp('2023-12-31')
    x,sd=state(p);lp=np.log(p)
    paths=np.stack([lp.reindex(p.index+pd.offsets.BDay(h)).to_numpy()-lp.to_numpy() for h in [1,2,3,4]],axis=2)/sd[:,:,None]
    keep=np.isfinite(x).all(axis=1)&np.isfinite(paths).all(axis=(1,2))&(p.index>=pd.Timestamp('2005-01-01'))
    dates=p.index[keep]
    assert ((dates+pd.offsets.BDay(4))<=pd.Timestamp('2023-12-31')).all()
    return x[keep],paths[keep],dates

def fit(path,out):
    full=pd.read_parquet(path);assert full.index.max()<=pd.Timestamp('2023-12-31')
    models={};receipts=[]
    for group,assets in GROUPS.items():
        x,paths,dates=training_arrays(full[assets].dropna())
        y=np.c_[paths.reshape(len(paths),-1),np.minimum(paths[:,:,-1]**2,25)]
        forest=ExtraTreesRegressor(n_estimators=256,min_samples_leaf=64,max_features=.7,bootstrap=False,random_state=24,n_jobs=2)
        forest.fit(x,y);members=[]
        for tree in forest.estimators_:
            leaves=tree.apply(x);members.append({int(leaf):np.flatnonzero(leaves==leaf) for leaf in np.unique(leaves)})
        assert all(len(ix)>=64 for m in members for ix in m.values())
        models[group]={'forest':forest,'members':members,'paths':paths,'assets':assets}
        receipts.append({'group':group,'training_origins':len(x),'first_origin':str(dates.min().date()),'last_origin':str(dates.max().date()),'last_target':str((dates.max()+pd.offsets.BDay(4)).date()),'features':x.shape[1],'target_dimensions':y.shape[1],'dates_sha256':hashlib.sha256(dates.values.tobytes()).hexdigest(),'paths_sha256':hashlib.sha256(paths.tobytes()).hexdigest()})
        print('trained',receipts[-1],flush=True)
    pathlib.Path(out).write_bytes(pickle.dumps(models,protocol=5))
    return {'executive_summary':'Frozen models trained only pre2024. Binary holds training paths and stays outside public repository.','training_file_sha256':hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest(),'model_sha256':hashlib.sha256(pathlib.Path(out).read_bytes()).hexdigest(),'models':receipts}

def predict(unit,models):
    unit=pathlib.Path(unit);card=tomllib.loads((unit/'card.toml').read_text());assets=card['targets']['asset_ids'];hs=card['targets']['horizons']
    assert card['targets']['target_type']=='level' and card['targets']['target_frequency']=='daily' and hs==[1,2,3,4]
    matches=[m for m in models.values() if m['assets']==assets];assert len(matches)==1;m=matches[0]
    p=pd.read_parquet(unit/'em_fx_ecb_daily.parquet');p['date']=pd.to_datetime(p.date)
    p=p.loc[p.date<=pd.Timestamp(card['provenance']['data_cutoff'])].pivot(index='date',columns='asset',values='value').reindex(columns=assets).dropna()
    assert len(p)>60 and (p>0).all().all()
    x,sd=state(p);z=x[-1:];assert np.isfinite(z).all()
    leaves=[int(t.apply(z)[0]) for t in m['forest'].estimators_];rng=np.random.default_rng(17)
    chosen=np.array([rng.choice(m['members'][j][leaves[j]]) for j in rng.integers(0,256,size=1000)])
    out=p.iloc[-1].to_numpy()[None,:,None]*np.exp(m['paths'][chosen]*sd[-1][None,:,None])
    out=out.reshape(1000,-1);assert np.isfinite(out).all()
    return out,[(a,h) for a in assets for h in hs],hashlib.sha256(chosen.tobytes()).hexdigest()

if __name__=='__main__':
    if sys.argv[1]=='train':
        r=fit(sys.argv[2],sys.argv[3]);pathlib.Path(sys.argv[4]).write_text(json.dumps(r,indent=2))
    else:
        root=pathlib.Path(sys.argv[2]);models=pickle.loads(pathlib.Path(sys.argv[3]).read_bytes());out=pathlib.Path(sys.argv[4]);out.mkdir(parents=True,exist_ok=True)
        manifest=[];start=time.monotonic()
        for i,card in enumerate(sorted(root.glob('inputs-*/*/card.toml'))):
            unit=card.parent;x,c,s=predict(unit,models);assert np.array_equal(x,predict(unit,models)[0]);np.save(out/(unit.name+'.npy'),x)
            manifest.append({'id':unit.name,'shape':list(x.shape),'cells':c,'sha256':hashlib.sha256(x.tobytes()).hexdigest(),'selected_training_rows_sha256':s,'repeat_identical':True})
            (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
            if i%10==0:print('forecast',i+1,'seconds',round(time.monotonic()-start,2),flush=True)

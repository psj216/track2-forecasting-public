"""Executive summary: separate label-side paired diagnostic using unchanged official loss functions."""
import json,pathlib,hashlib,sys
import numpy as np,pandas as pd
from evaluate import metrics,summary,matrix
from m0 import reconstruct,scales
from qfbench2_track_forecasting.grid import grid_from_card
import tomllib
root=pathlib.Path('receipts/alpha19-newdata');base=pathlib.Path('receipts/alpha19-ecb');pred=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);rows=[];missing=[]
for f in sorted(pred.glob('*.npy')):
    group='ECB_EM' if 'ECB_EM' in f.stem else 'ECB_G10';unit=root/('inputs-'+group)/f.stem
    manifest=json.loads((unit.parent/'input-manifest.json').read_text());entry=next(e for e in manifest['inputs'] if e['id']==f.stem)
    for name,digest in entry['files'].items():assert hashlib.sha256((unit/name).read_bytes()).hexdigest()==digest
    label=pd.read_parquet(root/'labels'/(f.stem+'.parquet')).set_index(['asset','horizon'])
    card=tomllib.loads((unit/'card.toml').read_text());cells=grid_from_card(card).cells()
    if not all(c in label.index for c in cells):missing.append(f.stem);continue
    y=np.array([label.loc[c,'value'] for c in cells]);d=reconstruct(unit);scale=scales(d.mean,d.covariance)
    fs=list(base.glob('**/'+f.stem+'/forecast.parquet'));assert len(fs)==1
    receipt=json.loads(fs[0].with_name('receipt.json').read_text());assert receipt['exit']==0
    for name,digest in receipt['output_hashes'].items():assert hashlib.sha256(fs[0].with_name(name).read_bytes()).hexdigest()==digest
    a=matrix(fs[0],cells);b=np.load(f);assert a.shape==b.shape and np.isfinite(b).all()
    r={'id':f.stem,'origin':entry['origin'],'market':group,'ff03':metrics(a,y,scale),'candidate':metrics(b,y,scale),'subsets':{}}
    for key,ix in [(f'horizon:{h}',[i for i,c in enumerate(cells) if c[1]==h]) for h in [1,2,3,4]]+[(f'asset:{v}',[i for i,c in enumerate(cells) if c[0]==v]) for v in entry['assets']]:
        s=scales(d.mean[ix],d.covariance[np.ix_(ix,ix)]);r['subsets'][key]={'ff03':metrics(a[:,ix],y[ix],s)['score'],'candidate':metrics(b[:,ix],y[ix],s)['score']}
    rows.append(r);out.write_text(json.dumps({'summary':summary(rows),'cards':rows,'missing':missing},indent=2))
    if len(rows)%10==0:print('scored',len(rows),flush=True)
assert len(rows)==96 and len(missing)==4
by=pd.DataFrame([{'origin':r['origin'],'gain':r['ff03']['score']-r['candidate']['score']} for r in rows]).groupby('origin').gain.mean().sort_index()
rng=np.random.default_rng(2301);v=by.values;boots=[]
for _ in range(2000):
    starts=rng.integers(0,len(v),size=12);ix=np.concatenate([(s+np.arange(4))%len(v) for s in starts]);boots.append(v[ix].mean())
res={'executive_summary':'Exposed current-vintage research diagnostic; not independent OOS or Final score.','summary':summary(rows),'ci95_four_origin_blocks':np.quantile(boots,[.025,.975]).tolist(),'groups':{g:summary([r for r in rows if r['market']==g]) for g in ['ECB_EM','ECB_G10']},'remove_best_origin_gain':float(by.drop(by.idxmax()).mean()),'worst_card_gain':min(r['ff03']['score']-r['candidate']['score'] for r in rows),'quarters':{},'missing':missing,'cards':rows}
for q in range(1,5):res['quarters'][str(q)]=summary([r for r in rows if pd.Timestamp(r['origin']).quarter==q])
out.write_text(json.dumps(res,indent=2));print(json.dumps({k:v for k,v in res.items() if k!='cards'},indent=2))

"""Executive summary: all fixed robustness views; no candidate selection or tuning."""
import json
import pathlib
import sys
import numpy as np
from evaluate import summary


def analyze(rows):
    origins=sorted(set(r['origin'] for r in rows));delta=np.array([r['ff03']['score']-r['candidate']['score'] for r in rows])
    rng=np.random.default_rng(19019);indices={o:[i for i,r in enumerate(rows) if r['origin']==o] for o in origins}
    draws=[];n=len(origins)
    for _ in range(2000):
        starts=rng.integers(0,max(1,n-3),size=(n+3)//4)
        selected=[origins[i] for s in starts for i in range(s,min(s+4,n))][:n]
        ix=[i for o in selected for i in indices[o]]
        draws.append(float(delta[ix].mean()))
    ci=np.quantile(draws,[.025,.975]).tolist()
    out={'summary':summary(rows),'origin_block_improvement_ci95':ci,'bootstrap_origins':n,
         'independent_inference':False,'component_relative_damage':{},'groups':{},'removals':{},'sampling_sensitivity':{}}
    for c in ['marginal','joint','tail']:
        a=np.mean([r['ff03']['normalized'][c] for r in rows]);b=np.mean([r['candidate']['normalized'][c] for r in rows])
        out['component_relative_damage'][c]=(float(b/a-1) if a else None)
    categories={'family':lambda r:r['family'],'market':lambda r:r['market'],'year':lambda r:r['origin'][:4],
        'quarter':lambda r:r['origin'][:4]+'Q'+str((int(r['origin'][5:7])-1)//3+1),
        'shape':lambda r:'single' if r['cells']==1 else 'multi','text_active':lambda r:str(r['text_active'])}
    for key,fn in categories.items():
        groups=sorted(set(fn(r) for r in rows));out['groups'][key]={g:summary([r for r in rows if fn(r)==g]) for g in groups}
        if key in ['family','market','year']:
            out['removals']['leave_'+key+'_out']={g:(summary([r for r in rows if fn(r)!=g]) if any(fn(r)!=g for r in rows) else {'status':'UNKNOWN_NO_REMAINING_SAMPLE'}) for g in groups}
    origin_gain={o:sum(delta[indices[o]]) for o in origins};largest=max(origin_gain,key=origin_gain.get)
    out['removals']['largest_gain_origin']={'removed':largest,**summary([r for r in rows if r['origin']!=largest])}
    q=categories['quarter'];qgain={g:sum(d for d,r in zip(delta,rows) if q(r)==g) for g in out['groups']['quarter']};largestq=max(qgain,key=qgain.get)
    remaining=[r for r in rows if q(r)!=largestq]
    out['removals']['largest_gain_quarter']={'removed':largestq,**(summary(remaining) if remaining else {'status':'UNKNOWN_NO_REMAINING_SAMPLE'})}
    for seed in ['18','19']:
        score=float(np.mean([r['sampling_sensitivity'][seed] for r in rows]));out['sampling_sensitivity'][seed]={'score':score,'improvement':out['summary']['ff03']['score']-score}
    worst=int(delta.argmin());best=int(delta.argmax())
    out['worst_regression']={'id':rows[worst]['id'],'origin':rows[worst]['origin'],'increase':float(-delta[worst])}
    out['largest_gain']={'id':rows[best]['id'],'improvement':float(delta[best])}
    out['improved_cards']=int((delta>0).sum());out['worsened_cards']=int((delta<0).sum());out['ties']=int((delta==0).sum())
    keys=sorted(set(k for r in rows for k in r['subsets']));out['subset_diagnostics']={}
    for key in keys:
        selected=[r['subsets'][key] for r in rows if key in r['subsets']]
        out['subset_diagnostics'][key]={'cards':len(selected),'ff03':float(np.mean([r['ff03']['score'] for r in selected])),
            'candidate':float(np.mean([r['candidate']['score'] for r in selected])),
            'interpretation':'recomputed subgrid scales; diagnostic only, not original card contribution'}
    out['single_cell_empirical']='AVAILABLE' if 'single' in out['groups']['shape'] else 'NOT_AVAILABLE'
    out['text_active_empirical']='AVAILABLE' if 'True' in out['groups']['text_active'] else 'NOT_AVAILABLE'
    return out


if __name__=='__main__':
    datasets=[json.loads(pathlib.Path(p).read_text()) for p in sys.argv[2:]]
    result={'executive_summary':'Complete fixed falsification; dependent cards resampled by origin blocks. All evidence remains non-independent.',
       'datasets':{name:analyze(data['cards']) for name,data in zip(['practice','ecb2025'],datasets)}}
    pathlib.Path(sys.argv[1]).write_text(json.dumps(result,indent=2)+'\n')

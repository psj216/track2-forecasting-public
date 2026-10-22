"""Executive summary: distinguish distances, ordering, RNG and distribution impact."""
import json,pathlib
import numpy as np
import pandas as pd
import sys
r=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path('/results')
def read(p):return json.loads((r/p).read_text())
comparisons={}
for a,b in [('original-normal','ff03-normal'),('ff03-normal','ff03-repeat'),('ff03-normal','ff03-disabled'),('original-normal','original-disabled')]:
    x=pd.read_parquet(r/a/'forecast.parquet').sort_values(['asset','horizon','draw'])
    y=pd.read_parquet(r/b/'forecast.parquet').sort_values(['asset','horizon','draw'])
    dif=(x.value.to_numpy()-y.value.to_numpy()); cells=[]
    for (asset,h),group in x.groupby(['asset','horizon']):
        v=group.value.to_numpy();w=y[(y.asset==asset)&(y.horizon==h)].value.to_numpy()
        iqr=float(np.quantile(v,.75)-np.quantile(v,.25));q=[.01,.05,.5,.95,.99]
        cells.append(dict(asset=asset,horizon=int(h),iqr=iqr,mean_delta=float(w.mean()-v.mean()),median_delta=float(np.median(w)-np.median(v)),max_abs=float(np.max(np.abs(w-v))),rms_delta=float(np.sqrt(np.mean((w-v)**2))),quantile_delta=(np.quantile(w,q)-np.quantile(v,q)).tolist(),quantiles=q,tail_count_delta={str(p):int((w<=np.quantile(v,p)).sum()-(v<=np.quantile(v,p)).sum()) for p in [.01,.05,.95,.99]}))
    comparisons[a+'__'+b]=dict(changed=int(np.count_nonzero(dif)),total=len(dif),max_abs=float(np.abs(dif).max()),cells=cells,finite=bool(np.isfinite(y.value).all()),file_hashes_equal=read(a+'.json')['hashes']==read(b+'.json')['hashes'])
d0=read('ff03-normal-trace/numerical.json');d1=read('ff03-disabled-trace/numerical.json')
states=[]
for a,b in zip(d0['states'],d1['states'],strict=True):
    x=np.array(a['distance']);y=np.array(b['distance']);o=np.array(a['default_full_order']);p=np.array(b['default_full_order']);sx=np.array(a['stable_full_order']);sy=np.array(b['stable_full_order'])
    changed=np.flatnonzero(o!=p);swaps=[]
    for i in changed[:100]:
        j,k=int(o[i]),int(p[i]);swaps.append({'position':int(i),'normal_index':j,'disabled_index':k,'normal_distance_a':float(x[j]),'normal_distance_b':float(x[k]),'disabled_distance_a':float(y[j]),'disabled_distance_b':float(y[k]),'exact_tie_normal':bool(x[j]==x[k]),'exact_tie_disabled':bool(y[j]==y[k])})
    states.append(dict(distance_changed=int(np.count_nonzero(x!=y)),distance_max_abs=float(np.max(np.abs(x-y))),default_order_changed=int(len(changed)),stable_order_changed=int(np.count_nonzero(sx!=sy)),exact_tie_groups_normal=a['exact_tie_groups'],exact_tied_positions_normal=a['exact_tied_positions'],pool_same_members=sorted(a['selected'])==sorted(b['selected']),pool_changed_positions=sum(i!=j for i,j in zip(a['selected'],b['selected'],strict=True)),feature_matrix_equal=a['matrix_sha256']==b['matrix_sha256'],current_equal=a['current']==b['current'],scale_equal=a['scale']==b['scale'],ordering_examples=swaps))
blocks0=d0['blocks'];blocks1=d1['blocks']
result=dict(executive_summary='Same frozen numerical code; raw scoring is diagnostic only.',comparisons=comparisons,state_comparisons=states,random_pool_draw_sequence_equal=[b['pool_draw'] for b in blocks0]==[b['pool_draw'] for b in blocks1],rng_states_equal=[b['rng_state'] for b in blocks0]==[b['rng_state'] for b in blocks1],rng_final_state_equal=d0['rng_final_state']==d1['rng_final_state'],selected_blocks_changed=sum(a['start']!=b['start'] for a,b in zip(blocks0,blocks1,strict=True)),versions={k:d0[k] for k in ['python','numpy','pandas']})
(r/'analysis.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

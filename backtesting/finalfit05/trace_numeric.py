"""Executive summary: trace unchanged frozen code in a separate diagnostic process."""
import hashlib,json,linecache,pathlib,platform,sys
import numpy as np
import pandas as pd
from qfbench2_track_forecasting import cli
records={'states':[], 'blocks':[]}
def plain(x):
    if isinstance(x,np.ndarray): return x.tolist()
    if isinstance(x,np.generic): return x.item()
    raise TypeError(type(x).__name__)
def trace(frame,event,arg):
    name=frame.f_code.co_name
    if name=='_state_matched_starts' and event=='return' and 'distance' in frame.f_locals:
        loc=frame.f_locals;d=loc['distance'].to_numpy(dtype=float)
        vals,counts=np.unique(d,return_counts=True)
        records['states'].append({'distance':d.tolist(),'distance_hex':[float(v).hex() for v in d],
            'eligible':loc['eligible'],'selected':arg,'nearest_positions':loc['nearest_positions'].tolist(),
            'default_full_order':np.argsort(d).tolist(),'stable_full_order':np.argsort(d,kind='stable').tolist(),
            'exact_tie_groups':int((counts>1).sum()),'exact_tied_positions':int(counts[counts>1].sum()),
            'current':loc['current'].tolist(),'scale':loc['scale'].tolist(),
            'matrix_sha256':hashlib.sha256(loc['matrix'].to_numpy().tobytes()).hexdigest()})
    if name=='_sample_blocks':
        loc=frame.f_locals
        if event=='line' and linecache.getline(frame.f_code.co_filename,frame.f_lineno).strip().startswith('take ='):
            records['blocks'].append({k:plain(loc[k]) if isinstance(loc[k],np.generic) else loc[k] for k in ['draw','cursor','pool_draw','use_recent','use_matched','start']})
            records['blocks'][-1]['rng_state']=loc['rng'].bit_generator.state
        if event=='return' and 'rng' in loc: records['rng_final_state']=loc['rng'].bit_generator.state
    return trace if name in ('_state_matched_starts','_sample_blocks') else None
sys.settrace(trace)
exitcode=cli.main(sys.argv[1:])
sys.settrace(None)
records.update(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,features={k:bool(v) for k,v in np._core._multiarray_umath.__cpu_features__.items()})
pathlib.Path('/trace/numerical.json').write_text(json.dumps(records,default=plain))
raise SystemExit(exitcode)

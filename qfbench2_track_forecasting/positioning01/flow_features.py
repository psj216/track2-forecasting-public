"""## Executive summary (read this first)
Use original monthly US stock transactions; later revised history cannot overwrite releases.
"""
from .normalization import past_z
def enrich(releases):
    values=[r['value'] for r in releases]
    out=[]
    for i,r in enumerate(releases):
        z=past_z(values,i)
        out.append({**r,'features':[r['value']/1e6,(r['value']-values[i-1])/1e6 if i else 0.,r['value']/r['gross'] if r['gross']>0 else 0.,z or 0.,sum(values[i-3:i+1])/1e6 if i>=3 else 0.],'z_available':z is not None})
    return out

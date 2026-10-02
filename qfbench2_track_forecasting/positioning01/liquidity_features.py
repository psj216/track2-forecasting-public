"""## Executive summary (read this first)
Bank reserve balances are global funding quantities, using each original weekly release.
"""
from .normalization import past_z
def enrich(releases):
    values=[r['value'] for r in releases];out=[]
    for i,r in enumerate(releases):
        z=past_z(values,i)
        out.append({**r,'features':[r['value']/1e6,(r['value']-values[i-1])/1e6 if i else 0.,(r['value']-values[i-4])/1e6 if i>=4 else 0.,(r['value']-values[i-13])/1e6 if i>=13 else 0.,z or 0.],'z_available':z is not None})
    return out

"""## Executive summary (read this first)
Build matched-as-of expert inputs using the unchanged admitted source feature specifications.
"""
import numpy as np
from ..expectation01.expectation_features import expectation_at,E_NAMES,V_NAMES
from ..expectation01.surprise_features import surprise_at
from ..positioning01.publication_alignment import latest,age
from ..positioning01.source_asset_map import LIQUIDITY_ASSETS
def expectation_query(rows,snapshots,events,columns):
 cache={}
 for origin in sorted(set(r['origin']for r in rows)):
  e,v,_=expectation_at(snapshots,origin);s,_=surprise_at(events,origin)
  cache[origin]=dict(zip(E_NAMES+['S_RGDP_1','S_RGDP_5','S_RGDP_21']+V_NAMES,np.r_[e,s,v]))
 x=np.zeros((len(rows),len(columns)))
 for j,c in enumerate(columns):
  base=c['name'].split('__')[0]
  for i,r in enumerate(rows):
   x[i,j]=cache[r['origin']][base]
   if 'metadata'in c:x[i,j]*=float(str(r[c['metadata']])==c['value'])
 return x
def quantity_query(rows,releases,columns):
 x=np.zeros((len(rows),len(columns)))
 for i,r in enumerate(rows):
  for cls in ['F','L']:
   if (cls=='F'and r['asset']!='MKT')or(cls=='L'and r['asset']not in LIQUIDITY_ASSETS):continue
   maximum=30 if cls=='F' else 10
   actual=latest(releases[cls],r['origin'],maximum)
   if actual is None:continue
   v=actual['features']+[age(actual['release_date'],r['origin'])/maximum,age(actual['observation_date'],r['origin'])/63]
   base=[j for j,c in enumerate(columns)if c['class_id']==cls and c['stage']==1];x[i,base]=v
   for h in [5,21,63,126,189]:
    dest=[j for j,c in enumerate(columns)if c['class_id']==cls and c.get('horizon')==h]
    if r['horizon']==h and dest:x[i,dest]=v
 return x

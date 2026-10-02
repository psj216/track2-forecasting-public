"""## Executive summary (read this first)
Annotate public task metadata and dated text using fixed rules; never consume a label.
"""
import re
import numpy as np
from .context_schema import TOPICS,CONDITIONS,LANGUAGE,ENTITIES,EVENTS,STRUCTURE,asset_group,horizon_bin,schema
def present(pattern,text):return bool(re.search(pattern,text,re.I))
def annotate(card,question,documents):
 # The public task question defines requested economics and conditionality.
 # Broad central-bank corpus incidental topics do not silently become routing tags.
 q=question.lower();corpus='\n'.join(documents).lower();alltext=q+'\n'+corpus
 a={n:0. for n in STRUCTURE};a['family_'+card['family'][-2:]]=1.;hs=card['horizons'];single=card['cells']==1
 a.update(single=float(single),multi=float(not single),assets_count=len(card['assets'])/8.,horizons_count=len(hs)/5.,min_horizon=min(hs)/189.,max_horizon=max(hs)/189.,target_level=float(card['target_type']=='level'),target_return=float(card['target_type']in('return','log_return')),target_other=float(card['target_type']not in('level','return','log_return')))
 a['relative']=float(present(r'relative|comparison|spread|rank|versus|\bvs\b',q));a['absolute']=1.-a['relative'];a['trajectory']=float(len(hs)>1 or present(r'path|trajectory|curve',q));a['future_point']=1.-a['trajectory']
 for n,p in CONDITIONS.items():a[n]=float(present(p,q))
 a['joint_path_consistency']=max(a['joint_path_consistency'],float(card['cells']>1));a['unconditional']=float(not(a['explicit_scenario']or a['event_conditioned']))
 tags=[n for n,p in TOPICS.items()if present(p,q)]
 groups={asset_group(x,card['target_type'])for x in card['assets']}
 for g,t in [('FX','FX'),('Rates','rates'),('Factor/Equity','equity')]:
  if g in groups and t not in tags:tags.append(t)
 if not tags:tags=['generic_none']
 for n in TOPICS:a[n]=float(n in tags)
 for n,p in LANGUAGE.items():a[n]=float(present(p,alltext))
 a['named_event_count']=sum(present(re.escape(v),alltext)for v in EVENTS)/10.;a['named_entity_count']=sum(present(r'\b'+re.escape(v)+r'\b',alltext)for v in ENTITIES)/20.
 a.update(immediate=float(max(hs)<=5),short=float(5<max(hs)<=21),medium=float(21<max(hs)<=63),long=float(max(hs)>63),multi_horizon=float(len(hs)>1))
 return dict(features=a,economic_topics=tags,corpus_topics=[n for n,p in TOPICS.items()if present(p,corpus)],conditional_types=[n for n in CONDITIONS if a[n]],method='Fixed question/structured-asset topic routing; corpus lexical language and counts; no outcome input.')
def matrix(cards,annotations):
 cols=schema();rows=[];metadata=[]
 for c in cards:
  a=annotations[c['id']]['features']
  for h in c['horizons']:
   for asset in c['assets']:
    g=asset_group(asset,c['target_type']);v=horizon_bin(h);r=[]
    for s in cols:
     x=a[s.get('base',s['name'])]
     if 'interaction'in s:x*=float(s['value']==(g if s['interaction']=='group'else v))
     r.append(x)
    rows.append(r);metadata.append(dict(card_id=c['id'],family=c['family'],origin=c['origin'],asset=asset,horizon=int(h),group=g,single=c['cells']==1))
 return np.array(rows,float),metadata,cols

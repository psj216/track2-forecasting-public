"""## Executive summary (read this first)
Freeze whole-card text/topic rotation and semantic masking, preserving genuine target structure.
"""
import copy
from qfbench2_track_forecasting.context01.context_schema import BASE_COLUMNS,TEMPORAL,STRUCTURE,TOPICS
def controlled_annotations(cards,annotations,kind):
 out=copy.deepcopy(annotations);families=sorted(set(c['family']for c in cards))
 for fam in families:
  ids=sorted(c['id']for c in cards if c['family']==fam)
  for j,c in enumerate(ids):
   original=annotations[c]['features'];donor=annotations[ids[(j+1)%len(ids)]]['features']
   for n,stage in BASE_COLUMNS:
    if kind=='A'and stage>1 and n not in TEMPORAL:out[c]['features'][n]=donor[n]
    elif kind=='B'and n in TOPICS:out[c]['features'][n]=donor[n]
    elif kind=='D'and n not in STRUCTURE and n not in TEMPORAL and n not in ['explicit_date','numerical_threshold']:out[c]['features'][n]=0.
 for c in out:out[c]['economic_topics']=[n for n in TOPICS if out[c]['features'][n]]
 return out

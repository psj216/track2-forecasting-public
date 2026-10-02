"""## Executive summary (read this first)
Build at most forty text columns from frozen dated text using inherited lexical rules only.
"""
import re
import numpy as np
from qfbench2_track_forecasting.context01.context_schema import TOPICS,CONDITIONS,LANGUAGE
S_NAMES=['single','cells','assets_count','horizons_count','min_horizon','max_horizon','target_level','target_return','target_other','family_F1','family_F2','family_F3','family_F4']
T_NAMES=[*TOPICS,*CONDITIONS,*[n for n in LANGUAGE if n not in ['explicit_date','numerical_threshold']],'named_event_count','named_entity_count','log_characters','log_words','numeric_token_count','horizon_wording']
F_NAMES=['mean_absolute_standardized_disagreement','maximum_absolute_standardized_disagreement','mean_B0_SD','SD_dispersion','mean_absolute_median_disagreement']
def text_features(text,annotation):
 q=text['question'];alltext=q+'\n'+'\n'.join(text['documents']);f=annotation['features'];topics=[float(bool(re.search(p,q,re.I)))for p in TOPICS.values()]
 if not any(topics):topics[-1]=1.
 # Parent topic flags inject structured asset classes; never call those text-only features.
 return topics+[float(bool(re.search(p,q,re.I)))for p in CONDITIONS.values()]+[f[n]for n in LANGUAGE if n not in ['explicit_date','numerical_threshold']]+[f['named_event_count'],f['named_entity_count'],np.log1p(len(alltext)),np.log1p(len(re.findall(r'\b\w+\b',alltext))),float(len(re.findall(r'\b\d+(?:\.\d+)?\b',q))),float(bool(re.search(r'horizon|days|weeks|months|path|trajectory',q,re.I)))]
def structure_features(card):
 return [float(card['cells']==1),card['cells'],len(card['assets']),len(card['horizons']),min(card['horizons']),max(card['horizons']),float(card['target_type']=='level'),float(card['target_type']in('return','log_return')),float(card['target_type']not in('level','return','log_return'))]+[float(card['family']=='T2-F'+str(i))for i in range(1,5)]
def build(cards,texts,annotations,b0,r2):
 s=np.array([structure_features(c)for c in cards],float);t=np.array([text_features(texts[c['id']],annotations[c['id']])for c in cards],float);states=[]
 for x,z in zip(b0,r2):
  sd=np.std(x,axis=0);diff=np.median(z,axis=0)-np.median(x,axis=0);d=diff/np.maximum(sd,1e-12);states.append([np.mean(abs(d)),np.max(abs(d)),np.mean(sd),np.std(sd),np.mean(abs(diff))])
 state=np.array(states);assert t.shape[1]==len(T_NAMES)<=40
 return dict(S0=s,T0=t,ST0=np.column_stack([s,t]),STF0=np.column_stack([s,t,state]),LENGTH=t[:,[T_NAMES.index('log_characters'),T_NAMES.index('log_words')]],ST_NO_FAMILY=np.column_stack([s[:,:9],t]))

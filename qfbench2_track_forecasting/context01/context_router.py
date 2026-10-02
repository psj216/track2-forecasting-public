"""## Executive summary (read this first)
Choose eligible previously admitted experts from fixed semantic topics and original mapping.
"""
import numpy as np
EXPERTS=('RGDP','CPI','UNEMP','TBILL','TBOND','F','L')
PRIORITY=('L','F','TBILL','TBOND','CPI','RGDP','UNEMP')
TOPIC_EXPERTS={'growth':['RGDP'],'inflation':['CPI'],'labor':['UNEMP'],'monetary_policy':['TBILL','TBOND'],'rates':['TBILL','TBOND'],'equity':['F'],'capital_flow':['F'],'liquidity':['L']}
def eligible(topics,asset):
 selected={e for t in topics for e in TOPIC_EXPERTS.get(t,[])}
 if asset!='MKT':selected.discard('F')
 return [e for e in PRIORITY if e in selected]
def route(topics,assets,predictions,available,permuted=False):
 one=np.zeros(len(assets));mean=one.copy();coverage=np.zeros(len(assets),bool);choices=[]
 for j,asset in enumerate(assets):
  choices.append(eligible(topics,asset));active=[e for e in choices[-1]if available[e][j]]
  if not active:continue
  coverage[j]=True
  def get(e):return predictions[EXPERTS[(EXPERTS.index(e)+1)%len(EXPERTS)]] [j]if permuted else predictions[e][j]
  one[j]=get(active[0]);mean[j]=np.mean([get(e)for e in active])
 return np.clip(one,-10,10),np.clip(mean,-10,10),coverage,choices

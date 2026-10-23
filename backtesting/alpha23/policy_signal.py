"""Executive summary: cutoff-safe measurable policy language, not identified market surprises."""
import re
import numpy as np
import pandas as pd
TOPICS={'tightening':r'\b(raise|increase|restrictive|tighten\w*)\b','easing':r'\b(lower|reduce|accommodative|ease|easing)\b','inflation':r'\b(inflation|prices|price stability)\b','labor':r'\b(employment|unemployment|labor)\b','growth':r'\b(growth|activity|output|recession)\b','stability':r'\b(financial stability|banking|credit|liquidity)\b','balance_sheet':r'\b(holdings|balance sheet|securities|reinvestment)\b','guidance':r'\b(will|expects|anticipates|outlook|appropriate)\b'}
SCHEDULE=['2025-01-29','2025-03-19','2025-05-07','2025-06-18','2025-07-30','2025-09-17','2025-10-29','2025-12-10','2026-01-28','2026-03-18','2026-04-29','2026-06-17','2026-07-29','2026-09-16','2026-10-28','2026-12-09']
def signals(text):
 t=text.lower();n=max(1,len(re.findall(r'\w+',t)));return [1000*len(re.findall(pattern,t))/n for pattern in TOPICS.values()]
def features(dates,docs):
 ordered=sorted(docs,key=lambda x:(x['active'],x['sha256']));last=None;rows=[]
 for day in dates:
  eligible=[d for d in ordered if pd.Timestamp(d['active'])<=day]
  if eligible:
   v=eligible[-1];same=[d for d in eligible[:-1] if d['kind']==v['kind']];delta=np.array(v['signals'])-np.array(same[-1]['signals']) if same else np.zeros(8)
   age=(day-pd.Timestamp(v['active'])).days;vals=v['signals']+delta.tolist()+[min(age,365)/365,int(age<=4),int(age<=20),1,0]
  else:vals=[0.]*21
  # Dates published Aug9,2024. Training-era schedule absence is explicit, never backfilled.
  known=day>=pd.Timestamp('2024-08-12');inside=int(known and any(day<pd.Timestamp(s)<=day+pd.offsets.BDay(4) for s in SCHEDULE))
  rows.append(vals+[int(known),inside])
 names=list(TOPICS)+['delta_'+k for k in TOPICS]+['age','recent4','recent20','reliability_metadata_only','conflict','schedule_available','scheduled_event4']
 return pd.DataFrame(rows,index=dates,columns=['policy_'+n for n in names])

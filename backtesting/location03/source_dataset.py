"""Executive summary: exact original domestic C&I counts, denominators and PIT states.

No outcome loader exists here. Only original-round Table 1 is admitted.
"""
from pathlib import Path
import re,hashlib,json,csv
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
FEATURES=('CREDIT_STANDARDS','CREDIT_DEMAND','DELTA_CREDIT_STANDARDS','DELTA_CREDIT_DEMAND','SOURCE_AGE_BUSINESS_DAYS')
STANDARDS=('Tightened considerably','Tightened somewhat','Remained basically unchanged','Eased somewhat','Eased considerably')
DEMAND=('Substantially stronger','Moderately stronger','About the same','Moderately weaker','Substantially weaker')
AGE_LIMIT=100
START_YEAR=2013

def normalize(text):return re.sub(r'\s+',' ',text).strip()
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps({'executive_summary':'Original-release research source audit; no forecasting outcomes used.',**x},indent=2,allow_nan=False)+'\n')
def write_csv(p,rows):
 if not rows:raise ValueError('Empty ledger')
 with Path(p).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def publication(text):
 matches=re.findall(r'Last\s+[Uu]pdate\s*:\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',normalize(text))
 if not matches:raise ValueError('Missing dated official original-round metadata')
 return str(pd.Timestamp(matches[-1]).date())
def activation(date):return pd.Timestamp(date).tz_localize('America/New_York')+pd.Timedelta(hours=23,minutes=59,seconds=59)
def cutoff(origin):return (pd.Timestamp(origin)-pd.offsets.BDay(1)).tz_localize('America/New_York')+pd.Timedelta(hours=16)
def net(counts,total):
 c=np.asarray(counts,int)
 if len(c)!=5 or np.any(c<0) or sum(c)!=total or total<=0:raise ValueError('Applicable denominator mismatch')
 return 100.*float(c[0]+c[1]-c[3]-c[4])/total

def parse_table(table,categories):
 parsed={}; percentages={}
 for tr in table.find_all('tr'):
  cells=[normalize(c.get_text(' ',strip=True)) for c in tr.find_all(['td','th'],recursive=False)]
  if len(cells)>=3 and cells[0] in (*categories,'Total'):
   if cells[0] in parsed:raise ValueError('Duplicate response category')
   parsed[cells[0]]=int(cells[1]);percentages[cells[0]]=float(cells[2])
 if set(parsed)!=set((*categories,'Total')):raise ValueError('Missing original response counts')
 counts=[parsed[c] for c in categories];total=parsed['Total'];value=net(counts,total)
 if any(abs(percentages[c]-100*parsed[c]/total)>.16 for c in categories):raise ValueError('Count/percentage disagreement')
 return dict(counts=counts,denominator=total,net=value,percentages=[percentages[c] for c in categories])

def extract(html):
 soup=BeautifulSoup(html,'html.parser');text=normalize(soup.get_text(' ',strip=True))
 if not all(s in text for s in ['C&I','large and middle-market','small firms']):raise ValueError('C&I semantics absent')
 tables=soup.find_all('table'); standards=[];demand=[]
 for t in tables:
  tt=normalize(t.get_text(' ',strip=True))
  if all(c in tt for c in STANDARDS) and len(standards)<2:standards.append(t)
  if all(c in tt for c in DEMAND) and len(demand)<2:demand.append(t)
 if len(standards)!=2 or len(demand)!=2:raise ValueError('Primary question tables absent')
 out=[]
 for kind,ts,cats in [('standards',standards,STANDARDS),('demand',demand,DEMAND)]:
  for size,t in zip(('large_middle','small'),ts):
   # Discovered original table summaries/captions establish borrower group order.
   context=t.get('summary','') or normalize(t.find_previous(['h4','h5','p']).get_text(' ',strip=True))
   if ('small' not in context.lower() if size=='small' else not any(s in context.lower() for s in ['large','middle'])):raise ValueError('Borrower group context inconsistent: '+context)
   row=parse_table(t,cats);row.update(variable=kind,borrower_size=size,table_context=context)
   segment=''
   for element in t.next_elements:
    if getattr(element,'name',None)=='table':break
    if isinstance(element,str):segment+=' '+element
    if len(segment)>10000:break
   m=re.search(r'(\d+)\s+respondent(?:s)?\s+answered.*?does not originate',normalize(BeautifulSoup(segment,'html.parser').get_text(' ',strip=True)),re.I)
   row['non_originating_explicit_count']=int(m[1]) if m else None
   out.append(row)
 return out

def states_from_rows(rows):
 rows=sorted(rows,key=lambda s:s['publication_date']);out=[];previous=None
 for row in rows:
  s=dict(row);s['available_at']=activation(s['publication_date']).isoformat()
  s['DELTA_CREDIT_STANDARDS']=s['CREDIT_STANDARDS']-previous['CREDIT_STANDARDS'] if previous else None
  s['DELTA_CREDIT_DEMAND']=s['CREDIT_DEMAND']-previous['CREDIT_DEMAND'] if previous else None
  out.append(s);previous=s
 return out

def asof_features(states,origin):
 t=cutoff(origin);eligible=[s for s in states if pd.Timestamp(s['available_at'])<=t and not s.get('inactive',False)]
 if not eligible:return None
 s=max(eligible,key=lambda x:x['available_at']).copy();age=int(np.busday_count(s['publication_date'],str(t.date())))
 if age>AGE_LIMIT:return None
 s['SOURCE_AGE_BUSINESS_DAYS']=age
 if any(s.get(f) is None for f in FEATURES):return None
 return s

def original_fields_admissible(affected_fields,original_recovered):
 return not affected_fields or original_recovered

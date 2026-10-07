"""Executive summary: original SEP median fields and conservative historical activation."""
from pathlib import Path
import re,json,hashlib
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
PARENT='6653df8c61042c4642be3e2ed37b52daeea16de7'
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'results'
HORIZONS=(5,21,63,126,189)
ASSETS=('UST_2Y','UST_5Y')
YEARS=(2020,2021,2022,2023,2024)
SEED=31802
AMPLITUDE=.05
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(value,indent=2,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+'\n')
def csv(path,rows):
 Path(path).parent.mkdir(parents=True,exist_ok=True);pd.DataFrame(rows).to_csv(path,index=False)
def activation(date):return pd.Timestamp(date).normalize().tz_localize('America/New_York')+pd.Timedelta(hours=23,minutes=59,seconds=59)
def cutoff(origin):return (pd.Timestamp(origin)-pd.offsets.BDay(1)).tz_localize('America/New_York')+pd.Timedelta(hours=16)
def age(date,at):return int(np.busday_count(np.datetime64(str(date)[:10],'D'),np.datetime64(str(pd.Timestamp(at).date()),'D')))
def parse(html,date):
 """Follow HTML accessibility header IDs, accepting old td and new th row stubs."""
 soup=BeautifulSoup(html,'html.parser');matches=[];year=int(str(date)[:4])
 for table in soup.find_all('table'):
  head=table.find('thead')
  if head is None:continue
  med=next((x for x in head.find_all(['th','td']) if re.match('^Median',x.get_text(' ',strip=True))),None)
  if med is None or not med.get('id'):continue
  ident=med['id'];headers={x.get('id'):x.get_text(' ',strip=True) for x in head.find_all(['th','td']) if ident in x.get('headers',[])}
  for row in table.select('tbody tr'):
   cells=row.find_all(['td','th'],recursive=False)
   if not cells or not re.fullmatch(r'Federal funds rate(?:\s*\d+)?',cells[0].get_text(' ',strip=True)):continue
   mapping={}
   for cell in cells[1:]:
    h=cell.get('headers',[]);years=[headers[x] for x in h if x in headers and re.fullmatch(r'20\d{2}',headers[x])]
    if ident in h and len(years)==1 and int(years[0]) in [year,year+1]:
     text=cell.get_text(' ',strip=True)
     if not re.fullmatch(r'(?:\d+(?:\.\d+)?|\.\d+)',text):raise ValueError('Non-numeric published policy median')
     mapping[int(years[0])]=float(text)
   if year not in mapping or year+1 not in mapping:raise ValueError('Explicit release-year CY and NCY missing')
   matches.append((mapping[year],mapping[year+1]))
 if not matches:raise ValueError('Original policy median row not extractable')
 if len(set(matches))!=1:raise ValueError('Conflicting original policy values')
 cy,ncy=matches[0]
 return dict(release_id='SEP_'+str(date),release_date=str(date),available_at=activation(date).isoformat(),CY=cy,NCY=ncy,CY_target=year,NCY_target=year+1,value=ncy-cy,aggregation='published median',units='percentage points',active=True)
def canonical(rows):
 """Duplicates with identical values collapse; conflicting versions fail closed."""
 out={}
 for r in rows:
  ident=(r['release_id'],r.get('version',0));fields=(r.get('CY'),r.get('NCY'),r['available_at'],r.get('active',True))
  if ident in out and fields!=out[ident][0]:raise ValueError('Conflicting duplicate original release')
  out[ident]=(fields,dict(r))
 return sorted([r for _,r in out.values()],key=lambda r:(pd.Timestamp(r['available_at']),r['release_id'],r.get('version',0)))
def asof(rows,at,delay=0,previous=False):
 at=pd.Timestamp(at);query=at-pd.offsets.BDay(delay)
 known=[r for r in canonical(rows) if pd.Timestamp(r['available_at'])<=query]
 if not known:return None
 # Latest version for each original release; later correction cannot rewrite earlier states.
 versions={r['release_id']:r for r in known};ordered=sorted(versions.values(),key=lambda r:r['release_date'])
 current=ordered[-1]
 if not current.get('active',True) or age(current['release_date'],query)>90:return None
 if previous:
  if len(ordered)<2:return None
  current=ordered[-2]
  if not current.get('active',True):return None
 return {**current,'source_age':age(current['release_date'],query),'query_cutoff':query.isoformat()}

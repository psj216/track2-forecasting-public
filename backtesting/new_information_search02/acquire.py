"""Original official-source acquisition with per-document receipts and bounded chunks."""
from pathlib import Path
import requests,json,hashlib,re,time,concurrent.futures
from datetime import datetime,timezone
from urllib.parse import urljoin
from bs4 import BeautifulSoup
P=Path(__import__('os').environ['NEWINFO02_PRIVATE']); D=P/'documents';D.mkdir(exist_ok=True)
def get(url,name):
 f=D/(name+'.html');receipt=D/(name+'.json')
 if f.exists() and receipt.exists():return f.read_text(errors='replace')
 try:
  r=requests.get(url,timeout=30);r.raise_for_status();b=r.content
  f.write_bytes(b);receipt.write_text(json.dumps({'url':url,'retrieved_at':datetime.now(timezone.utc).isoformat(),'status':r.status_code,'bytes':len(b),'SHA256':hashlib.sha256(b).hexdigest()},indent=2));return b.decode(errors='replace')
 except Exception as e:
  (D/(name+'.error.json')).write_text(json.dumps({'url':url,'error':str(e)}));return ''
def batch(items,label):
 started=time.monotonic()
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  for n,(name,s) in enumerate(pool.map(lambda z:(z[1],get(*z)),items),1):
   print(label,n,'/',len(items),name,'elapsed',round(time.monotonic()-started),'output',D,flush=True)
 return
if __name__=='__main__':
 stage=__import__('sys').argv[1]
 if stage=='indexes':
  html=get('https://www.federalreserve.gov/monetarypolicy/fomc_historical_year.htm','fomc_year_index')
  links={urljoin('https://www.federalreserve.gov',a['href']) for a in BeautifulSoup(html,'html.parser').select('a[href]') if re.search(r'fomchistorical20(1[5-9]|20)\.htm',a['href'],re.I)}
  batch([(u,'fomc_'+re.search(r'20\d{2}',u)[0]) for u in sorted(links)],'annual_indexes')
  get('https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm','fomc_calendars')
 elif stage=='sep':
  links=set()
  for file in D.glob('fomc_*.html'):
   for a in BeautifulSoup(file.read_text(errors='replace'),'html.parser').select('a[href]'):
    h=a['href'];m=re.search(r'(20\d{6})',h)
    if m and '20150101'<=m[1]<='20241218' and re.search(r'(fomcprojtabl|fomcprojtable|fomcproj[a-z]*20\d{6})\.htm',h,re.I):links.add(urljoin('https://www.federalreserve.gov',h))
  (P/'sep_links.json').write_text(json.dumps(sorted(links),indent=2));print('SEP discovered',len(links),flush=True)
  batch([(u,'sep_'+re.search(r'20\d{6}',u)[0]) for u in sorted(links)],'SEP_originals')
 elif stage=='h41':
  import pandas as pd
  dates=sorted({d for y in json.loads((P/'h41_dates.txt').read_text()) for m in y['Months'] for d in m['Dates'] if '20150101'<=d<='20241218'})
  origins=pd.read_parquet(P/'frozen_spd_direction_state.parquet').origin_date.unique();wanted=set()
  # Entire weekly original universe enumeration; sampled documents only, never pretend unacquired changes are unchanged.
  for origin in origins:
   o=pd.Timestamp(origin)
   for offset in (0,21,42):
    cutoff=(o-pd.offsets.BDay(1+offset)).strftime('%Y%m%d');eligible=[d for d in dates if d<=cutoff]
    if eligible:wanted.add(eligible[-1])
  wanted.update(d for d in dates if d.startswith(('2015','2016')) and d[4:6] in ('01','07'))
  wanted.update(d for d in dates if '20230101'<=d<='20230630')
  (P/'h41_acquisition_plan.json').write_text(json.dumps({'universe':dates,'sample':sorted(wanted),'sampling':'Latest at every frozen origin, 21/42 business days earlier, Jan/July2015/16, complete2023H1'},indent=2))
  batch([('https://www.federalreserve.gov/releases/h41/'+d,'h41_'+d) for d in sorted(wanted)],'H41_original_sample')
 elif stage=='rrp':
  batch([('https://markets.newyorkfed.org/api/rp/results/search.json?startDate='+str(y)+'-01-01&endDate='+str(y)+'-12-'+('18' if y==2024 else '31')+'&operationTypes=Reverse%20Repo&term=overnight','rrp_'+str(y)) for y in range(2015,2025)],'RRP_version_audit')

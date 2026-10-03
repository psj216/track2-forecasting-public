"""Executive summary: Acquire discovered official original-round files with checkpoints."""
import pathlib,json,csv,subprocess,re,time,concurrent.futures
from bs4 import BeautifulSoup
from urllib.parse import urljoin
ROOT=pathlib.Path(__file__).resolve().parents[3]; raw=ROOT/'location03-private/source';raw.mkdir(exist_ok=True)
out=ROOT/'location03-repo/backtesting/location03/results'; base='https://www.federalreserve.gov'
s=BeautifulSoup((ROOT/'location03-private/fed-archive.html').read_bytes(),'html.parser')
rows=[]
for h in s.select('h5.panel-heading'):
 t=h.get_text(strip=True)
 if t.isdigit() and 1997<=int(t)<=2024:
  for a in h.parent.select('a[href]'):
   m=a.get_text(strip=True);url=urljoin(base,a['href']); rid=t+'-'+m
   rows.append({'release_id':rid,'survey_year':int(t),'survey_month':m,'original_url':url,'scope':'candidate' if int(t)>=2013 else 'excluded_pre_panel_clean_period'})
rows=sorted(rows,key=lambda x:x['release_id']);
with (out/'sloos_release_universe.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
(raw/'universe.json').write_text(json.dumps(rows,indent=2))
def download(url,p):
 if p.exists() and p.stat().st_size>100:return
 temp=p.with_suffix(p.suffix+'.part')
 r=subprocess.run(['curl','--fail','--silent','--show-error','--max-time','35',url,'-o',str(temp)],capture_output=True,text=True)
 if r.returncode:raise RuntimeError(f'{url}: {r.stderr}')
 temp.replace(p)
def one(row):
 rid=row['release_id'];d=raw/rid;d.mkdir(exist_ok=True);download(row['original_url'],d/'main.html')
 soup=BeautifulSoup((d/'main.html').read_bytes(),'html.parser')
 candidates=[];pdfs=[]
 for a in soup.find_all('a',href=True):
  t=a.get_text(' ',strip=True).lower();u=urljoin(row['original_url'],a['href'])
  if re.fullmatch(r'table\s*1',t):candidates.append(u)
  if re.fullmatch(r'table\s*1\s*\(pdf\)',t):pdfs.append(u)
 if candidates:download(candidates[0],d/'table1.html')
 if pdfs:download(pdfs[0],d/'table1.pdf')
 manifest={'release':row,'table_url':candidates[0] if candidates else None,'table_pdf_url':pdfs[0] if pdfs else None}
 (d/'manifest.json').write_text(json.dumps(manifest,indent=2));return rid
start=time.monotonic();todo=[x for x in rows if x['scope']=='candidate' or x['survey_year']==2012]
errors=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 fs={ex.submit(one,x):x for x in todo}
 for i,f in enumerate(concurrent.futures.as_completed(fs),1):
  try: rid=f.result();print(f'ACQUIRE {i}/{len(todo)} elapsed={time.monotonic()-start:.1f}s release={rid} output={raw}',flush=True)
  except Exception as e:errors.append({'release':fs[f]['release_id'],'error':str(e)});print('FAILED',errors[-1],flush=True)
  (raw/'acquisition_status.json').write_text(json.dumps({'completed':i,'total':len(todo),'errors':errors},indent=2))
print('DONE',len(rows),'universe',len(todo),'attempted','errors',len(errors),flush=True)

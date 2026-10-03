"""Executive summary: resumable official SPD originals; never forecasting labels."""
import argparse,csv,datetime,hashlib,json,time,subprocess
from pathlib import Path
from urllib.parse import urljoin,urlparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'backtesting/location04/results'
ARCHIVE='https://www.newyorkfed.org/markets/market-intelligence/survey-of-market-expectations'
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
def write_csv(p,rows):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def status(stage,**kw):
 p=OUT.parent/'STATUS.json';d=json.loads(p.read_text());d['current_stage']=stage;d.update(kw);d['last_update']=datetime.datetime.now(datetime.UTC).isoformat();save(p,d)
def official(url):return urlparse(url).hostname in ['www.newyorkfed.org','resources.newyorkfed.org','www.federalreserve.gov']
def fetch(private,relative,url):
 assert official(url),url
 p=private/'source'/relative;receipt=p.with_suffix(p.suffix+'.receipt.json')
 if p.exists() and receipt.exists():
  d=json.loads(receipt.read_text());assert hashlib.sha256(p.read_bytes()).hexdigest()==d['sha256'];return d
 p.parent.mkdir(parents=True,exist_ok=True)
 r=requests.get(url,timeout=(15,60));r.raise_for_status();assert official(r.url),r.url
 if p.suffix=='.pdf' and not r.content.startswith(b'%PDF'):raise ValueError('Non-PDF response '+url)
 temp=p.with_suffix(p.suffix+'.part');temp.write_bytes(r.content);temp.replace(p)
 d={'path':relative,'url':url,'resolved_url':r.url,'retrieved_at':datetime.datetime.now(datetime.UTC).isoformat(),'sha256':hashlib.sha256(r.content).hexdigest(),'bytes':len(r.content),'rights':'Copyright Federal Reserve Bank of New York; private research copy, original attribution retained; not relicensed as MIT'};save(receipt,d)
 return d
def enumerate_rounds(private):
 p=private/'source/archive.html'
 if not p.exists():fetch(private,'archive.html',ARCHIVE)
 soup=BeautifulSoup(p.read_bytes(),'html.parser');table=next(t for t in soup.find_all('table') if 'Survey of Primary Dealers' in t.get_text())
 year=None;rows=[]
 for tr in table.find_all('tr'):
  cells=tr.find_all(['td','th'],recursive=False)
  if not cells:continue
  label=cells[0].get_text(' ',strip=True)
  if label.isdigit() and len(label)==4:year=int(label);continue
  if year is None or not cells[1:]:continue
  links=cells[1].find_all('a');questions=next((a.get('href') for a in links if a.get_text(strip=True)=='Questions'),None);results=next((a.get('href') for a in links if a.get_text(strip=True)=='Results'),None)
  if not results:continue
  smp=next((a.get('href') for a in cells[2].find_all('a') if a.get_text(strip=True)=='Results'),None) if len(cells)>2 else None
  rows.append({'survey_id':f'{year}-{label.replace("*","").replace("/","-")}','year':year,'reference_period':label.replace('*',''),'appendix_update_marker':'*' in label,'panel':'SPD','question_url':urljoin(ARCHIVE,questions),'results_url':urljoin(ARCHIVE,results),'SMP_url_excluded':urljoin(ARCHIVE,smp) if smp else '', 'SURVEY_DISTRIBUTED_AT':'','SURVEY_DUE_AT':'','FOMC_EVENT_DATE':'','RESULT_PUBLIC_AVAILABLE_AT':'','publication_evidence':'pending','extraction_status':'pending','original_document_type':'PDF','source_hash':'pending','retrieval_timestamp':'pending'})
 rows.sort(key=lambda r:(r['year'],r['results_url']));assert len(rows)==len({r['survey_id'] for r in rows});write_csv(OUT/'spd_release_universe.csv',rows);status('official_source_universe',discovered_rounds=len(rows));print('UNIVERSE',len(rows),flush=True);return rows
def acquire(private,years):
 rows=list(csv.DictReader((OUT/'spd_release_universe.csv').open()));jobs=[]
 for r in rows:
  if int(r['year']) in years:
   for kind in ['question','results']:jobs.append((r['survey_id'],kind,r[kind+'_url']))
 start=time.monotonic();documents=[]
 def one(job):
  rid,kind,url=job;d=fetch(private,rid+'/'+kind+'.pdf',url);p=private/'source'/d['path'];txt=p.with_suffix('.txt')
  if not txt.exists():subprocess.run(['pdftotext','-layout',str(p),str(txt)],check=True,timeout=30)
  return dict(d,survey_id=rid,kind=kind,panel='SPD',type='original PDF')
 with ThreadPoolExecutor(max_workers=4) as pool:
  pending={pool.submit(one,j):j for j in jobs}
  for i,f in enumerate(as_completed(pending),1):
   job=pending[f]
   try:d=f.result()
   except Exception as e:
    save(private/'acquisition_failure.json',{'stage':'acquisition','job':job,'error':str(e),'completed':i-1});raise
   documents.append(d);save(private/('acquisition-'+str(min(years))+'-'+str(max(years))+'.json'),documents);status('original_result_acquisition',completed_source_files=i,total_source_files=len(jobs),current_survey=job[0]);print(f'ACQUIRE {i}/{len(jobs)} elapsed={time.monotonic()-start:.1f}s survey={job[0]} kind={job[1]} output={d["path"]}',flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--private',type=Path,required=True);ap.add_argument('--enumerate',action='store_true');ap.add_argument('--years',type=int,nargs='+');a=ap.parse_args()
 if a.enumerate:enumerate_rounds(a.private)
 if a.years:acquire(a.private,a.years)

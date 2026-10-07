"""Executive summary: Gate A uses source documents and calendar availability only."""
from pathlib import Path
from urllib.parse import urljoin
import argparse,json,re,time,datetime,subprocess
import numpy as np,pandas as pd,requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from .source import *
def run(private,start=0,stop=999):
 p=Path(private);parent=p/'parent-extracted/private';docs=parent/'documents';source=p/'source';source.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
 # Enumerate links actually present on saved official conference/calendar documents.
 links={};evidence=[]
 for f in sorted(docs.glob('*.html')):
  if not (f.stem.startswith('fomc') or f.stem.startswith('conference')):continue
  soup=BeautifulSoup(f.read_text(errors='replace'),'html.parser')
  for a in soup.find_all('a',href=True):
   m=re.search(r'fomcprojtabl(?:e)?(20\d{6})\.(?:htm|pdf)',a['href'])
   if m and 2016<=int(m[1][:4])<=2024:
    stamp=m[1];links.setdefault(stamp,{})['pdf' if a['href'].endswith('.pdf') else 'html']=urljoin('https://www.federalreserve.gov',a['href']);evidence.append({'path':str(f.relative_to(parent)),'SHA256':digest(f),'round':stamp})
 # Parent inventory also records original links from official archive traversal.
 for u in json.loads((parent/'sep_links_full.json').read_text()):
  stamp=re.search(r'20\d{6}',u)[0]
  if 2016<=int(stamp[:4])<=2024:links.setdefault(stamp,{}).setdefault('html',u)
 universe=[dict(release_id='SEP_'+str(pd.Timestamp(k).date()),release_date=str(pd.Timestamp(k).date()),round=k,**v) for k,v in sorted(links.items())]
 csv(OUT/'source_release_universe.csv',universe)
 save(OUT/'enumeration_evidence.json',{'executive_summary':'Actual official archive links, not an assumed round count. March2020 has no SEP projection release.','release_count':len(universe),'archive_links':evidence,'parent_links_manifest_SHA256':digest(parent/'sep_links_full.json')})
 begun=time.monotonic()
 for j,row in enumerate(universe):
  if not start<=j<stop:continue
  stamp=row['round'];pdf=source/('sep_'+stamp+'.pdf');receipt=pdf.with_suffix('.pdf.receipt.json')
  if not pdf.exists():
   if 'pdf' not in row:raise ValueError('Official PDF link absent '+stamp)
   result=requests.get(row['pdf'],timeout=40);result.raise_for_status()
   if not result.content.startswith(b'%PDF'):raise ValueError('Not original PDF '+stamp)
   pdf.write_bytes(result.content)
  if not receipt.exists():save(receipt,{'url':row.get('pdf'),'SHA256':digest(pdf),'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'official_original_dated_path':True})
  print('SEP acquisition',j+1,'/',len(universe),stamp,'elapsed',round(time.monotonic()-begun,1),'output',pdf,flush=True)
 if not all((source/('sep_'+r['round']+'.pdf')).exists() for r in universe):return
 states=[];pit=[];documents=[];early=[]
 for row in universe:
  stamp=row['round'];html=docs/('sep_'+stamp+'.html');pdf=source/('sep_'+stamp+'.pdf')
  if not html.exists():raise ValueError('Saved original accessible table absent '+stamp)
  state=parse(html.read_text(errors='replace'),row['release_date'])
  layout=pdf.with_suffix('.layout.txt')
  subprocess.run(['pdftotext','-layout','-f','1','-l','2',str(pdf),str(layout)],check=True,timeout=30)
  text=layout.read_text()
  # First-two-page dated advance table must substantiate publication and the same printed medians.
  line=next((l for l in text.splitlines() if 'Federal funds rate' in l),'')
  numbers=re.findall(r'(?<![A-Za-z])(?:\d+\.\d+|\.\d+)',line)
  if len(numbers)<2 or not np.allclose([float(numbers[0]),float(numbers[1])],[state['CY'],state['NCY']],atol=1e-12,rtol=0):raise ValueError('Original PDF/HTML policy mismatch '+stamp+' '+line)
  expected=pd.Timestamp(row['release_date']).strftime('%B %d %Y').replace(' 0',' ')
  compact=lambda s:re.sub(r'[^A-Za-z0-9]','',s)
  if 'release' not in text.lower() or compact(expected) not in compact(text):raise ValueError('Exact dated release evidence absent '+stamp)
  main=BeautifulSoup(html.read_text(),'html.parser').find('main')
  body=main.get_text(' ',strip=True) if main else BeautifulSoup(html.read_text(),'html.parser').get_text(' ',strip=True)
  # Ordinary "previous projection" comparisons are not amendments.
  warning=bool(re.search(r'\berrat(?:a|um)\b|\bcorrected\b|\bcorrection\b|\breposted\b',body,re.I))
  state['active']=not warning;state['version']=0;state['original_pdf_SHA256']=digest(pdf);state['original_html_SHA256']=digest(html)
  state['field_confidence']='PDF first-two-page policy medians match header-resolved original accessible table'
  states.append(state)
  pit.append({**state,'original_url':row.get('pdf'),'publication_evidence':text[:180].replace('\n',' '),'publication_time_rule':'Conservative release-date EOD, NY; never infer from retrieval/meeting alone','original_status':'Dated original-release PDF corroborated by accessible table; PIT B','errata_status':'WARNING_INACTIVE' if warning else 'No field correction notice identified in selected original text; absence is not immutable proof','available':not warning})
  for f,u in [(pdf,row.get('pdf')),(html,row['html'])]:documents.append({'path':str(f),'URL':u,'SHA256':digest(f),'round':stamp,'rights':'Fed Board public-domain information with attribution; no affiliation/logo claim'})
  print('SEP verify',stamp,'CY',state['CY'],'NCY',state['NCY'],'active',state['active'],flush=True)
 # Inspect all six previously unparsed originals; 2015 is outside primary release scope.
 for stamp in ['20150318','20150617','20150917','20151216','20160316','20160615']:
  try:old=parse((docs/('sep_'+stamp+'.html')).read_text(),str(pd.Timestamp(stamp).date()));early.append({**old,'primary_scope':stamp[:4]!='2015','parser_fix':'Support td row-stubs and explicit median/year headers; source definition unchanged'})
  except ValueError as e:early.append({'round':stamp,'active':False,'error':str(e)})
 save(OUT/'early_original_audit.json',{'executive_summary':'Investigated original tables before outcomes; no release chosen by performance.','documents':early})
 states=canonical(states);save(p/'source_states.json',states);csv(OUT/'source_pit_ledger.csv',pit)
 save(OUT/'source_document_manifest.json',{'executive_summary':'Original official source bytes; all publication dates are evidenced by dated release PDFs.','documents':documents})
 usable=[r for r in states if r['active']];byyear={y:sum(int(r['CY_target'])==y for r in usable) for y in range(2016,2025)}
 # Criterion is source-only: >=8 development release events, >=2/year in all five eval years and >=2 distinct state values.
 ready=sum(byyear[y] for y in range(2016,2020))>=8 and all(byyear[y]>=2 for y in YEARS) and len(set(r['value'] for r in usable))>=2 and len(states)==len(universe)
 criterion={'minimum_development_releases':8,'minimum_per_eval_year':2,'minimum_distinct_policy_values':2,'chosen_before_outcomes':True,'does_not_claim_statistical_power':True}
 readiness={'executive_summary':'Gate A based exclusively on source originals/availability. PIT B is reconstructibility, not an immutable first-download archive.','DATASET_READY':bool(ready),'release_universe':len(universe),'usable_releases':len(usable),'releases_by_year':byyear,'source_only_state_changes':sum(a['value']!=b['value'] for a,b in zip(usable,usable[1:])),'adequate_sample_criterion':criterion,'publication_EOL_NY':True,'max_source_age_business_days':90,'original_PDF_HTML_fields_agree':True,'no_current_history_substitution':True,'rights_evidence':'Official Board disclaimer public-domain copying/distribution with attribution + organizer DATA-LICENSE Fed projections category','offline_research_feasible':True,'official_submission_readiness':False,'future_labels_read':False,'errata_limit':'Known corrected originals fail closed. No claim to prove nonexistence of undisclosed replacements.','PIT':'B'}
 save(OUT/'source_readiness.json',readiness)
 save(OUT/'source_dataset_manifest.json',{'executive_summary':'Deterministically parsed original source state, constant until next release, no January retargeting.','states_SHA256':digest(p/'source_states.json'),'states':states,'source_only_criterion':criterion,'parser_SHA256':digest(Path(__file__).with_name('source.py'))})
 save(OUT.parent/'STATUS.json',{'executive_summary':'Gate A completed before labels or models.','branch':'track2/persistent-direction-state-02','HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'current_stage':'SOURCE_GATE_COMPLETE','completed_stages':['environment','parent_recovery','source_acquisition','PIT','source_readiness'],'pending_stages':['implementation','tests','PRE','evaluation','controls','bootstrap','report','Git','recovery'],'last_successful_artifact':'source_readiness.json','last_update':datetime.datetime.now(datetime.timezone.utc).isoformat()})
 print('GATE A',readiness,flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('private');a.add_argument('--start',type=int,default=0);a.add_argument('--stop',type=int,default=999);q=a.parse_args();run(q.private,q.start,q.stop)

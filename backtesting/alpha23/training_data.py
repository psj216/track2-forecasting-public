"""Executive summary: one official historical panel plus later Treasury dates; labels kept external."""
import pathlib,json,hashlib,io,re,sys
import pandas as pd
from bs4 import BeautifulSoup
from policy_signal import signals
ASSETS=['UST_3M','UST_6M','UST_1Y','UST_2Y','UST_5Y','UST_7Y','UST_10Y','UST_20Y','UST_30Y']
COLS=['3 Mo','6 Mo','1 Yr','2 Yr','5 Yr','7 Yr','10 Yr','20 Yr','30 Yr']
PANEL='t2-F2-curve-ust6m-004-ps1/rates_daily.parquet'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def prepare(official,raw,out):
 official=pathlib.Path(official);raw=pathlib.Path(raw);out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True)
 p=official/'units'/PANEL;d=pd.read_parquet(p);d['date']=pd.to_datetime(d.date);frame=d.pivot(index='date',columns='asset',values='value').reindex(columns=ASSETS)
 source=[{'path':str(p),'sha256':sha(p),'last_date':str(frame.index.max().date())}];end=frame.index.max();extra=[]
 for y in range(2024,2027):
  f=raw/f'treasury-{y}.html'
  try:t=pd.read_html(io.StringIO(f.read_text()),flavor='lxml')[0]
  except ValueError:
   source.append({'path':str(f),'sha256':sha(f),'status':'NO_TABLE_SOURCE_UNAVAILABLE'});continue
  t['Date']=pd.to_datetime(t.Date);t=t.set_index('Date')[COLS].apply(pd.to_numeric,errors='coerce');t.columns=ASSETS
  extra.append(t.loc[t.index>end]);source.append({'path':str(f),'sha256':sha(f)})
 frame=pd.concat([frame]+extra).sort_index();assert not frame.index.duplicated().any();frame=frame.loc[:'2026-10-22'];frame.to_parquet(out/'curve.parquet')
 seen={}
 for idx in (official/'units').glob('*/text/corpus_index.json'):
  for e in json.loads(idx.read_text()).get('documents',[]):
   if e.get('doc_type') not in ['fomc_statement','fomc_minutes'] or 'Federal Reserve' not in e.get('source',''):continue
   f=idx.parent/e['file'];h=sha(f);rec=seen.setdefault(h,{'sha256':h,'dates':set(),'kind':e['doc_type'],'path':str(f),'text':f.read_text()});rec['dates'].add(e['timestamp'][:10])
 docs=[];excluded=[]
 for v in seen.values():
  if len(v['dates'])!=1:excluded.append({'sha256':v['sha256'],'reason':'CONFLICTING_DATES'});continue
  date=next(iter(v.pop('dates')));v.update(date=date,active=str((pd.Timestamp(date)+pd.offsets.BDay(1)).date()),signals=signals(v['text']));docs.append(v)
 for f in sorted(raw.glob('fed-*.html')):
  date=pd.Timestamp(f.stem[4:]);soup=BeautifulSoup(f.read_text(),'html.parser');body=soup.select_one('#article') or soup.select_one('main')
  if body is None:raise ValueError('no statement body '+str(f))
  text=body.get_text(' ',strip=True);assert 'Federal Reserve issues FOMC statement' in text
  docs.append({'sha256':sha(f),'date':str(date.date()),'active':str((date+pd.offsets.BDay(1)).date()),'kind':'fomc_statement','path':str(f),'text':text,'signals':signals(text)})
 (out/'documents.json').write_text(json.dumps(docs,indent=2))
 manifest={'executive_summary':'Exploratory current-vintage official curve and metadata-dated policy documents. No claim of authenticated PIT.','assets':ASSETS,'source':source,'curve_sha256':sha(out/'curve.parquet'),'rows':len(frame),'range':[str(frame.index.min()),str(frame.index.max())],'missing_by_asset':frame.isna().sum().to_dict(),'docs':[{k:v for k,v in x.items() if k!='text'} for x in docs],'excluded_documents':excluded,'PIT':'CURRENT_VINTAGE_METADATA_DATED_NOT_AUTHENTICATED'}
 (out/'dataset-manifest.json').write_text(json.dumps(manifest,indent=2));print('curve',len(frame),'docs',len(docs),'missing',frame.isna().sum().to_dict(),flush=True)
if __name__=='__main__':prepare(*sys.argv[1:])

"""Executive summary: original published SPD modes; deterministic source-only five features."""
from pathlib import Path
import datetime,hashlib,re,json,calendar,csv
import numpy as np,pandas as pd
from .acquire import save,write_csv
FEATURES=('POLICY_NEAR','POLICY_FAR','POLICY_PATH_SLOPE','POLICY_REVISION_SAME_TARGET','SOURCE_AGE_BUSINESS_DAYS')
MONTHS={'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12}
STATISTIC='DIRECT_PUBLISHED_MEDIAN_OF_DEALER_MODAL_TARGET_RATE_OR_RANGE_MIDPOINT_PERCENT'
MODE=re.compile(r'most likely outcome[^\n]+mode',re.I)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def activation(date):return pd.Timestamp(date+'T23:59:59',tz='America/New_York')
def cutoff(origin):return (pd.Timestamp(origin)-pd.offsets.BDay(1)).tz_localize('America/New_York')+pd.Timedelta(hours=16)
def eligible_panel(rows):return [dict(r) for r in rows if r.get('panel')=='SPD']
def publication_after_minutes(date):
 from pandas.tseries.holiday import USFederalHolidayCalendar
 return (pd.Timestamp(date)+pd.offsets.CustomBusinessDay(calendar=USFederalHolidayCalendar())).date().isoformat()
def source_dates(text,year):
 hits=re.findall(r'Distributed\s*:\s*(\d{1,2}/\d{1,2}/\d{4})[^\n]*Received by\s*:\s*(\d{1,2}/\d{1,2}/\d{4})',text,re.I)
 valid=[(pd.Timestamp(a).date().isoformat(),pd.Timestamp(b).date().isoformat()) for a,b in hits if pd.Timestamp(a).year==year and pd.Timestamp(b).year==year]
 if len(set(valid))!=1:raise ValueError('Unresolved source distribution/deadline '+str((year,hits)))
 return valid[0],{'hidden_template_date_conflict':len(hits)!=len(valid),'all_date_pairs':hits}
def target_date(label,base_year,previous_month=None):
 label=label.replace('–','-').replace('−','-');label=re.sub(r'\bdun\b','Jun',label,flags=re.I);label=re.sub(r'\bdul\b','Jul',label,flags=re.I);label=re.sub(r'([QH])([1-4])\s+(20\d{2})',r'\3 \1\2',label);label=re.sub(r'(20\d{2})\s*[a0]([1-4])',r'\1 Q\2',label);label=re.sub(r'\b(20\d{2})\s*([1-4])\b',r'\1 Q\2',label)
 q=re.search(r'(20\d{2})\s*([QH])\s*([1-4])',label,re.I)
 if q:
  year,kind,n=int(q[1]),q[2].upper(),int(q[3]);month=n*(3 if kind=='Q' else 6)
  if month>12:raise ValueError('Invalid half-year '+label)
  return datetime.date(year,month,calendar.monthrange(year,month)[1]).isoformat(),kind+str(n),year,month
 names=list(re.finditer(r'\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?',label,re.I))
 if names:
  m=names[-1];month=MONTHS[m[1][:3].lower()];years=re.findall(r'\b(20\d{2})\b',label);year=int(years[-1]) if years else base_year+(previous_month is not None and month<previous_month)
  tail=re.sub(r'\b20\d{2}\b','',label[m.end():]);days=re.findall(r'\b\d{1,2}\b',tail)
  if not days:
   before=re.findall(r'\b\d{1,2}\b',label[:m.start()]);days=before[-1:] if before else []
  if not days:raise ValueError('Target month has no explicit event day '+label)
  day=int(days[-1]);return datetime.date(year,month,day).isoformat(),'FOMC',year,month
 years=re.findall(r'\b(20\d{2})\b',label)
 if len(set(years))==1:return years[0]+'-12-31','YEAR_END',int(years[0]),12
 raise ValueError('Unresolved explicit target '+repr(label))
def mode_block(text):
 m=MODE.search(text)
 if not m:return None
 rest=text[m.start():];b=re.search(r'(?m)^\s*\d+[b-z]\)|(?m:^\s*If your responses)|In addition',rest,re.I);return rest[:b.start()] if b else rest[:6000]
def plain_tables(text,year):
 block=mode_block(text)
 if not block or 'midpoint' not in block[:1000].lower():return []
 lines=block.splitlines();tables=[]
 for index,line in enumerate(lines):
  if not re.match(r'^\s*Median\b',line):continue
  values=list(re.finditer(r'[-+]?\d+(?:\.\d+)?%',line))
  if len(values)<2:continue
  centers=np.array([(m.start()+m.end())/2 for m in values]);bounds=np.r_[(centers[0]-(centers[1]-centers[0])/2),(centers[:-1]+centers[1:])/2,centers[-1]+(centers[-1]-centers[-2])/2]
  upper=index-1
  while upper>=0 and (not lines[upper].strip() or re.match(r'^\s*25th\b',lines[upper])):upper-=1
  header=[h for h in lines[max(0,upper-3):upper+1] if '%' not in h and 'Responses' not in h];labels=[]
  bounds[0]=0;bounds[-1]=10000
  for j in range(len(values)):
   parts=[h[max(0,int(bounds[j])):int(bounds[j+1])].strip() for h in header];labels.append(' '.join(p for p in parts if p))
  for h in header:
   months=r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?';dates=re.findall(months+r'\s*\d{1,2}(?:\s*-\s*(?:'+months+r'\s*)?\d{1,2})?',h)
   if len(dates)==len(values):
    yearline=next((re.findall(r'\b20\d{2}\b',hh) for hh in header if len(re.findall(r'\b20\d{2}\b',hh))==len(values)),None)
    labels=[d+(' '+yearline[j] if yearline else '') for j,d in enumerate(dates)];break
   targets=re.findall(r'20\d{2}\s+[QH]\d',h)
   if len(targets)==len(values):labels=targets;break
   years=re.findall(r'\b20\d{2}\b',h)
   if len(years)==len(values) and all(re.match(r'^\s*(20\d{2}\s+)+$',h) for _ in [0]):labels=years;break
  tables.append((labels,[float(m[0][:-1]) for m in values],'PDF_TEXT_LAYOUT'))
 return tables

def ocr_tables(private,rid):
 receipt=json.loads((private/'ocr'/rid/'receipt.json').read_text());df=pd.read_csv(private/receipt['OCR_tsv'],sep='\t',keep_default_na=False);df=df.loc[(df.level==5)&(df.text!='')];groups=[g for _,g in df.groupby(['block_num','par_num','line_num'],sort=False)];medians=[]
 end=next((int(g.top.min()) for g in groups if re.match(r'^\d+b\)',str(g.iloc[0].text))),10**9)
 for g in groups:
  if str(g.iloc[0].text).lower()!='median' or int(g.top.min())>=end:continue
  v=g.loc[g.text.str.match(r'^[-+]?\d+\.\d+%$')]
  if len(v)<2:continue
  centers=v.left.to_numpy()+v.width.to_numpy()/2;bounds=np.r_[centers[0]-(centers[1]-centers[0])/2,(centers[:-1]+centers[1:])/2,centers[-1]+(centers[-1]-centers[-2])/2];y=int(g.top.min());header=df.loc[(df.top<y-22)&(df.top>y-160)&~df.text.str.contains('%')];labels=[]
  for i in range(len(v)):
   xx=header.left+header.width/2;h=header.loc[(xx>=bounds[i])&(xx<bounds[i+1])].sort_values(['top','left']);labels.append(' '.join(h.text.tolist()))
  medians.append((labels,[float(x[:-1]) for x in v.text],'PDF_RASTER_OCR_VERIFIED'))
 return medians

def policy_rows(private,row):
 text=(private/'source'/row['survey_id']/'results.txt').read_text();block=mode_block(text)
 if not block:block=mode_block((private/'source'/row['survey_id']/'question.txt').read_text())
 if not block or 'midpoint' not in block[:1000].lower():return [],'NONCANONICAL_SPLIT_RANGE_OR_PROBABILITY_ONLY'
 tables=plain_tables(text,int(row['year']))
 if not tables:tables=ocr_tables(private,row['survey_id'])
 fields=[];year=int(row['year']);month=None
 for tab,(labels,values,method) in enumerate(tables):
  for j,(label,value) in enumerate(zip(labels,values)):
   date,kind,year,month=target_date(label,year,month);fields.append({'survey_id':row['survey_id'],'panel':'SPD','raw_target_label':label,'target_event_date':date,'target_kind':kind,'representation':STATISTIC,'units':'percent','published_value':value,'extraction_method':method,'table_index':tab,'column_index':j,'is_primary_policy_family':True,'future_at_publication':date>row['RESULT_PUBLIC_AVAILABLE_AT'][:10],'eligible_within_180_days':0<(pd.Timestamp(date)-pd.Timestamp(row['RESULT_PUBLIC_AVAILABLE_AT'][:10])).days<=180,'questionnaire_family':'own modal federal funds policy path; excludes SEP projections and conditional distributions'})
 if not fields:raise ValueError('No canonical numerical path '+row['survey_id'])
 dates=[x['target_event_date'] for x in fields]
 if dates!=sorted(dates) or len(dates)!=len(set(dates)):raise ValueError('Unordered/duplicate explicit targets '+row['survey_id'])
 return fields,'EXTRACTED_CANONICAL'
def state_from_release(row,fields,previous):
 date=row['RESULT_PUBLIC_AVAILABLE_AT'][:10];future=sorted([f for f in fields if f['target_event_date']>date],key=lambda f:f['target_event_date']);far=[f for f in future if (pd.Timestamp(f['target_event_date'])-pd.Timestamp(date)).days<=180];near=future[0] if future else None;last=far[-1] if far else None
 previous_fields={f['target_event_date']:f for f in previous if f['representation']==STATISTIC}
 old=previous_fields.get(near['target_event_date']) if near else None
 active=original_fields_admissible(row.get('material_primary_amendment',False),row.get('original_recovered',False)) and near is not None and last is not None and near['target_event_date']!=last['target_event_date'] and old is not None
 return {'release_id':row['survey_id'],'panel':'SPD','publication_date':date,'available_at':row['RESULT_PUBLIC_AVAILABLE_AT'],'representation':STATISTIC,'near_target_date':near['target_event_date'] if near else None,'far_target_date':last['target_event_date'] if last else None,'revision_target_date':near['target_event_date'] if near else None,'POLICY_NEAR':near['published_value'] if near else None,'POLICY_FAR':last['published_value'] if last else None,'POLICY_PATH_SLOPE':last['published_value']-near['published_value'] if near and last else None,'POLICY_REVISION_SAME_TARGET':near['published_value']-old['published_value'] if near and old else None,'full5_usable_at_release':bool(active)}
def asof_features(states,origin):
 c=cutoff(origin);eligible=[s for s in states if s.get('panel')=='SPD' and pd.Timestamp(s['available_at'])<=c]
 if not eligible:return None
 s=dict(max(eligible,key=lambda x:x['available_at']));age=int(np.busday_count(np.datetime64(s['publication_date']),np.datetime64(str(c.date()))));s['SOURCE_AGE_BUSINESS_DAYS']=age
 if age>70 or not s['full5_usable_at_release'] or any(s[k] is None for k in FEATURES):return None
 s['cutoff']=c.isoformat();return s

def original_fields_admissible(amended,original_recovered):return not amended or original_recovered

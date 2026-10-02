"""## Executive summary (read this first)

Validate real survey snapshots against dated original first-release GDP.
"""
from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd,numpy as np,json,re,hashlib,datetime
import argparse
p=argparse.ArgumentParser();p.add_argument('--private',type=Path,required=True);P=p.parse_args().private
def dump(n,v): (P/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
dates=json.loads((P/'spf-publication-dates.json').read_text());families=['RGDP','CPI','UNEMP','TBILL','TBOND'];snaps=[]
for fam in families:
 d=pd.read_excel(P/('medianGrowth.xlsx' if fam=='RGDP' else 'medianLevel.xlsx'),sheet_name=fam)
 for _,r in d[(d.YEAR>=1998)&(d.YEAR<=2024)].iterrows():
  y,q=int(r.YEAR),int(r.QUARTER);key=f'{y}Q{q}';pub=dates[key];prefix='drgdp' if fam=='RGDP' else fam
  cur,nxt=float(r[prefix+'2']),float(r[prefix+'3'])
  assert np.isfinite([cur,nxt]).all()
  quarter=pd.Period(key,freq='Q')
  for offset,value in [(0,cur),(1,nxt)]:
   snaps.append(dict(source_id='PHIL_SPF',family=fam,target=str(quarter+offset),publication_date=pub,value=value,unit='annualized_qoq_percent' if fam in ['RGDP','CPI'] else 'percent',survey_id=key,document_sha256=sha(P/'reports'/f'{y}q{q}.pdf'),snapshot_kind='actual_survey_median'))
dump('survey_snapshots.json',snaps)
actuals=[];reject=[];audit=[];check=pd.read_excel(P/'routput_first_second_third.xlsx',sheet_name='DATA',header=4)
first={str(r.Date):r.First for _,r in check.iterrows()}
for f in sorted((P/'bea').glob('*.html')):
 key=f.stem;y,q=int(key[:4]),int(key[-1]);s=BeautifulSoup(f.read_text(),'html.parser');text=s.get_text(' ',strip=True)
 path=f
 if key=='1999q1':path=P/'bea/1999q1-original.txt';text=path.read_text()
 elif key in ['1998q1','1998q2','1998q3']:path=P/'bea'/f'{key}.txt';text=path.read_text()
 text=re.sub(r'\s+',' ',text);i=text.lower().find('real gross domestic product');sub=text[i:i+1300]
 match=re.search(r'(increased|decreased|grew|contracted)\s+(?:at\s+)?(?:an annual rate of\s+)?([\d.]+)\s+percent',sub,re.I)
 dm=re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',text[:text.lower().find('real gross domestic product')],re.I)
 if not match or not dm:reject.append(dict(event=key,reason='unparsed original first release/date',snippet=sub[:250]));continue
 val=float(match[2])*(-1 if match[1].lower() in ['decreased','contracted'] else 1);date=pd.Timestamp(' '.join(dm.groups())).strftime('%Y-%m-%d')
 cv=first.get(f'{y}:Q{q}');gap=abs(val-float(cv)) if cv is not None and np.isfinite(cv) else None
 if gap is None or gap>.055:reject.append(dict(event=key,reason='original headline vs first-vintage validation mismatch',actual=val,support_first=cv,gap=gap));continue
 assert pd.Timestamp(date)>pd.Period(f'{y}Q{q}').end_time
 actuals.append(dict(event_id='GDP_'+f'{y}Q{q}',family='RGDP',target=f'{y}Q{q}',release_date=date,value=val,unit='annualized_qoq_percent',vintage='first',document_sha256=sha(path),document=str(path.relative_to(P)),support_gap=gap))
 audit.append(dict(event=key,release_date=date,headline_unit_match=True,first_vintage_match=True,gap=gap))
dump('first_actuals.json',actuals);dump('first_release_validation.json',dict(accepted=len(actuals),rejected=reject,events=audit))
print(json.dumps(dict(snapshots=len(snaps),events=len(actuals),reject=reject),indent=2))

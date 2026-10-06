"""Executive summary: extract pre-outcome source fields from official originals; preserve timing caveats."""
from pathlib import Path
import json,re,zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from .core import available_eod

def sep_fields(html,release_date):
    soup=BeautifulSoup(html,'html.parser')
    for table in soup.select('table'):
        head=table.find('thead')
        if head is None or 'Median' not in head.get_text():continue
        median=head.find(string=re.compile('Median'))
        if median is None:continue
        col=median.find_parent('th');ident=col.get('id');span=int(col.get('colspan',1))
        headers=[x for x in head.select('th') if ident in x.get('headers',[])]
        years=[x.get_text(' ',strip=True) for x in headers][:span]
        for row in table.select('tbody tr'):
            th=row.find('th')
            if th is not None and re.match(r'^Federal funds rate',th.get_text(' ',strip=True)):
                values=[x.get_text(' ',strip=True) for x in row.select('td')][:span]
                mapping={int(y):float(v) for y,v in zip(years,values) if re.fullmatch(r'20\d{2}',y)}
                yr=int(str(release_date)[:4])
                if yr not in mapping or yr+1 not in mapping:raise ValueError('Explicit CY / NCY median absent')
                return {'date':str(release_date),'available_at':available_eod(release_date).isoformat(),'source_state_id':'SEP_'+str(release_date),'value':mapping[yr+1]-mapping[yr],'medians_by_target_year':mapping,'recipe':'release-year NCY median minus CY median; constant until next release, no rollover redefinition'}
    raise ValueError('No original median Federal funds rate table')

def h41_reserves(html):
    soup=BeautifulSoup(html,'html.parser')
    # Screen-reader release has one explicit row; Wednesday is its last numeric column.
    for pre in soup.find_all('pre'):
        for line in pre.get_text().splitlines():
            if line.strip().startswith('Reserve balances with Federal Reserve Banks'):
                nums=re.findall(r'-?\d[\d,]*',line)
                if len(nums)>=4:return float(nums[-1].replace(',',''))
    for tr in soup.select('tr'):
        cells=tr.find_all(['td','th'],recursive=False)
        if not cells:continue
        if 'Reserve balances with Federal Reserve Banks' in cells[0].get_text(' ',strip=True):
            # Printed tables split +/- signs into extra cells; last numeric cell remains Wednesday.
            nums=[re.sub(r'[^0-9-]','',c.get_text()) for c in cells[1:]];nums=[x for x in nums if re.fullmatch('-?\\d+',x)]
            if len(nums)>=4:return float(nums[-1])
    raise ValueError('Wednesday reserve-balance field absent')

def mpt_state(path,cutoff='2024-12-18'):
    with zipfile.ZipFile(path) as z:
        texts=[]
        for name in z.namelist():
            if name.startswith('xl/drawings/') and name.endswith('.xml'):
                texts.extend(n.text or '' for n in ET.fromstring(z.read(name)).iter() if n.tag.endswith('}t'))
    license_text='\n'.join(texts)
    bounded=Path(path).with_name('mpt_bounded.csv')
    if bounded.exists():
        frame=pd.read_csv(bounded)
    else:
        import openpyxl
        workbook=openpyxl.load_workbook(path,read_only=True,data_only=True);sheet=workbook['DATA'];sheet.reset_dimensions();rows=[];previous=''
        for i,row in enumerate(sheet.iter_rows(values_only=True)):
            if i==0:headers=list(row);continue
            date=str(row[0])[:10]
            if date<previous:raise ValueError('MPT date order invalid; cannot early stop')
            previous=date
            if date>cutoff:break
            rows.append(row)
        workbook.close();frame=pd.DataFrame(rows,columns=headers);frame.to_csv(bounded,index=False)
    frame['date']=pd.to_datetime(frame.date);frame['reference_start']=pd.to_datetime(frame.reference_start)
    frame=frame[frame.date<=pd.Timestamp(cutoff)]
    rows=[]
    for date,d in frame.groupby('date'):
        d=d[(d.field.str.lower().str.replace(' ','',regex=False)=='rate:mean')&(d.reference_start>date)].sort_values('reference_start')
        if len(d)<2:continue
        rows.append({'date':str(date.date()),'available_at':available_eod(date+pd.offsets.BDay(1)).isoformat(),'value':float(d.iloc[1].value)-float(d.iloc[0].value),'source_state_id':'MPT_'+str(date.date()),'recipe':'second-nearest future quarter mean minus nearest future quarter mean, bps; conservative next-weekday EOD; CURRENT-VINTAGE PIT-C only'})
    return pd.DataFrame(rows,columns=['date','available_at','value','source_state_id','recipe']),license_text

def rrp_fields(records):
    rows=[]
    for r in records:
        if r.get('operationType')!='Reverse Repo' or r.get('term')!='Overnight':continue
        op=pd.Timestamp(r['operationDate']);updated=pd.Timestamp(r['lastUpdated']);known=max(op,updated.normalize())
        rows.append({'date':str(op.date()),'available_at':available_eod(known).isoformat(),'level':float(r['totalAmtAccepted']),'source_state_id':str(r['operationId']),'lastUpdated':r['lastUpdated'],'availability_warning':'PIT-C current version, conservatively never before later lastUpdated; no original-version recovery'})
    return rows

def construct(private):
    private=Path(private); docs=private/'documents';audit={'SEP':{},'H41':{},'RRP':{},'MPT':{}};sources={}
    sep=[]
    for f in sorted(docs.glob('sep_*.html')):
        stamp=f.stem[4:];date=pd.Timestamp(stamp).date()
        try:sep.append(sep_fields(f.read_text(errors='replace'),date))
        except Exception as e:audit['SEP'][stamp]={'inactive':True,'reason':str(e)}
    sources['FOMC_SEP_POLICY_PATH']=pd.DataFrame(sep)
    hr=[];inactive={'20200319','20200416','20200730'}
    for f in sorted(docs.glob('h41_*.html')):
        stamp=f.stem[4:]
        try:
            html=f.read_text(errors='replace')
            if stamp in inactive:raise ValueError('2020 public release / DDP timing ambiguity; inactive conservatively')
            # Explicit corrections/revisions in selected document require manual field-level recovery before admission.
            txt=BeautifulSoup(html,'html.parser').get_text(' ',strip=True)
            if re.search(r'corrected|correction|revised on|reposted',txt,re.I):raise ValueError('Correction warning; inactive until field-specific original established')
            date=pd.Timestamp(stamp);hr.append({'date':str(date.date()),'available_at':available_eod(date).isoformat(),'level':h41_reserves(html),'source_state_id':'H41_'+stamp})
        except Exception as e:audit['H41'][stamp]={'inactive':True,'reason':str(e)}
    h=pd.DataFrame(hr).sort_values('date');h['value']=np.nan
    # exact latest dated release as of 21BD earlier, not 21 rows in an irregular sample.
    for i,row in h.iterrows():
        past=h[pd.to_datetime(h.date)<=pd.Timestamp(row.date)-pd.offsets.BDay(21)]
        if len(past):
            prev=past.iloc[-1]
            # Dataset is sampled. Only use prior release if it is actually the latest scheduled release.
            dates=json.loads((private/'h41_acquisition_plan.json').read_text())['universe'];cut=(pd.Timestamp(row.date)-pd.offsets.BDay(21)).strftime('%Y%m%d');latest=max(d for d in dates if d<=cut)
            if prev.source_state_id=='H41_'+latest:h.loc[i,'value']=-(row.level-prev.level)
    sources['H41_RESERVES']=h
    r=[]
    for f in sorted(docs.glob('rrp_*.html')):
        r.extend(rrp_fields(json.loads(f.read_text())['repo']['operations']))
    r=pd.DataFrame(r).sort_values('date').drop_duplicates('date',keep='last');grid=r.set_index(pd.to_datetime(r.date)).level.reindex(pd.bdate_range('2015-01-01','2024-12-18'))
    # Do not use a future version to form a historical difference.
    vals=[]
    for _,row in r.iterrows():
        prev=r[pd.to_datetime(r.date)<=pd.Timestamp(row.date)-pd.offsets.BDay(21)]
        if len(prev):
            old=prev.iloc[-1];vals.append(-(row.level-old.level) if pd.Timestamp(old.available_at)<=pd.Timestamp(row.available_at) else np.nan)
        else:vals.append(np.nan)
    r['value']=vals
    r=r.sort_values(['available_at','date']);newest='';keep=[]
    for i,row in r.iterrows():
        if row.date>=newest:newest=row.date;keep.append(i)
    sources['NYFED_ONRRP']=r.loc[keep].copy()
    m,license_text=mpt_state(private/'mpt_data.xlsx');sources['ATLANTA_MPT_SOFR']=m
    (private/'mpt_license.txt').write_text(license_text)
    audit['MPT']={'first_numeric_date':m.date.min(),'last_numeric_date':m.date.max(),'rows':len(m),'required_2015_2022_absent':True,'primary_eligible':False,'license_personal_educational_only':'personal and educational purposes only' in license_text}
    for key,df in sources.items():
        df.to_parquet(private/(key+'.parquet'),index=False)
        audit.setdefault(key,{})['rows']=len(df)
    (private/'source_extraction_audit.json').write_text(json.dumps(audit,indent=2))
    return sources,audit

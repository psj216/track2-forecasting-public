"""## Executive summary (read this first)
Parse original release archives without using later revisions of older observations.
"""
import re,json,zipfile,gzip,calendar
from pathlib import Path
from datetime import datetime
import numpy as np
from bs4 import BeautifulSoup
from .align_location_ledger import digest,dump
DATE_RE=r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{1,2},\s*\d{4}'
def date_parse(s):
    s=s.replace('.','');s=re.sub(r'\s+',' ',s)
    for form in ('%b %d, %Y','%B %d, %Y'):
        try:return datetime.strptime(s,form).date().isoformat()
        except ValueError:pass
    raise ValueError('Unrecognized source date '+s)
def parse_flow(data,release_date):
    text=data.decode('latin1');records=[]
    if 'millions' not in text.lower():raise ValueError('Unit not explicit')
    for line in text.splitlines():
        tokens=line.split()
        if len(tokens)==14 and tokens[0]=='99996' and re.fullmatch(r'\d{4}-\d{2}',tokens[1]):
            values=[float(t.replace(',','')) for t in tokens[2:]]
            records.append((tokens[1],values))
    if not records:raise ValueError('Missing all-country stock transaction table')
    month,v=max(records,key=lambda x:x[0]);yy,mm=map(int,month.split('-'));obs=f'{month}-{calendar.monthrange(yy,mm)[1]:02d}'
    if obs>=release_date:raise ValueError('Observation not before publication')
    # Native net foreign purchases of US corporate equities, millions USD.
    return dict(observation_date=obs,value=v[3]-v[9],gross=v[3]+v[9],month=month)
def parse_liquidity(data,release_date):
    soup=BeautifulSoup(data,'html.parser');pres=soup.find_all('pre')
    if not pres and b'<html' not in data.lower():
        from types import SimpleNamespace
        pres=[SimpleNamespace(get_text=lambda:data.decode('latin1'))]
    phrase='Reserve balances with Federal Reserve Banks';value=None;obs=None
    if pres:
        text=pres[0].get_text();match=re.search(r'Reserve balances with (?:Federal Reserve Banks|F\.R\. Banks)\s*(?:\(\d+\))?\s+([\d,]+)',text)
        if match:value=float(match[1].replace(',',''))
        header=re.search(r'Averages\s+of\s+daily\s+figures',text)
        head=text[header.start():header.start()+1000] if header else ''
        # Header has publication date followed by week-ended/current-year dates.
        dates=re.findall(DATE_RE,head);ds=[date_parse(d) for d in dates];prior=[d for d in ds if d<release_date]
        if prior:obs=prior[0]
    if value is None:
        for tr in soup.find_all('tr'):
            cells=tr.find_all(['td','th'],recursive=False);txt=[c.get_text(' ',strip=True) for c in cells]
            if txt and txt[0]==phrase and len(txt)>=2:
                value=float(re.sub(r'[^\d.]','',txt[1]));break
        for table in soup.find_all('table'):
            text=table.get_text(' ',strip=True)
            if 'Reserve Bank credit' in text and 'Week ended' in text:
                dates=re.findall(DATE_RE,text[:1800]);prior=[date_parse(d) for d in dates if date_parse(d)<release_date]
                if prior:obs=prior[0];break
    if value is None or obs is None:raise ValueError('Missing original weekly reserve balance or week-ended header')
    if not 'Millions of dollars' in soup.get_text(' ',strip=True):raise ValueError('Unit not explicit')
    return dict(observation_date=obs,value=value)
def build(private):
    f=[];l=[];reject=[];seen=set();raw=[]
    for record in sorted([x for path in private.glob('tic_acquisition_*.json') for x in json.loads(path.read_text())],key=lambda x:datetime.strptime(x['text'],'%m/%d/%Y')):
        if 'error' in record:reject.append(dict(source='TIC_FORM_S',reason=record['error'],record=record));continue
        file=private/'tic_raw'/record['file'];actual=digest(file)
        if actual!=record['sha256']:raise ValueError('Raw TIC changed')
        raw.append(dict(source='TIC_FORM_S',**record));release=datetime.strptime(record['text'],'%m/%d/%Y').date().isoformat()
        try:
            if not record['s1_member']:raise ValueError('Form S missing')
            with zipfile.ZipFile(file)as z:v=parse_flow(z.read(record['s1_member']),release)
            if v['month'] in seen:raise ValueError('Repeated measurement month: original first record retained; revision ignored')
            seen.add(v['month']);f.append(dict(**v,release_date=release,publication_time_et='23:59',publication_time_basis='Unknown individual archive release time; conservative end-of-day bound',event_id='TIC_'+release,source_id='TIC_FORM_S',instrument='US_EQUITIES',category='foreign_transactions',raw_sha256=actual))
        except ValueError as e:reject.append(dict(source='TIC_FORM_S',release_date=release,reason=str(e)))
    for record in sorted([x for path in private.glob('h41_acquisition_*.json') for x in json.loads(path.read_text())],key=lambda x:x['date']):
        if 'error' in record:reject.append(dict(source='FED_H41_RESERVES',reason=record['error'],record=record));continue
        file=private/'h41_raw'/record['file'];data=gzip.decompress(file.read_bytes());import hashlib
        if hashlib.sha256(data).hexdigest()!=record['raw_sha256']:raise ValueError('Raw H41 changed')
        raw.append(dict(source='FED_H41_RESERVES',**record));release=datetime.strptime(record['date'],'%Y%m%d').date().isoformat()
        try:
            v=parse_liquidity(data,release);available='2020-04-17' if release=='2020-04-16' else release;l.append(dict(**v,file_release_date=release,release_date=available,publication_time_et='23:59',publication_time_basis='Known usual16:30ETafter16:00cutoff; early exact time unverified, conservativeEOD; delayed2020Apr16availableApr17',event_id='H41_'+release,source_id='FED_H41_RESERVES',instrument='BANK_RESERVES',category='depository_institutions',raw_sha256=record['raw_sha256']))
        except ValueError as e:reject.append(dict(source='FED_H41_RESERVES',release_date=release,reason=str(e)))
    dump(private/'processed_releases.json',dict(F=f,L=l,P=[],rejected=reject));dump(private/'original_raw_manifest.json',dict(records=raw));print(json.dumps(dict(F=len(f),L=len(l),rejected=len(reject),reasons=reject[:12])),flush=True)
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--private',type=Path,required=True);a=p.parse_args();build(a.private)

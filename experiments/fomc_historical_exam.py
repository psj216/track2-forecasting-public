"""Executive summary: frozen FF03 historical exam; source has no outcomes or tuned choices."""
from __future__ import annotations
import concurrent.futures,hashlib,io,json,os,pathlib,re,shutil,subprocess,sys,time,uuid,traceback
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from pandas.tseries.holiday import USFederalHolidayCalendar
B=pd.offsets.CustomBusinessDay(calendar=USFederalHolidayCalendar())
ROOT=pathlib.Path.cwd(); W=pathlib.Path(os.environ.get('EXAM_WORK','/tmp/ff03-historical-exam'));W.mkdir(parents=True,exist_ok=True)
IMAGE='ghcr.io/psj216/track2-forecasting-ff03@sha256:daddaf6222ebeea0c8951643db525eb73e7d856af9c5ac23b09772f3d1b8b81c'
V51='docker.io/jotj216/track2-f4-approved@sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874'
MEETINGS=[('2022-06-15','20220504','2022-05-25'),('2023-03-22','20230201','2023-02-22'),('2024-09-18','20240731','2024-08-21'),('2025-09-17','20250730','2025-08-20'),('2026-09-16','20260729','2026-08-19')]
COLS={'1 Mo':'UST_1M','1.5 Mo':'UST_6W','2 Mo':'UST_2M','3 Mo':'UST_3M','4 Mo':'UST_4M','6 Mo':'UST_6M','1 Yr':'UST_1Y','2 Yr':'UST_2Y','3 Yr':'UST_3Y','5 Yr':'UST_5Y','7 Yr':'UST_7Y','10 Yr':'UST_10Y','20 Yr':'UST_20Y','30 Yr':'UST_30Y'}
FRED={'DGS1MO':'UST_1M','DGS3MO':'UST_3M','DGS6MO':'UST_6M','DGS1':'UST_1Y','DGS2':'UST_2Y','DGS3':'UST_3Y','DGS5':'UST_5Y','DGS7':'UST_7Y','DGS10':'UST_10Y','DGS20':'UST_20Y','DGS30':'UST_30Y'}
def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,indent=2,default=str,allow_nan=False))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def status(stage,**kw):dump(W/'STATUS.json',dict(stage=stage,source_sha=os.environ.get('GITHUB_SHA'),updated_utc=pd.Timestamp.now(tz='UTC').isoformat(),**kw))
def get(url):
    r=requests.get(url,timeout=45,headers={'User-Agent':'Mozilla/5.0 research data audit'});r.raise_for_status();return r.text
def dates():
    rows=[]
    for m,doc,minutes in MEETINGS:
        for kind,off in [('fomc',0),('control15',15),('control10',10)]:
            event=pd.Timestamp(m)-off*B;asof=event-2*B
            rows.append(dict(id=m+'-'+kind,meeting=m,group='fomc' if off==0 else 'control',pseudo_event=str(event.date()),asof=str(asof.date()),previous_statement=doc,minutes_release=minutes,targets=[str((asof+h*B).date()) for h in range(1,5)]))
    return rows
def read_table(html):
    tables=pd.read_html(io.StringIO(html));d=next(t for t in tables if 'Date' in t.columns and '2 Yr' in t.columns)
    good=[c for c in COLS if c in d];d=d[['Date']+good].rename(columns={'Date':'date',**COLS})
    d['date']=pd.to_datetime(d['date']);d=d.melt(id_vars='date',var_name='asset',value_name='value');d['value']=pd.to_numeric(d['value'],errors='coerce')
    return d.dropna()
def prepare():
    status('prepare');raw=W/'acquisition';raw.mkdir(exist_ok=True);sources=[];frames=[]
    def treasury(y):
        url=f'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value={y}'
        try:
            text=get(url);p=raw/f'treasury-{y}.html';p.write_text(text);f=read_table(text);f=f[f.date.dt.year==y]
            return f,dict(url=url,path=p.name,sha256=sha(p),rows=len(f),vintage='CURRENT_VINTAGE_NOT_CERTIFIED',publication_time='Treasury daily rates, usually approximately 15:30 ET; date-only values activated after close')
        except Exception as e:return None,dict(url=url,error=str(e))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for f,src in pool.map(treasury,range(2020,2027)):
            sources.append(src)
            if f is not None and len(f):f['source']=src['url'];frames.append(f)
    # One alternative official source, not an outcome-dependent source selection.
    url='https://fred.stlouisfed.org/graph/?'+requests.compat.urlencode({'id':','.join(FRED),'cosd':'2020-01-01','coed':'2026-09-18','format':'csv'})
    try:
        text=get(url);p=raw/'fred.csv';p.write_text(text);f=pd.read_csv(io.StringIO(text))
        f=f.rename(columns={f.columns[0]:'date',**FRED});f['date']=pd.to_datetime(f['date']);f=f.melt(id_vars='date',var_name='asset',value_name='value')
        f['value']=pd.to_numeric(f['value'],errors='coerce');f=f[f.asset.isin(FRED.values())].dropna();f['source']=url;frames.append(f)
        sources.append(dict(url=url,sha256=sha(p),rows=len(f),vintage='CURRENT_VINTAGE_NOT_CERTIFIED'))
    except Exception as e:sources.append(dict(url=url,error=str(e)))
    # Existing official panels are fallback only. Their retrieval history is not PIT-certified.
    for rel in ['units/t2-F3-rates-into-factors-2022/rates_daily.parquet','units/t2-F1-hawkish-cut-2024/rates_daily.parquet']:
        try:
            p=ROOT/rel;f=pd.read_parquet(p);f=f.rename(columns={'asset_id':'asset','timestamp':'date'});f['date']=pd.to_datetime(f.date)
            f=f[['date','asset','value']].dropna();f['source']='inherited:'+rel;frames.append(f)
            sources.append(dict(path=rel,sha256=sha(p),rows=len(f),vintage='INHERITED_OFFICIAL_PANEL_NOT_PIT_CERTIFIED'))
        except Exception as e:sources.append(dict(path=rel,error=str(e)))
    if not frames:raise RuntimeError('No usable official yield data')
    market=pd.concat(frames,ignore_index=True).drop_duplicates(['date','asset'],keep='first').sort_values(['date','asset'])
    market.to_parquet(W/'evaluator-market.parquet',index=False);dump(W/'SOURCES.json',sources)
    cases=dates();dump(W/'COHORT.json',cases);manifest=[]
    for c in cases:
        try:
            dest=W/'inputs'/c['id'];(dest/'panels').mkdir(parents=True,exist_ok=True);(dest/'text').mkdir(exist_ok=True)
            cutoff=pd.Timestamp(c['asof']);past=market[market.date<=cutoff]
            assets=[];excluded=[]
            for a,g in past.groupby('asset'):
                if a.startswith('UST_') and len(g)>=120 and g.date.max()==cutoff:assets.append(a)
                else:excluded.append(dict(asset=a,reason='missing_asof_or_less_than_120_observations',observations=len(g)))
            wide=past[past.asset.isin(assets)].pivot(index='date',columns='asset',values='value').tail(504)
            # Discard newer tenors only if they prevent any valid 120-row joint history.
            while len(wide.dropna())<120 and len(assets)>1:
                a=wide.notna().sum().idxmin();assets.remove(a);excluded.append(dict(asset=a,reason='insufficient_common_joint_history'));wide=wide[assets]
            wide=wide.dropna()
            if len(wide)<120 or wide.index[-1]!=cutoff:raise RuntimeError('No valid complete curve origin history')
            long=wide.reset_index().melt(id_vars='date',var_name='asset',value_name='value');long.date=long.date.dt.strftime('%Y-%m-%d')
            long.to_parquet(dest/'panels'/'rates.parquet',index=False)
            entries=[];doc_errors=[]
            for typ,day,release,url in [
                ('fomc_statement',c['previous_statement'],pd.Timestamp(c['previous_statement']).strftime('%Y-%m-%d'),'https://www.federalreserve.gov/newsevents/pressreleases/monetary'+c['previous_statement']+'a.htm'),
                ('fomc_minutes',c['previous_statement'],c['minutes_release'],'https://www.federalreserve.gov/monetarypolicy/fomcminutes'+c['previous_statement']+'.htm')]:
                if release>c['asof']:continue
                try:
                    cache=raw/(typ+'-'+day+'.html')
                    if not cache.exists():cache.write_text(get(url))
                    soup=BeautifulSoup(cache.read_text(),'html.parser');section=soup.select_one('div.col-xs-12.col-sm-8.col-md-8') or soup.select_one('#content')
                    if section is None:raise ValueError('No official content section')
                    body=section.get_text(' ',strip=True);fn=typ+'-'+day+'.txt';(dest/'text'/fn).write_text(body)
                    entries.append(dict(doc_id=typ+'-'+day,timestamp=release,available_at=pd.Timestamp(release+' 14:00',tz='America/New_York').isoformat(),source=url,doc_type=typ,file=fn,sha256=sha(dest/'text'/fn),pit='RELEASE_SCHEDULE_KNOWN_BODY_VINTAGE_UNCERTIFIED'))
                except Exception as e:doc_errors.append(dict(url=url,error=str(e)))
            (dest/'text'/'corpus_index.json').write_text(json.dumps(dict(asof=c['asof'],documents=entries)))
            cid='t2-fomc-exam-'+c['id']
            # Minimal same F3 card in both arms; only corpus contents differ.
            card=f'''# Executive summary: frozen historical exam input.
schema_version = "2.0"
[task]
id = "{cid}"
track = "forecasting"
title = "FF03 historical examiner"
split = "validation"
[metadata]
category = "T2-F3"
horizons = [1,2,3,4]
n_assets = {len(assets)}
target_type = "level"
target_frequency = "daily"
[provenance]
data_cutoff = "{c['asof']}"
data_source = "Official yields; current/inherited vintage, limited reconstruction"
[contamination]
canary_guid = "{uuid.uuid5(uuid.NAMESPACE_URL,cid)}"
[targets]
asset_ids = {json.dumps(assets)}
horizons = [1,2,3,4]
target_type = "level"
target_frequency = "daily"
value_unit = "percent_per_annum"
[scoring.params]
n_draws_min = 2000
[panels.rates]
asset_ids = {json.dumps(assets)}
frequency = "business_daily"
[text]
cutoff = "{c['asof']}"
path = "text/"
'''
            (dest/'card.toml').write_text(card)
            (dest/'forecast_spec.json').write_text(json.dumps(dict(schema_version='2',card_id=cid,track='forecasting',card_family='T2-F3',targets=dict(asset_ids=assets,horizons=[1,2,3,4],target_type='level',target_frequency='daily',value_unit='percent_per_annum'),output_format='samples',n_draws_min=2000)))
            no=W/'inputs-no-text'/c['id'];shutil.copytree(dest,no,dirs_exist_ok=True);shutil.rmtree(no/'text');(no/'text').mkdir()
            row=dict(**c,status='READY',assets=assets,excluded_tenors=excluded,history_rows=len(wide),history_start=str(wide.index.min().date()),documents=entries,document_errors=doc_errors,pit='LIMITED_RECONSTRUCTION',
              input_hashes={str(p.relative_to(dest)):sha(p) for p in dest.rglob('*') if p.is_file()})
        except Exception as e:row=dict(**c,status='EXCLUDED',error=str(e))
        manifest.append(row);dump(W/'INPUT-MANIFEST.json',manifest)
        print('PREPARED',c['id'],row['status'],flush=True)
    status('prepared',ready=sum(c['status']=='READY' for c in manifest),total=len(manifest))
def canon(f):
    ac='asset' if 'asset' in f else 'asset_id';vc='value' if 'value' in f else 'sample'
    dc=next(c for c in ['draw','draw_id','sample_id'] if c in f)
    return f.rename(columns={ac:'asset',vc:'value',dc:'draw'}).sort_values(['asset','horizon','draw'])[['asset','horizon','draw','value']].reset_index(drop=True)
def forecasts():
    manifest=json.loads((W/'INPUT-MANIFEST.json').read_text());receipts=[];failures=[]
    status('forecasting')
    v51_available=False
    try:
        p=subprocess.run(['docker','pull',V51],capture_output=True,text=True,timeout=180);v51_available=p.returncode==0
        dump(W/'V51-PULL.json',dict(status='PASS' if v51_available else 'NOT_RUN',exit_code=p.returncode,stderr=p.stderr[-3000:],image=V51))
    except Exception as e:dump(W/'V51-PULL.json',dict(status='NOT_RUN',error=str(e),image=V51))
    for i,c in enumerate(manifest):
        if c['status']!='READY':continue
        dest=W/'inputs'/c['id'];past=pd.read_parquet(dest/'panels'/'rates.parquet').pivot(index='date',columns='asset',values='value')
        for model,img,input_root in [('ff03',IMAGE,W/'inputs'),('ff03_no_text',IMAGE,W/'inputs-no-text')]+([('v51',V51,W/'inputs')] if v51_available else []):
            out=W/'predictions'/c['id']/model;out.mkdir(parents=True,exist_ok=True);out.chmod(0o777)
            cmd=['docker','run','--rm','--network=none','--read-only','--tmpfs','/tmp:rw,size=512m','--cpus=2','--memory=4g','-v',str(input_root/c['id'])+':/input:ro','-v',str(out)+':/output',img,'forecast','--panels','/input/panels','--text','/input/text','--asof',c['asof'],'--out','/output/forecast.parquet','--n-draws','2000','--seed','318']
            try:
                p=subprocess.run(cmd,capture_output=True,text=True,timeout=120);dump(out/'process.json',dict(command=cmd,exit_code=p.returncode,stderr=p.stderr[-5000:]))
                if p.returncode:raise RuntimeError(p.stderr[-1600:])
                f=canon(pd.read_parquet(out/'forecast.parquet'))
                assert np.isfinite(f.value).all() and len(f)==len(c['assets'])*4*2000
                assert (f.groupby(['asset','horizon']).size()==2000).all()
                f.to_csv(out/'forecast.csv',index=False)
                receipts.append(dict(case=c['id'],model=model,status='PASS',image=img,forecast_sha256=sha(out/'forecast.parquet'),csv_sha256=sha(out/'forecast.csv'),seed=318,n_draws=2000))
            except Exception as e:failures.append(dict(case=c['id'],model=model,status='FAILED',error=str(e)))
        # Two frozen statistical comparators. No target data are mounted or opened here.
        assets=c['assets'];base=past.iloc[-1][assets].to_numpy(float);rng=np.random.default_rng(318)
        cov=past[assets].diff().dropna().tail(60).cov().to_numpy();cov=.9*cov+.1*np.diag(np.diag(cov))
        innovations=rng.multivariate_normal(np.zeros(len(assets)),cov,size=(2000,4),check_valid='raise')
        paths=base[None,None,:]+np.cumsum(innovations,axis=1)
        for model,arr in [('flat',np.broadcast_to(base,(2000,4,len(base)))),('gaussian60',paths)]:
            out=W/'predictions'/c['id']/model;out.mkdir(parents=True,exist_ok=True)
            f=pd.DataFrame([dict(asset=a,horizon=h+1,draw=d,value=float(arr[d,h,k])) for k,a in enumerate(assets) for h in range(4) for d in range(2000)])
            f.to_parquet(out/'forecast.parquet',index=False);f.to_csv(out/'forecast.csv',index=False)
            receipts.append(dict(case=c['id'],model=model,status='PASS',forecast_sha256=sha(out/'forecast.parquet'),csv_sha256=sha(out/'forecast.csv'),seed=318,n_draws=2000))
        dump(W/'PREDICTION-MANIFEST.json',receipts);dump(W/'FAILURES.json',failures)
        status('forecasting',completed=i+1,total=len(manifest),last=c['id'])
        print('FORECAST_CHECKPOINT',i+1,len(manifest),c['id'],flush=True)
    # This seal exists before evaluate() is permitted to open evaluator-market.
    dump(W/'PREDICTIONS-FROZEN.json',dict(manifest_sha256=sha(W/'PREDICTION-MANIFEST.json'),source_sha=os.environ.get('GITHUB_SHA'),frozen_at=pd.Timestamp.now(tz='UTC').isoformat(),count=len(receipts)))
    status('predictions_frozen',count=len(receipts),failures=len(failures))
    print('PREDICTIONS_FROZEN',sha(W/'PREDICTIONS-FROZEN.json'),flush=True)
def evaluate():
    sys.path.insert(0,str(ROOT/'common-current'/'common'))
    from qfbench2_common.scoring.crps import crps_ensemble
    frozen=json.loads((W/'PREDICTIONS-FROZEN.json').read_text())
    assert frozen['manifest_sha256']==sha(W/'PREDICTION-MANIFEST.json')
    manifest=json.loads((W/'INPUT-MANIFEST.json').read_text());receipts=json.loads((W/'PREDICTION-MANIFEST.json').read_text())
    for r in receipts:assert sha(W/'predictions'/r['case']/r['model']/'forecast.parquet')==r['forecast_sha256']
    # First evaluator access to origin-to-horizon observed target values.
    market=pd.read_parquet(W/'evaluator-market.parquet').pivot(index='date',columns='asset',values='value')
    metrics=[];truth=[];missing=[];ab=[]
    for c in manifest:
        if c['status']!='READY':continue
        for r in [r for r in receipts if r['case']==c['id']]:
            f=canon(pd.read_parquet(W/'predictions'/c['id']/r['model']/'forecast.parquet'))
            for (a,h),g in f.groupby(['asset','horizon']):
                date=c['targets'][int(h)-1]
                if pd.Timestamp(date) not in market.index or pd.isna(market.loc[date,a]):
                    missing.append(dict(case=c['id'],model=r['model'],asset=a,horizon=int(h),date=date,reason='No official exact-date target'));continue
                y=float(market.loc[date,a]);anchor=float(market.loc[c['asof'],a]);x=g.value.to_numpy();q=np.quantile(x,[.05,.25,.5,.75,.95])
                move=(y-anchor)*100;pred=(q[2]-anchor)*100;p10=float(np.mean(np.abs(x-anchor)*100>=10-1e-9));hit=abs(move)>=10-1e-9
                d=dict(case=c['id'],group=c['group'],meeting=c['meeting'],asof=c['asof'],model=r['model'],asset=a,horizon=int(h),target_date=date,anchor=anchor,actual=y,actual_move_bp=move,median=float(q[2]),median_move_bp=pred,
                    direction_valid=abs(move)>1e-9,direction_correct=bool(abs(move)>1e-9 and np.sign(pred)==np.sign(move)),mae_bp=abs(q[2]-y)*100,flat_mae_bp=abs(y-anchor)*100,crps_bp=float(crps_ensemble(x,y))*100,
                    coverage50=bool(q[1]<=y<=q[3]),width50_bp=float(q[3]-q[1])*100,coverage90=bool(q[0]<=y<=q[4]),width90_bp=float(q[4]-q[0])*100,p_abs10=p10,event_abs10=bool(hit),brier_abs10=(p10-float(hit))**2)
                metrics.append(d)
                if r['model']=='ff03':truth.append({k:d[k] for k in ['case','asset','horizon','target_date','actual','anchor']})
        a=W/'predictions'/c['id']/'ff03'/'forecast.parquet';b=W/'predictions'/c['id']/'ff03_no_text'/'forecast.parquet'
        if a.exists() and b.exists():
            fa=canon(pd.read_parquet(a));fb=canon(pd.read_parquet(b));ledger=(a.parent/'forecast_rationale.md').read_text()
            ab.append(dict(case=c['id'],documents=len(c['documents']),byte_identical=sha(a)==sha(b),draws_identical=fa.equals(fb),max_abs_diff=float(np.max(np.abs(fa.value-fb.value))),family_frozen='family_frozen' in ledger))
        dump(W/'AB-RESULTS.json',ab)
    df=pd.DataFrame(metrics);df.to_csv(W/'metrics.csv',index=False);df.to_parquet(W/'metrics.parquet',index=False);pd.DataFrame(truth).to_csv(W/'observations.csv',index=False);dump(W/'MISSING-TARGETS.json',missing)
    def agg(g):
        valid=g[g.direction_valid]
        return dict(cells=len(g),origins=int(g['case'].nunique()),direction_n=len(valid),direction_accuracy=float(valid.direction_correct.mean()) if len(valid) else None,
            mae_bp=float(g.mae_bp.mean()),flat_mae_bp=float(g.flat_mae_bp.mean()),mae_skill_vs_flat=1-float(g.mae_bp.mean()/g.flat_mae_bp.mean()) if g.flat_mae_bp.mean() else None,
            crps_bp=float(g.crps_bp.mean()),coverage50=float(g.coverage50.mean()),width50_bp=float(g.width50_bp.mean()),coverage90=float(g.coverage90.mean()),width90_bp=float(g.width90_bp.mean()),abs10_frequency=float(g.event_abs10.mean()),abs10_mean_probability=float(g.p_abs10.mean()),brier_abs10=float(g.brier_abs10.mean()))
    summary=[dict(group=k[0],model=k[1],**agg(g)) for k,g in df.groupby(['group','model'])]
    perorigin=[dict(case=k[0],model=k[1],**agg(g)) for k,g in df.groupby(['case','model'])]
    pd.DataFrame(perorigin).to_csv(W/'per-origin.csv',index=False)
    dump(W/'SUMMARY.json',summary);dump(W/'PER-ORIGIN.json',perorigin)
    hashes={str(p.relative_to(W)):sha(p) for p in W.rglob('*') if p.is_file() and p.name!='EVIDENCE-HASHES.json'};dump(W/'EVIDENCE-HASHES.json',hashes)
    status('complete',evaluated_cells=len(df),ab_cases=len(ab),excluded=sum(c['status']!='READY' for c in manifest),failed=len(json.loads((W/'FAILURES.json').read_text())))
    print('SUMMARY_JSON='+json.dumps(summary),flush=True)
    print('ORIGIN_JSON='+json.dumps([r for r in perorigin if r['model']=='ff03']),flush=True)
    print('AB_JSON='+json.dumps(ab),flush=True)
    print('COHORT_JSON='+json.dumps([dict(id=c['id'],status=c['status'],asof=c['asof'],assets=c.get('assets'),history_rows=c.get('history_rows'),documents=len(c.get('documents',[])),error=c.get('error')) for c in manifest]),flush=True)
    print('FAILURES_JSON='+(W/'FAILURES.json').read_text(),flush=True)
if __name__=='__main__':
    {'prepare':prepare,'forecast':forecasts,'evaluate':evaluate}[sys.argv[1]]()

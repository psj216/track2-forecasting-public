"""Executive summary: frozen two-origin FF03 FOMC market-yield exam; no model changes.
Retrospective September is not independent OOS. Current-vintage Treasury data are used.
Neither Treasury yield direction nor its probability is a Fed decision probability.
"""
import io,json,hashlib,pathlib,subprocess,uuid
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
ROOT=pathlib.Path.cwd()
WORK=pathlib.Path('/tmp/fomc-exam');WORK.mkdir(exist_ok=True)
IMAGE='ghcr.io/psj216/track2-forecasting-ff03@sha256:daddaf6222ebeea0c8951643db525eb73e7d856af9c5ac23b09772f3d1b8b81c'
ASSETS={'3 Mo':'UST_3M','6 Mo':'UST_6M','1 Yr':'UST_1Y','2 Yr':'UST_2Y','5 Yr':'UST_5Y','7 Yr':'UST_7Y','10 Yr':'UST_10Y','20 Yr':'UST_20Y','30 Yr':'UST_30Y'}
def get(url):
    r=requests.get(url,timeout=60);r.raise_for_status();return r.text
frames=[];sources=[]
for year in [2025,2026]:
    url=f'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value={year}'
    html=get(url);tables=pd.read_html(io.StringIO(html))
    df=next(t for t in tables if 'Date' in t.columns and '2 Yr' in t.columns)
    df=df[['Date']+list(ASSETS)].rename(columns={'Date':'date',**ASSETS})
    df['date']=pd.to_datetime(df['date'])
    for a in ASSETS.values():df[a]=pd.to_numeric(df[a],errors='coerce')
    frames.append(df);sources.append({'url':url,'sha256':hashlib.sha256(html.encode()).hexdigest()})
panel=pd.concat(frames).drop_duplicates('date').sort_values('date').set_index('date')
print('DATA',json.dumps({'rows':len(panel),'min':str(panel.index.min()),'max':str(panel.index.max()),'sources':sources}),flush=True)
# Decisions are never supplied as targets. Both prediction files are completed before scoring.
cases=[('september','2026-09-14',['20260729']),('october','2026-10-23',['20260729','20260916'])]
outputs=[]
for name,asof,docs in cases:
    dest=WORK/name;dest.mkdir(exist_ok=True);(dest/'panels').mkdir(exist_ok=True);(dest/'text').mkdir(exist_ok=True)
    out=WORK/(name+'-output');out.mkdir(exist_ok=True);out.chmod(0o777)
    past=panel.loc[:asof].dropna()
    assert str(past.index[-1].date())==asof and len(past)>200
    long=past.reset_index().melt(id_vars='date',var_name='asset',value_name='value')
    long['date']=long['date'].dt.strftime('%Y-%m-%d');long.to_parquet(dest/'panels'/'rates.parquet',index=False)
    entries=[]
    for day in docs:
        url=f'https://www.federalreserve.gov/newsevents/pressreleases/monetary{day}a.htm'
        html=get(url);soup=BeautifulSoup(html,'html.parser')
        section=soup.select_one('div.col-xs-12.col-sm-8.col-md-8') or soup.select_one('#content') or soup
        body=section.get_text(' ',strip=True)
        timestamp=f'{day[:4]}-{day[4:6]}-{day[6:]}'
        assert timestamp<=asof
        fn=f'fomc-{day}.txt';(dest/'text'/fn).write_text(body)
        entries.append(dict(doc_id=day,timestamp=timestamp,source=url,doc_type='fomc_statement',file=fn))
    (dest/'text'/'corpus_index.json').write_text(json.dumps(dict(asof=asof,documents=entries)))
    assets=list(ASSETS.values());cid='t2-ff03-fomc-exam-'+name
    card=f'''schema_version = "2.0"
[task]
id = "{cid}"
track = "forecasting"
title = "Frozen FF03 FOMC yield exam"
split = "validation"
[metadata]
category = "T2-F3"
horizons = [1,2,3,4]
n_assets = 9
target_type = "level"
target_frequency = "daily"
[provenance]
data_cutoff = "{asof}"
data_source = "US Treasury current vintage; exploratory"
[contamination]
canary_guid = "{uuid.uuid4()}"
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
cutoff = "{asof}"
path = "text/"
'''
    (dest/'card.toml').write_text(card)
    (dest/'forecast_spec.json').write_text(json.dumps(dict(schema_version='2',card_id=cid,track='forecasting',card_family='T2-F3',targets=dict(asset_ids=assets,horizons=[1,2,3,4],target_type='level',target_frequency='daily',value_unit='percent_per_annum'),output_format='samples',n_draws_min=2000)))
    hashes={str(f.relative_to(dest)):hashlib.sha256(f.read_bytes()).hexdigest() for f in dest.rglob('*') if f.is_file()}
    (WORK/(name+'-inputs.json')).write_text(json.dumps(hashes,indent=2))
    args=['docker','run','--rm','--network=none','--read-only','--tmpfs','/tmp:rw,size=512m','--cpus=2','--memory=4g','-v',str(dest)+':/input:ro','-v',str(out)+':/output',IMAGE,'forecast','--panels','/input/panels','--text','/input/text','--asof',asof,'--out','/output/forecast.parquet','--n-draws','2000','--seed','318']
    print('RUN',name,flush=True)
    p=subprocess.run(args,capture_output=True,text=True,timeout=180)
    print('PROCESS',name,p.returncode,p.stderr[-1600:],flush=True)
    if p.returncode:raise RuntimeError('forecast failed '+name)
    f=pd.read_parquet(out/'forecast.parquet')
    print('OUTPUT_COLUMNS',list(f.columns),flush=True)
    outputs.append((name,asof,past.iloc[-1],f,out))
print('BOTH_PREDICTIONS_FROZEN',flush=True)
for name,asof,anchor,f,out in outputs:
    ac='asset' if 'asset' in f else 'asset_id';vc='value' if 'value' in f else 'sample'
    rows=[]
    for (a,h),g in f.groupby([ac,'horizon']):
        vals=g[vc].to_numpy();assert np.isfinite(vals).all() and len(vals)==2000
        date=(pd.Timestamp(asof)+pd.offsets.BDay(int(h))).strftime('%Y-%m-%d')
        q=np.quantile(vals,[.05,.5,.95])
        row=dict(asset=a,horizon=int(h),date=date,anchor=float(anchor[a]),p_up=float(np.mean(vals>anchor[a])),p_down=float(np.mean(vals<anchor[a])),q05=float(q[0]),median=float(q[1]),q95=float(q[2]),median_change_bp=float((q[1]-anchor[a])*100))
        if name=='september':
            actual=float(panel.loc[date,a]);row.update(actual=actual,actual_change_bp=(actual-anchor[a])*100,covered90=bool(q[0]<=actual<=q[2]),median_error_bp=float((q[1]-actual)*100))
        rows.append(row)
    receipt=dict(case=name,asof=asof,image=IMAGE,seed=318,n_draws=2000,rows=rows,
      forecast_sha256=hashlib.sha256((out/'forecast.parquet').read_bytes()).hexdigest(),
      limitation='Not a policy-decision classifier. September model was built after the event. Current-vintage inputs; no claim of independent PIT/OOS.')
    (WORK/(name+'-summary.json')).write_text(json.dumps(receipt,indent=2))
    print('RESULT_JSON='+json.dumps(receipt),flush=True)
    print('RATIONALE_'+name+'='+ (out/'forecast_rationale.md').read_text()[:7000],flush=True)

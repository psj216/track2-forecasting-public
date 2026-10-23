"""Executive summary: fixed 2025 research inputs; no labels generated or read here."""
import hashlib
import json
import pathlib
import sys
import zipfile
import numpy as np
import pandas as pd

SOURCE_SHA='93bac351c4a60e612e641150f2392db9f85fe497336ee9d71c4d241f70063eda'
GROUPS={'ECB_EM':['MXN','BRL','ZAR','KRW','INR'],'ECB_G10':['EUR','JPY','CHF']}


def load(zip_path):
    assert hashlib.sha256(pathlib.Path(zip_path).read_bytes()).hexdigest()==SOURCE_SHA
    z=zipfile.ZipFile(zip_path);frame=pd.read_csv(z.open('eurofxref-hist.csv'))
    frame['Date']=pd.to_datetime(frame.Date);frame=frame.set_index('Date').sort_index()
    for c in ['USD','JPY','CHF','MXN','BRL','ZAR','KRW','INR']:
        frame[c]=pd.to_numeric(frame[c],errors='coerce')
    frame['EUR']=1.
    return frame


def prepare(raw,out,group):
    frame=load(raw);out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True)
    assets=GROUPS[group];receipts=[]
    for origin in pd.date_range('2025-01-06','2025-12-15',freq='W-MON'):
        date=str(origin.date());name='a19-research-'+group+'-'+date;unit=out/name;unit.mkdir(exist_ok=True);(unit/'text').mkdir(exist_ok=True)
        rows=[]
        for a in assets:
            # Declared research unit: currency units per USD, EUR is1/USD.
            series=(frame.loc[frame.index<=origin,a]/frame.loc[frame.index<=origin,'USD']).dropna()
            assert np.isfinite(series).all()
            rows.extend(dict(date=d.date(),asset=a,value=float(v),panel_id='em_fx_ecb_daily') for d,v in series.items())
        panel=pd.DataFrame(rows);assert pd.to_datetime(panel.date).max()<=origin
        panel.to_parquet(unit/'em_fx_ecb_daily.parquet',index=False)
        card=f'''schema_version = "2.0"
[task]
id = "{name}"
track = "forecasting"
[metadata]
category = "T2-F3"
target_frequency = "daily"
[provenance]
data_cutoff = "{date}"
[targets]
asset_ids = {json.dumps(assets)}
horizons = [1,2,3,4]
target_type = "level"
target_frequency = "daily"
value_unit = "currency_units_per_USD"
[panels]
panel_ids = ["em_fx_ecb_daily"]
[panels.em_fx_ecb_daily]
asset_ids = {json.dumps(assets)}
frequency = "business_daily"
[scoring.params]
n_draws_min = 200
joint = "variogram"
tail_metric = "pinball"
'''
        (unit/'card.toml').write_text(card)
        receipts.append(dict(id=name,origin=date,group=group,assets=assets,horizons=[1,2,3,4],
            files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in unit.iterdir() if p.is_file()},
            observation_max=str(pd.to_datetime(panel.date).max().date()),rows=len(panel)))
    (out/'input-manifest.json').write_text(json.dumps({'executive_summary':'Current ECB history truncated per origin; PIT authenticity limited, research cards not official Final cards.','source_sha256':SOURCE_SHA,'inputs':receipts},indent=2))
    print('prepared',len(receipts),group)

if __name__=='__main__':prepare(*sys.argv[1:])

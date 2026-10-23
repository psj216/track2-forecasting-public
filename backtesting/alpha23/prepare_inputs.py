"""Executive summary: identical isolated asof inputs for all forecasters; outcomes stay outside units."""
import pathlib,json,hashlib,sys,tomllib
import pandas as pd
from feature_builder import ASSETS

def prepare(data,out):
 data=pathlib.Path(data);out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True);p=pd.read_parquet(data/'curve.parquet');docs=json.loads((data/'documents.json').read_text());receipts=[];missing=[]
 origins=list(pd.date_range('2025-01-06','2025-12-15',freq='W-MON'))+list(pd.date_range('2026-01-05','2026-10-12',freq='W-MON'))
 for day in origins:
  if day not in p.index:missing.append(str(day.date()));continue
  date=str(day.date());unit=out/('a23-ust-'+date);unit.mkdir(exist_ok=True);text=unit/'text';text.mkdir(exist_ok=True)
  history=p.loc[:day,ASSETS];frame=history.rename_axis('date').reset_index().melt('date',var_name='asset',value_name='value').dropna();frame['date']=frame.date.dt.date;frame['panel_id']='rates_daily';frame.to_parquet(unit/'rates_daily.parquet',index=False)
  eligible=[d for d in docs if d['active']<=date];selected=[]
  for kind in ['fomc_statement','fomc_minutes']:selected+=sorted([d for d in eligible if d['kind']==kind],key=lambda d:(d['active'],d['sha256']))[-2:]
  entries=[]
  for i,d in enumerate(selected):
   f=f'policy-{i}.txt';(text/f).write_text(d['text']);entries.append({'doc_id':'policy-'+d['sha256'][:16],'timestamp':d['active'],'source':'Federal Reserve','doc_type':d['kind'],'file':f})
  (text/'corpus_index.json').write_text(json.dumps({'documents':entries,'asof':date},indent=2))
  (unit/'policy.json').write_text(json.dumps([{k:v for k,v in d.items() if k not in ['text','path']} for d in selected],indent=2))
  card=f'''schema_version = "2.0"
[task]
id = "{unit.name}"
track = "forecasting"
[metadata]
category = "T2-F3"
target_frequency = "daily"
[provenance]
data_cutoff = "{date}"
[targets]
asset_ids = {json.dumps(ASSETS)}
horizons = [1,2,3,4]
target_type = "level"
target_frequency = "daily"
value_unit = "percent_per_annum"
[panels]
panel_ids = ["rates_daily"]
[panels.rates_daily]
asset_ids = {json.dumps(ASSETS)}
frequency = "business_daily"
[text]
path = "text/"
cutoff = "{date}"
cutoff_checked = true
[scoring.params]
n_draws_min = 200
joint = "variogram"
tail_metric = "pinball"
'''
  (unit/'card.toml').write_text(card)
  receipts.append({'id':unit.name,'origin':date,'files':{str(f.relative_to(unit)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(unit.rglob('*')) if f.is_file()},'last_observation':str(history.index.max().date()),'docs':len(selected)})
 (out/'input-manifest.json').write_text(json.dumps({'executive_summary':'Research cards, not official Final metadata; each input cutoff enforced.','requested_origins':len(origins),'prepared':len(receipts),'missing_origin_observations':missing,'inputs':receipts},indent=2));print('prepared',len(receipts),'missing origins',len(missing),flush=True)
if __name__=='__main__':prepare(*sys.argv[1:])

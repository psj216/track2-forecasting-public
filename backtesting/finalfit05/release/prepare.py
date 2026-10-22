"""Executive summary: add one unsupported-cadence synthetic input, never a Final card."""
import json,pathlib,shutil,sys,tomllib,uuid
import pandas as pd
sys.path.insert(0,'/audit03')
from container_tools import write_toml
r=pathlib.Path('/worktest');p=r/'inputs/unsupported-cadence';shutil.copytree(r/'inputs/monthly-a',p)
c=tomllib.loads((p/'card.toml').read_text());c['task']['id']='t2-fit05-unsupported-cadence';c['contamination']['canary_guid']=str(uuid.uuid4());write_toml(c,p/'card.toml')
s=json.loads((p/'forecast_spec.json').read_text());s['card_id']=c['task']['id'];(p/'forecast_spec.json').write_text(json.dumps(s))
d=pd.read_parquet(p/'synthetic_history.parquet');d['date']=pd.date_range(end='2018-08-31',periods=len(d),freq='W-FRI').strftime('%Y-%m-%d');d.to_parquet(p/'synthetic_history.parquet',index=False)

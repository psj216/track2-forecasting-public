"""Executive summary: score completed isolated forecasts against separately materialized labels."""
import hashlib
import json
import pathlib
import sys
import pandas as pd
from prepare_ecb import load,GROUPS
from evaluate import evaluate_one,summary


def run(raw,local_inputs,artifacts,out):
    frame=load(raw);root=pathlib.Path(local_inputs);artifacts=pathlib.Path(artifacts)
    labels=root/'labels';labels.mkdir(exist_ok=True)
    rows=[];missing=[];hash_checks=[]
    for group,assets in GROUPS.items():
        own=json.loads((root/('inputs-'+group)/'input-manifest.json').read_text())
        found=list(artifacts.glob('**/input-manifest.json'))
        matches=[p for p in found if json.loads(p.read_text())['inputs'][0]['group']==group]
        assert len(matches)==1
        remote=json.loads(matches[0].read_text());assert own==remote
        hash_checks.append(dict(group=group,input_manifests_equal=True,requested=50))
        for entry in own['inputs']:
            name=entry['id'];unit=root/('inputs-'+group)/name
            forecasts=list(artifacts.glob('**/'+name+'/forecast.parquet'));assert len(forecasts)==1,(name,forecasts)
            forecast=forecasts[0];receipt=json.loads(forecast.with_name('receipt.json').read_text())
            assert receipt['exit']==0
            for f,h in receipt['output_hashes'].items():assert hashlib.sha256(forecast.with_name(f).read_bytes()).hexdigest()==h
            origin=pd.Timestamp(entry['origin']);records=[];absent=[]
            for a in assets:
                for h in [1,2,3,4]:
                    date=origin+pd.offsets.BDay(h)
                    if date not in frame.index or pd.isna(frame.loc[date,a]) or pd.isna(frame.loc[date,'USD']):
                        absent.append(dict(asset=a,horizon=h,target_date=str(date.date())))
                    else:records.append(dict(asset=a,horizon=h,value=float(frame.loc[date,a]/frame.loc[date,'USD'])))
            label=labels/(name+'.parquet');pd.DataFrame(records,columns=['asset','horizon','value']).to_parquet(label,index=False)
            if absent:
                missing.append(dict(id=name,origin=entry['origin'],missing=absent,forecast_success=True,status='MISSING_EXACT_LABEL_GRID'));continue
            row=evaluate_one(unit,forecast,label);assert row['status']=='SCORED';row['market']=group
            row['PIT']='PIT_AUTHENTICITY_LIMITED';row['input_observation_max']=entry['observation_max']
            row['baseline_wall_seconds']=receipt['wall_seconds'];rows.append(row)
            print(name,'SCORED',flush=True)
    result={'executive_summary':'Current-vintage2025 ECB chronological diagnostic, not independent PIT-authentic OOS; no label imputation.',
        'requested_cards':100,'requested_origins':50,'independence':'UNKNOWN','PIT':'PIT_AUTHENTICITY_LIMITED',
        'input_hash_verification':hash_checks,'summary':summary(rows),'missing_grids':missing,'cards':rows}
    pathlib.Path(out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))

if __name__=='__main__':run(*sys.argv[1:])

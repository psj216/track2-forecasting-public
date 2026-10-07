"""Executive summary: source/calendar/price-only design before any future label loading."""
from pathlib import Path
import json
import numpy as np,pandas as pd
from .source import *
from backtesting.new_information_search02.analyze import price_states
def price_frame(parent):
 features,levels=price_states(Path(parent))
 return features,levels
def build(private):
 p=Path(private);states=json.loads((p/'source_states.json').read_text());cache=json.loads((p/'baseline-byte-recovery.json').read_text())['cache_origins'];features,levels=price_frame(p/'parent-extracted/private');rows=[]
 for o in sorted(cache):
  if not '2016-01-01'<=o<='2024-12-18':continue
  c=cutoff(o);s=asof(states,c)
  if s is None:continue
  eligible=[d for d in features.index if activation(d+pd.offsets.BDay(1))<=c]
  if not eligible:continue
  d=eligible[-1];px=features.loc[d]
  if not np.isfinite(px.to_numpy()).all():continue
  lag5=asof(states,c,5);lag21=asof(states,c,21);prev=asof(states,c,previous=True)
  for asset in ASSETS:
   own='DGS2' if asset=='UST_2Y' else 'DGS5'
   for h in HORIZONS:
    # Calendar-only planned maturity; exact inherited target_end verified after PRE.
    end=pd.Timestamp(o)+pd.offsets.BDay(h)
    if end>pd.Timestamp('2024-12-18'):continue
    row={'origin':o,'asset':asset,'horizon':h,'planned_target_end':str(end.date()),'year':int(o[:4]),'cutoff':c.isoformat(),'release_id':s['release_id'],'release_date':s['release_date'],'source_age':s['source_age'],'SEP':s['value'],'SEP5':lag5['value'] if lag5 else np.nan,'SEP21':lag21['value'] if lag21 else np.nan,'persistence_direction':np.sign(prev['value']) if prev else 0.,'price_direction':np.sign(px[own+'_21BD']),'price_observation_date':str(d.date()),'price_available_at':activation(d+pd.offsets.BDay(1)).isoformat()}
    row.update({'price_'+k:v for k,v in px.to_dict().items()});rows.append(row)
 frame=pd.DataFrame(rows);frame.to_parquet(p/'design_calendar.parquet',index=False);csv(OUT/'source_origin_calendar.csv',frame.to_dict('records'))
 save(OUT/'calendar_manifest.json',{'executive_summary':'All source-active exact inherited monthly forecast caches, shared price-available origins, no outcome-based filtering.','origins':int(frame.origin.nunique()),'calendar_cells':len(frame),'evaluation_origins_before_truth_validation':int(frame.loc[frame.year>=2020].origin.nunique()),'origin_dates':sorted(frame.origin.unique()),'calendar_SHA256':digest(p/'design_calendar.parquet'),'price_features':list(features.columns),'price_file_SHA256':digest(p/'parent-extracted/private/fred_prices.txt'),'price_vintage':'Inherited bounded official H15 current-vintage probe, not exact original price-model cache; no claim of immutable historical vintages','age_semantics':'Weekdays exactly inherited; holidays not newly introduced','cache_grid_limit':'Monthly cache availability inherited from earlier source studies; missing months not regenerated or chosen by outcomes','outcomes_loaded':False})
 return frame

"""## Executive summary (read this first)
Deterministic panel-prefix summaries and timestamp-filtered text digest; no outcome data.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path
from qfbench2_track_forecasting.cli import _read_panels, _series
from qfbench2_track_forecasting.text_evidence import read_frozen_corpus
from .engine import CONFIG

def summarize_series(s,asof):
    s=s[np.isfinite(s.to_numpy())]
    if len(s)==0: raise ValueError('empty_series')
    x=s.to_numpy(dtype=float);diff=np.diff(x[-64:]);window=x[-64:]
    result={'latest':float(x[-1]),'observations':len(x),'latest_date':str(s.index[-1])[:10], 'staleness_calendar_days':max(0,(pd.Timestamp(asof)-pd.Timestamp(s.index[-1])).days), 'missing_values_excluded':False}
    for lag in CONFIG['numeric_windows']:
        result['move_'+str(lag)+'_observations']=float(x[-1]-x[-lag-1]) if len(x)>lag else None
    result['realized_change_sd']=float(np.std(diff)) if len(diff) else 0.
    result['range_position']=(float((x[-1]-min(window))/(max(window)-min(window))) if max(window)>min(window) else .5)
    result['drawdown_from_recent_max']=float(x[-1]-max(window))
    return result

def build_context(card,panels_dir,text_dir,asof,assets,horizons,base):
    panels=_read_panels(Path(panels_dir))
    numeric={a:summarize_series(_series(panels,a,asof),asof) for a in assets}
    corpus=read_frozen_corpus(Path(text_dir),asof)
    docs=[]
    for d in corpus.documents[:CONFIG['max_documents']]:
        # Documents have passed publication checks before their bytes were opened.
        docs.append({'id':d.doc_id,'timestamp':d.timestamp,'source':d.source,'excerpt':' '.join(d.text.split())[:CONFIG['document_chars']]})
    return {'card':{'asof':asof,'assets':assets,'horizons':horizons,'target_type':card['targets'].get('target_type','level'),'target_frequency':card['targets'].get('target_frequency','daily'),'value_unit':card['targets'].get('value_unit','unspecified'),'panel_metadata':card.get('panels',{}),'regime_names':list(CONFIG['regimes'])},'numeric':numeric,'baseline':[{'asset':a,'horizon':h,'median':float(np.median(base[:,i,j])),'SD':float(np.std(base[:,i,j]))} for i,a in enumerate(assets) for j,h in enumerate(horizons)],'dated_text':docs}

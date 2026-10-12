"""## Executive summary (read this first)
Exercise strict replies, as-of safety, coherent shifts, proxy binding and exact fallbacks.
"""
import copy
import json
import os
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
import pytest
from moonshot15_engine import engine
from moonshot15_engine.context import summarize_series,build_context
from backtesting.moonshot15.runtime.synthetic import reply
CTX={'card':{'assets':['UST_2Y','EUR'],'horizons':[5,63]}}
KINDS=['A','B','C','D','E1','E2']
@pytest.mark.parametrize('kind',KINDS)
def test_closed_valid_reply(kind):
    r=reply(kind,CTX)
    assert engine.parse(json.dumps(r),kind,CTX['card']['assets'],CTX['card']['horizons'])==r
@pytest.mark.parametrize('kind',KINDS)
def test_unknown_keys_reject(kind):
    r=reply(kind,CTX);r['extra']=1
    with pytest.raises(engine.InvalidReply):engine.parse(json.dumps(r),kind,['UST_2Y','EUR'],[5,63])
@pytest.mark.parametrize('kind',KINDS)
def test_duplicate_json_reject(kind):
    with pytest.raises(engine.InvalidReply):engine.parse('{"x":1,"x":2}',kind,['UST_2Y','EUR'],[5,63])
@pytest.mark.parametrize('bad',[float('nan'),float('inf'),-1,11,True,'0.7'])
def test_invalid_magnitude_reject(bad):
    r=reply('B',CTX);r['cells'][0]['standardized_shift']=bad
    with pytest.raises((ValueError,engine.InvalidReply)):engine.parse(json.dumps(r),'B',['UST_2Y','EUR'],[5,63])
@pytest.mark.parametrize('variant',list('ABCDE'))
def test_transform_finite_capped_and_deterministic(variant):
    base=np.random.default_rng(91).normal(size=(300,2,2))
    r=reply('E2' if variant=='E' else variant,CTX)
    a,m=engine.transform(base,variant,r,['UST_2Y','EUR'],[5,63]);b,_=engine.transform(base,variant,r,['UST_2Y','EUR'],[5,63])
    assert np.array_equal(a,b) and np.isfinite(a).all()
    assert np.max(np.abs((a-base)/base.std(axis=0)))<=engine.CONFIG['variants'][variant]['location_cap_sd']+1e-12
    if variant in 'ABD':assert np.allclose(a-a.mean(axis=0),base-base.mean(axis=0),atol=1e-13)
    else:assert m['scenario_labels_reused_all_cells']
def test_scenario_label_is_joint_not_cell_random():
    s=reply('C',CTX)['scenarios'];z,labels=engine.scenario_shifts(s,['UST_2Y','EUR'],[5,63],300,3)
    for label in range(3):
        rows=z[labels==label];assert np.array_equal(rows,np.broadcast_to(rows[0],rows.shape))
def test_zero_probability_and_unknown_asset():
    r=reply('C',CTX)
    for s in r['scenarios']:s['probability']=0
    with pytest.raises(engine.InvalidReply):engine.validate(r,'C',['UST_2Y','EUR'],[5,63])
    r=reply('B',CTX);r['cells'][0]['asset']='INJECTED'
    with pytest.raises(engine.InvalidReply):engine.validate(r,'B',['UST_2Y','EUR'],[5,63])
def test_loading_quote_direction_and_unknown():
    assert engine.loading('EUR')[5]<0 and engine.loading('JPY')[5]>0
    assert (engine.loading('UNKNOWN')==0).all()
def test_literal_official_proxy_contract(monkeypatch):
    from moonshot15_engine import official_transport as t
    monkeypatch.setenv('http_proxy','http://testuser:testpass@proxy.test:8080')
    observed={}
    class Conn:
        def __init__(self,host,port,timeout):observed.update(host=host,port=port,timeout=timeout)
        def request(self,method,path,body,headers):observed.update(method=method,path=path,headers=headers)
        def getresponse(self):return self
        status=200
        def read(self,n):return b'{"ok":true}'
        def close(self):pass
    monkeypatch.setattr(t.http.client,'HTTPConnection',Conn)
    assert t._house_reply('http://house.test:8000','synthetic-testing-only',b'{}')['ok']
    assert observed['path']=='http://house.test:8000/v1/chat/completions'
    assert observed['headers']['Authorization']=='Bearer synthetic-testing-only'
    assert observed['headers']['Proxy-Authorization']=='Basic dGVzdHVzZXI6dGVzdHBhc3M='
@pytest.mark.parametrize('url',['https://vendor.test','http://house.test/x','http://user:pass@house.test','http://house.test?token=x'])
def test_no_vendor_or_path_downgrade(monkeypatch,url):
    from moonshot15_engine.official_transport import _house_reply
    monkeypatch.setenv('http_proxy','http://u:p@proxy:8080')
    with pytest.raises(ValueError):_house_reply(url,'synthetic',b'{}')
def test_future_panel_and_text_do_not_change_context(tmp_path):
    panel=tmp_path/'panel';panel.mkdir();text=tmp_path/'text';text.mkdir()
    df=pd.DataFrame({'date':['2010-01-01','2010-01-02','2010-02-01'],'asset':['UST_2Y']*3,'value':[1.,2.,999.]})
    df.to_parquet(panel/'x.parquet')
    (text/'corpus_index.json').write_text(json.dumps({'documents':[{'doc_id':'future','timestamp':'2010-02-01','path':'future.txt'}]}))
    (text/'future.txt').write_text('never use future')
    card={'targets':{'target_type':'level','target_frequency':'daily'}};base=np.zeros((200,1,1))
    before=build_context(card,panel,text,'2010-01-02',['UST_2Y'],[5],base)
    df.loc[2,'value']=-999;df.to_parquet(panel/'x.parquet');(text/'future.txt').write_text('changed future')
    after=build_context(card,panel,text,'2010-01-02',['UST_2Y'],[5],base)
    assert before==after and before['dated_text']==[]
@pytest.mark.parametrize('failure',[ValueError('credential-must-not-log'),TimeoutError('secret')])
def test_failed_call_preserves_exact_baseline(tmp_path,monkeypatch,failure):
    from moonshot15_engine import cli
    import hashlib
    import tomllib
    unit=Path(__file__).parents[1]/'units/t2-F2-eur-parity-2022'
    asof=tomllib.loads((unit/'card.toml').read_text())['provenance']['data_cutoff']
    for k,v in {'MODEL_ENDPOINT':'http://house.test','MODEL_NAME':'mock','MODEL_TOKEN':'synthetic','http_proxy':'http://u:p@proxy:8080','M15_VARIANT':'B'}.items():monkeypatch.setenv(k,v)
    monkeypatch.setattr(cli,'request',lambda *a:(_ for _ in ()).throw(failure))
    out=tmp_path/'forecast.parquet'
    cli.main(['--panels',str(unit),'--text',str(unit/'text'),'--asof',asof,'--out',str(out)])
    m=json.loads((tmp_path/'forecast_meta.json').read_text())['moonshot15']
    assert not m['applied'] and m['requests_attempted']==1
    assert hashlib.sha256(out.read_bytes()).hexdigest()==m['baseline_parquet_SHA256']
    assert 'credential-must-not-log' not in (tmp_path/'forecast_meta.json').read_text()
    assert 'secret' not in (tmp_path/'forecast_rationale.md').read_text()
def test_parameters_frozen():
    c=engine.CONFIG
    assert c['seed']==31815 and c['max_tokens']==4000 and c['retry_count']==0
    assert c['variants']['E']['requests']==2
    assert [c['variants'][k]['location_cap_sd'] for k in 'ABCDE']==[1.25,2.5,3.,2.,4.]

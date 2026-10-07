"""Executive summary: fixed source/PIT/model/purge rules and original-byte preservation."""
import copy,json,os,ast
from pathlib import Path
import numpy as np,pandas as pd,pytest
from backtesting.persistent_direction02 import source as s,model as m,evaluate as e
from backtesting.persistent_direction02.aggregate import decide
P=Path(os.environ.get('PERSISTENT02_PRIVATE','/unavailable'))

def row(date='2020-03-18',value=.1,**kw):
 y=int(date[:4]);r=dict(release_id='SEP_'+date,release_date=date,available_at=s.activation(date).isoformat(),CY=1.,NCY=1.+value,CY_target=y,NCY_target=y+1,value=value,active=True,version=0);r.update(kw);return r

def test_constants():
 assert s.PARENT=='6653df8c61042c4642be3e2ed37b52daeea16de7';assert s.AMPLITUDE==.05;assert s.SEED==31802;assert s.HORIZONS==(5,21,63,126,189);assert s.ASSETS==('UST_2Y','UST_5Y')
@pytest.mark.parametrize('when,active',[('2020-03-18 12:00',False),('2020-03-18 23:59:58',False),('2020-03-19',True)])
def test_publication_cutoff(when,active):assert (s.asof([row()],pd.Timestamp(when,tz='America/New_York')) is not None)==active

def test_future_mutation():
 r=[row()];at=pd.Timestamp('2020-04-01',tz='America/New_York');assert s.asof(r,at)==s.asof(r+[row('2021-03-17',99)],at)
def test_publication_shift():
 r=row();at=pd.Timestamp('2020-03-19',tz='America/New_York');assert s.asof([r],at);r['available_at']=s.activation('2020-03-20').isoformat();assert s.asof([r],at) is None

def test_rollover():
 r=row('2019-12-11',.4);q=s.asof([r],pd.Timestamp('2020-01-07',tz='America/New_York'));assert q['CY_target']==2019 and q['NCY_target']==2020 and q['value']==.4

def test_correction_later():
 a=row();b=row(value=99,version=1,available_at=s.activation('2020-04-10').isoformat());at=pd.Timestamp('2020-04-01',tz='America/New_York');assert s.asof([a,b],at)['value']==.1;assert s.asof([a,b],pd.Timestamp('2020-04-13',tz='America/New_York'))['value']==99

def test_correction_inactive():assert s.asof([row(active=False)],pd.Timestamp('2020-04-01',tz='America/New_York')) is None

def test_source_order():
 a,b=row(),row('2020-06-10',.5);at=pd.Timestamp('2020-07-01',tz='America/New_York');assert s.asof([a,b],at)==s.asof([b,a],at)
def test_duplicate():assert len(s.canonical([row(),row()]))==1

def test_conflict():
 with pytest.raises(ValueError):s.canonical([row(),row(value=2,CY=2)])
@pytest.mark.parametrize('days,active',[(90,True),(91,False)])
def test_age(days,active):
 r=row();at=(pd.Timestamp(r['release_date'])+pd.offsets.BDay(days)).tz_localize('America/New_York')+pd.Timedelta(hours=23,minutes=59,seconds=59);assert (s.asof([r],at) is not None)==active

def test_current_history_rejected():
 with pytest.raises(ValueError):s.parse('<table><tr><td>Current history 9.9</td></tr></table>','2020-03-18')
@pytest.mark.parametrize('stub,cy,ncy',[('td','.1','0.1'),('th','1.4','2.1')])
def test_old_new_field_semantics(stub,cy,ncy):
 html=f'<table><thead><tr><th id="med">Median</th></tr><tr><th id="y0" headers="med">2020</th><th id="y1" headers="med">2021</th></tr></thead><tbody><tr><{stub}>Federal funds rate</{stub}><td headers="med y0">{cy}</td><td headers="med y1">{ncy}</td></tr></tbody></table>';r=s.parse(html,'2020-09-16');assert r['value']==float(ncy)-float(cy)

def test_model_parameters_scaler():
 x=np.arange(90.).reshape(30,3);y=np.tile([0,1],15);sc,mo=m.fit(x,y);assert mo.C==1 and mo.class_weight is None and mo.fit_intercept and mo.penalty=='l2';assert np.array_equal(sc.mean_,x.mean(axis=0));before=sc.mean_.copy();m.probability((sc,mo),np.ones((2,3))*1e9);assert np.array_equal(before,sc.mean_)
@pytest.mark.parametrize('p,sg',[(.49,-1),(.5,0),(.51,1)])
def test_threshold(p,sg):assert m.direction([p])[0]==sg
@pytest.mark.parametrize('sg',[-1,0,1])
def test_geometry(sg):
 d=np.random.default_rng(31802).normal(size=(500,4));sd=d.std(axis=0);shift=m.shift(sd,sg);assert np.array_equal(shift,.05*sd*sg);c=m.translate(d,shift);assert np.allclose(c.std(axis=0),sd,atol=1e-14);assert np.array_equal(np.argsort(c,axis=0),np.argsort(d,axis=0))

def test_purge():
 d=pd.DataFrame({'origin':['2019-01-02','2019-12-03','2020-01-07','2015-01-07'],'target_end':['2019-03-01','2020-02-01','2020-02-01','2015-02-01'],'horizon':[21]*4,'release_id':['A','B','C','D']});assert m.training_mask(d,2020,pd.Timestamp('2020-01-06',tz='America/New_York'),['C']).tolist()==[True,False,False,False]
@pytest.mark.parametrize('kind',['STATE','DATE'])
def test_null_determinism_chronology(kind):
 states=[row('2019-03-20',.1),row('2019-06-19',.2),row('2019-09-18',.3)];a=e.null_source(states,kind,3);assert a==e.null_source(states,kind,3)
 for i,r in enumerate(a):
  if kind=='STATE':assert r['value'] in [x['value'] for x in states[:i+1]]
  else:assert pd.Timestamp(r['available_at'])>=pd.Timestamp(states[i]['available_at'])

def test_fast_asof_matches():
 states=[row('2019-03-20',.1),row('2019-06-19',.2,active=False),row('2019-09-18',.3)];r=pd.DataFrame({'origin':['2019-03-01','2019-04-02','2019-07-02','2019-10-01','2020-02-04']})
 for kind in ['STATE','DATE']:
  a=e.null_source(states,kind,4);expected=[(s.asof(a,s.cutoff(o)) or {}).get('value',np.nan) for o in r.origin];assert np.allclose(e.source_values(a,r),expected,equal_nan=True)

def test_no_amplitude_or_model_selection():
 tree=ast.parse(Path(e.__file__).read_text());assert not any(isinstance(n,ast.Name) and n.id in ['Ridge','GridSearchCV','RandomForestRegressor'] for n in ast.walk(tree));assert e.NAMES[1]=='SEP_DIRECTION_FIXED005'

def test_decision_timing_invalidation():
 rr={n:.99 for n in e.NAMES};rr[e.PRIMARY]=.985;rr['5BD_DELAYED']=.984;ci={b:{'primary_ratio':[.97,1.01]} for b in ['release','year','week']};v,nxt,_,g=decide(rr,[.99]*5,ci,{'year':.4,'release_id':.4},{'N':{'q05':1.}});assert v=='NO' and nxt=='PERSISTENCE-VS-INFORMATION-AUDIT-03'
@pytest.mark.skipif(not (P/'source_states.json').exists(),reason='private source inputs not available')
def test_source_rebuild_hashes():
 states=json.loads((P/'source_states.json').read_text());manifest=json.loads((s.OUT/'source_dataset_manifest.json').read_text());assert s.digest(P/'source_states.json')==manifest['states_SHA256'];assert len(states)==35;assert json.loads((s.OUT/'source_readiness.json').read_text())['DATASET_READY']
 for r in states:
  f=P/'parent-extracted/private/documents'/('sep_'+r['release_date'].replace('-','')+'.html');q=s.parse(f.read_text(),r['release_date']);assert q['value']==r['value'] and q['CY_target']==r['CY_target']
@pytest.mark.skipif(not (P/'design_calendar.parquet').exists(),reason='private design unavailable')
def test_calendar_firewall():
 rows=pd.read_parquet(P/'design_calendar.parquet');assert not set(rows)&{'truth','y','raw_center_error','median','sd'};assert (rows.planned_target_end<='2024-12-18').all();assert set(rows.asset)==set(s.ASSETS);assert rows.source_age.le(90).all();assert all(pd.Timestamp(a)<=pd.Timestamp(c) for a,c in zip(rows.price_available_at,rows.cutoff))
@pytest.mark.skipif(not (P/'scores.npz').exists(),reason='evaluation intentionally not available before PRE')
def test_result_hashes_purge_geometry():
 e.verify(P);rows=pd.read_parquet(P/'evaluation_ledger.parquet')
 for year,tr,te,c in e.folds(rows):
  assert (rows.iloc[tr].year<year).all();assert (pd.to_datetime(rows.iloc[tr].target_end)<c.tz_localize(None).normalize()).all();assert not set(rows.iloc[tr].release_id)&set(rows.iloc[te].release_id)
 assert json.loads((s.OUT/'draw_geometry_audit.json').read_text())['ranks_unchanged'];scores=np.load(P/'scores.npz');summary=json.loads((s.OUT/'primary_score_summary.json').read_text());assert abs(scores['losses'][1].sum()/scores['base'].sum()-summary['primary']['CRPS_ratio'])<1e-14

def test_parent_main_protection():
 import subprocess
 assert subprocess.check_output(['git','rev-parse','origin/main'],cwd=s.ROOT,text=True).strip()=='e1b5cf3b3a87966e902332ef3cc5c0ed2dbffee8'
 if (P/'protected_parent_hashes.json').exists():
  hashes=json.loads((P/'protected_parent_hashes.json').read_text());assert all(s.digest(s.ROOT/n)==v for n,v in hashes.items())

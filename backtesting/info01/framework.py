"""## Executive summary (read this first)
Apply frozen source-quality gates, timezone-safe availability, and a ten-item feasibility score.
No realized outcomes, forecast fitting, prediction, or scoring functions are imported.
"""
from datetime import datetime,date,time,timedelta
from zoneinfo import ZoneInfo
from urllib.parse import urlsplit,urlunsplit
import json,hashlib
from pathlib import Path
PARENT='a37f232d5fcdf8dd8fa1c44e30bde68b3dda458c'
BRANCH='track2/info-01-new-information-audit'
MAIN_BEFORE='e1b5cf3b3a87966e902332ef3cc5c0ed2dbffee8'
RESEARCH_CUTOFF=date(2024,12,18)
CRITERIA=('pit_integrity','novel_information','historical_depth','asset_coverage','horizon_relevance','machine_readability','reproducibility','offline_feasibility','licensing_contest','implementation_ease')
GROUPS=('FX','Rates','Equity_Factor','Commodity','Macro_Other')
MAP_VALUES={'DIRECT','PLAUSIBLE','WEAK','NONE'}
HORIZONS=(5,21,63,126,189)
PRIORITY={'TRUE_CONSENSUS':0,'MARKET_IMPLIED':1,'POLICY_EXPECTATIONS':1,'POSITIONING':2,'LIQUIDITY_FUNDING':3,'EXPECTATION_SURVEY_NOWCAST':4,'FUNDAMENTAL_VALUATION':5,'NEWS_EVENT':6}
REQUIRED_ARTIFACTS=('environment_audit.json','parent_research_ledger.json','already_tested_channels.csv','competition_data_constraints.md','source_inventory.csv','source_documentation_manifest.json','pit_integrity_matrix.csv','novelty_matrix.csv','asset_mapping.csv','horizon_mapping.csv','availability_probe.json','source_scorecard.csv','source_shortlist.json','selected_primary_source.json','independent_validation_audit.json','location02_frozen_draft.md','final_decision.json','execution_audit.json','artifact_manifest.json')
def sha256(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps({'executive_summary':'Source availability/quality audit only; no new forecasts or outcome scores.',**value},ensure_ascii=False,indent=2)+'\n')
def classify_pit(evidence):
 if evidence.get('exact_vintage')and evidence.get('release_proven')and evidence.get('field_revision_audited'):return 'A'
 if evidence.get('original_release_values')and evidence.get('release_proven')and evidence.get('field_revision_audited'):return 'B'
 if evidence.get('current_revised_history')and evidence.get('minor_revisions_documented'):return 'C'
 return 'D'
def aware(value):
 d=datetime.fromisoformat(value)
 if d.tzinfo is None or d.utcoffset()is None:raise ValueError('Timezone-aware timestamp required')
 return d

def release_bound(day,timezone='America/New_York',clock=None):
 d=date.fromisoformat(day);t=time.fromisoformat(clock)if clock else time(23,59,59)
 return datetime.combine(d,t,ZoneInfo(timezone))
def available_at(release,cutoff):return aware(release)<=aware(cutoff)
def preceding_business_cutoff(origin,timezone='America/New_York'):
 d=date.fromisoformat(origin)-timedelta(days=1)
 while d.weekday()>4:d-=timedelta(days=1)
 return datetime.combine(d,time(16),ZoneInfo(timezone))
def bounded_samples(rows,cutoff=RESEARCH_CUTOFF):
 for row in rows:
  if aware(row['available_at']).date()>cutoff:raise ValueError('Post-cutoff sample rejected')
 return rows

def source_total(values):
 if set(values)!=set(CRITERIA):raise ValueError('Exactly ten fixed criteria required')
 if any(type(v)is not int or v not in (0,1,2)for v in values.values()):raise ValueError('Integer scores0–2required')
 return sum(values.values())
def normalized_url(url):
 x=urlsplit(url);return urlunsplit((x.scheme.lower(),x.netloc.lower(),x.path.rstrip('/'),x.query,''))
def unique_sources(sources):
 ids=set();keys=set()
 for s in sources:
  key=(s['provider'].casefold(),s['dataset_identity'].casefold())
  if s['source_id']in ids or key in keys:raise ValueError('Duplicate source/dataset identity')
  ids.add(s['source_id']);keys.add(key)
 return sources

def sufficient_history(start,end):
 a=date.fromisoformat(start);b=min(date.fromisoformat(end),RESEARCH_CUTOFF)
 eras=sum(a<=date(hi,12,31)and b>=date(lo,1,1)for lo,hi in [(2010,2013),(2014,2017),(2018,2020),(2021,2024)])
 return (b-a).days>=8*365.25 and eras>=3

def primary_gate(s):
 failures=[]
 for label,condition in [('PIT_not_A_B',s['pit']in('A','B')),('timestamp_unproven',s['release_proven']),('low_or_redundant_novelty',s['novelty']in('HIGH','MEDIUM')),('same_tested_information',not s['already_tested_equivalent']),('insufficient_history',sufficient_history(s['earliest_history'],s['accepted_latest_history'])),('no_machine_or_reliable_transform',s['transformable']),('not_reproducible',s['reproducible']),('access_not_verified',s['access']=='ACCESSIBLE'),('research_rights_unverified_or_forbidden',s['research_use']=='ALLOWED'),('contest_forbidden',s['contest_usability']!='NOT_ALLOWED'),('no_actual_asset_mapping',bool(s['eligible_assets'])),('quality_below_14',source_total(s['scores'])>=14)]:
  if not condition:failures.append(label)
 return not failures,failures

def shortlist(sources):
 unique_sources(sources)
 eligible=[s for s in sources if primary_gate(s)[0]]
 eligible.sort(key=lambda s:(-source_total(s['scores']),PRIORITY[s['type']],s['source_id']))
 return eligible[:3]
def validate_mappings(rows,asset_universe):
 for s in rows:
  if set(s['asset_mapping'])!=set(GROUPS)or not set(s['asset_mapping'].values())<=MAP_VALUES:raise ValueError('Bad asset-group mapping')
  if not set(s['eligible_assets'])<=set(asset_universe):raise ValueError('Unknown asset')
  if set(s['horizon_mapping'])!=set(map(str,HORIZONS)):raise ValueError('Exact five BD horizons required')
 return True

def require_parent(branch,parent,main_before,main_after,clean=True):
 if branch!=BRANCH or parent!=PARENT or main_before!=main_after or not clean:raise ValueError('Frozen parent/main protection violation')
 return True

def validate_artifacts(root):
 root=Path(root)
 for name in REQUIRED_ARTIFACTS:
  f=root/name
  if not f.exists()or not f.stat().st_size:raise ValueError('Missing required artifact: '+name)
  if f.suffix=='.json':json.loads(f.read_text())
 decision=json.loads((root/'final_decision.json').read_text())
 keys=('INFO01_RESULT','SELECTED_PRIMARY_SOURCE','PIT_CLASS','NOVELTY_CLASS','CONTEST_COMPATIBILITY','ASSET_COVERAGE','HORIZON_COVERAGE','INDEPENDENT_VALIDATION_UNIVERSE','READY_FOR_LOCATION02','READY_FOR_SUBMISSION','T0_RIDGE_STATUS','NEXT_STEP')
 if any(k not in decision for k in keys)or decision['READY_FOR_SUBMISSION']is not False or decision['T0_RIDGE_STATUS']!='FROZEN_LEAD_ONLY':raise ValueError('Decision schema/freeze violation')
 return True

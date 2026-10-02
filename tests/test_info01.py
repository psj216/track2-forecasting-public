"""## Executive summary (read this first)
Test PIT, availability, deterministic source selection, asset/schema and Git-parent safety boundaries.
"""
from copy import deepcopy
from pathlib import Path
import json
import pytest
from backtesting.info01.framework import *

def source():
 return dict(source_id='survey',provider='bank',dataset_identity='surveyX',type='TRUE_CONSENSUS',pit='B',release_proven=True,novelty='HIGH',already_tested_equivalent=False,earliest_history='2011-01-01',accepted_latest_history='2024-12-18',transformable=True,reproducible=True,access='ACCESSIBLE',research_use='ALLOWED',contest_usability='UNKNOWN_REQUIRES_CONFIRMATION',eligible_assets=['UST_2Y'],scores={k:2 for k in CRITERIA},asset_mapping={k:'NONE'for k in GROUPS},horizon_mapping={str(h):'PLAUSIBLE'for h in HORIZONS})
@pytest.mark.parametrize('e,w',[(dict(exact_vintage=True,release_proven=True,field_revision_audited=True),'A'),(dict(original_release_values=True,release_proven=True,field_revision_audited=True),'B'),(dict(current_revised_history=True,minor_revisions_documented=True),'C'),(dict(current_revised_history=True),'D'),(dict(original_release_values=True),'D')])
def test_pit_classification(e,w):assert classify_pit(e)==w

def test_score_has_exactly_ten_fixed_items():assert source_total(source()['scores'])==20
@pytest.mark.parametrize('v',[-1,3,True,1.1])
def test_bad_quality_score_rejected(v):
 x=source()['scores'];x['pit_integrity']=v
 with pytest.raises(ValueError):source_total(x)
def test_missing_criterion_rejected():
 x=source()['scores'];x.pop('pit_integrity')
 with pytest.raises(ValueError):source_total(x)
def test_naive_time_rejected():
 with pytest.raises(ValueError):available_at('2024-01-01T09:00:00','2024-01-02T00:00:00+00:00')
def test_measurement_day_is_not_release_day():assert not available_at('2024-01-12T15:30:00-05:00','2024-01-09T16:00:00-05:00')
def test_future_release_rejected():assert not available_at('2024-12-18T16:01:00-05:00','2024-12-18T16:00:00-05:00')
def test_same_moment_available():assert available_at('2024-12-18T16:00:00-05:00','2024-12-18T21:00:00+00:00')
def test_date_only_release_uses_upper_bound():assert release_bound('2024-01-12').hour==23

def test_weekend_prior_cutoff():assert preceding_business_cutoff('2024-01-15').isoformat()=='2024-01-12T16:00:00-05:00'
def test_new_york_dst():assert release_bound('2024-07-01').utcoffset().total_seconds()==-14400

def test_numeric_post_cutoff_not_inspected():
 with pytest.raises(ValueError):bounded_samples([{'available_at':'2025-01-01T00:00:00+00:00'}])
def test_source_duplicate_detected():
 a=source();b=deepcopy(a);b['source_id']='alias'
 with pytest.raises(ValueError):unique_sources([a,b])
def test_url_fragments_are_not_new_sources():assert normalized_url('https://BANK.gov/a/#new')=='https://bank.gov/a'
@pytest.mark.parametrize('field,value',[('pit','D'),('pit','C'),('release_proven',False),('novelty','REDUNDANT'),('already_tested_equivalent',True),('access','ACCESS_REQUIRES_USER'),('research_use','UNKNOWN'),('contest_usability','NOT_ALLOWED'),('eligible_assets',[]),('reproducible',False),('earliest_history','2020-01-01')])
def test_hard_source_gate(field,value):
 x=source();x[field]=value;assert not primary_gate(x)[0]
def test_unknown_contest_permission_stays_research_candidate():assert primary_gate(source())[0]
def test_no_rank_by_future_outcomes():
 a=source();b=deepcopy(a);b['future_score']=.00001;b['winner']='T0Ridge';assert shortlist([a])[0]['source_id']==shortlist([b])[0]['source_id']
def test_shortlist_at_most_three():
 rows=[]
 for i in range(5):
  x=source();x.update(source_id=str(i),dataset_identity=str(i));rows.append(x)
 assert len(shortlist(rows))==3

def test_asset_mapping_rejects_foreign_asset():
 x=source()
 with pytest.raises(ValueError):validate_mappings([x],['MKT'])
def test_horizon_schema_mandatory():
 x=source();x['horizon_mapping'].pop('189')
 with pytest.raises(ValueError):validate_mappings([x],['UST_2Y'])
def test_valid_asset_mapping():assert validate_mappings([source()],['UST_2Y'])
@pytest.mark.parametrize('branch,parent,main_after,clean',[('main',PARENT,MAIN_BEFORE,True),(BRANCH,'0'*40,MAIN_BEFORE,True),(BRANCH,PARENT,'0'*40,True),(BRANCH,PARENT,MAIN_BEFORE,False)])
def test_parent_main_guard(branch,parent,main_after,clean):
 with pytest.raises(ValueError):require_parent(branch,parent,MAIN_BEFORE,main_after,clean)
def test_exact_parent_guard():assert require_parent(BRANCH,PARENT,MAIN_BEFORE,MAIN_BEFORE)
def test_artifact_missing_is_failure(tmp_path):
 with pytest.raises(ValueError):validate_artifacts(tmp_path)
def test_frozen_metadata_file():
 x=json.loads(Path('backtesting/info01/frozen_protocol.json').read_text());assert x['parent_sha']==PARENT and x['new_forecast_scores']==0 and x['new_forecast_fits']==0

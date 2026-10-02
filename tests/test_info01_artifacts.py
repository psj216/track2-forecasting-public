"""Executive summary: verify final source-audit evidence and scientific scope, without target data."""
import csv,json,hashlib
from pathlib import Path
from backtesting.info01.framework import validate_artifacts,shortlist,primary_gate,aware,RESEARCH_CUTOFF
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'backtesting/info01/results'
def read(n):return json.loads((OUT/n).read_text())
def test_complete_artifacts_and_non_submission_decision():
 assert validate_artifacts(OUT)
 d=read('final_decision.json')
 assert d['INFO01_RESULT']=='SOURCES_FOUND_RESEARCH_ONLY'
 assert d['READY_FOR_LOCATION02']is False and d['READY_FOR_SUBMISSION']is False
 assert d['NEW_FORECAST_FITS']==d['NEW_FORECAST_SCORES']==0
def test_precommitted_quality_ranking_and_excluded_tested_channels():
 s=json.loads((ROOT/'backtesting/info01/source_facts.json').read_text())['sources']
 assert [x['source_id']for x in shortlist(s)]==['ECB_SPF_ORIGINAL','FED_SLOOS_ORIGINAL','NYFED_SPD_ORIGINAL']
 assert all(not x['already_tested_equivalent']for x in shortlist(s))
 assert all(not primary_gate(x)[0]for x in s if x['already_tested_equivalent'])
def test_quality_selection_is_invariant_to_invented_outcomes():
 s=json.loads((ROOT/'backtesting/info01/source_facts.json').read_text())['sources']
 before=[x['source_id']for x in shortlist(s)]
 for i,x in enumerate(s):x['future_loss']=-100000*i;x['winning_card']=True
 assert before==[x['source_id']for x in shortlist(s)]
def test_probe_round_bound_publication_cutoff_and_no_faked_hashes():
 p=read('availability_probe.json');samples=p['original_samples']
 assert len(samples)==12
 assert max(sum(x['source_id']==y['source_id']for x in samples)for y in samples)<=3
 assert all(len(x['raw_sha256'])==64 and x['bytes']>0 for x in samples)
 assert all(aware(x['available_at']).date()<=RESEARCH_CUTOFF for x in samples if x['available_at'])
 old=next(x for x in samples if x['round']=='2010Q4')
 assert old['available_at']is None and not old['accepted_for_reconstruction']
 ny=next(x for x in samples if x['round']=='2011December')
 assert aware(ny['available_at']).date().isoformat()=='2012-01-04'
 sloos=next(x for x in samples if x['round']=='2024October')
 assert aware(sloos['available_at']).date().isoformat()=='2024-11-12'
def test_actual_asset_scope_and_independent_universe_not_invented():
 assert read('selected_primary_source.json')['first_experiment_assets']==['EUR']
 assert read('independent_validation_audit.json')['status']=='NOT_AVAILABLE'
 rows=list(csv.DictReader((OUT/'asset_mapping.csv').open()))
 assert all(json.loads(x['eligible_assets'])==[]for x in rows if x['source_id']=='EIA_INVENTORY')
def test_artifact_hashes_match_exact_bytes():
 m=read('artifact_manifest.json')
 for x in m['files']:
  p=ROOT/x['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256']
def test_current_page_incident_is_disclosed_not_used():
 x=read('availability_probe.json')['incidental_current_page_exposure']
 assert x['web_ref']=='turn33view0'and x['new_target_dataset_loaded']is False
 assert all(s['source_id']!='BOARD_H15_TIPS'for s in read('availability_probe.json')['original_samples'])
def test_provider_release_named_column_cannot_backdate_public_availability():
 x=read('availability_probe.json')['NYFED_XLSX_schema_check']
 assert x['provider_survey_release_date']=='2024-09-04'
 assert x['provider_survey_due_date']=='2024-09-09'
 assert x['public_results_available_date']=='2024-10-10'
 assert x['provider_survey_release_date_is_publication']is False
 assert x['availability_field']=='public_results_available_date'
 assert not x['numeric_forecast_panel_constructed']

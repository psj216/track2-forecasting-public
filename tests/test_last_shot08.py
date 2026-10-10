"""Executive summary: frozen-library integrity, PRE firewall and whole-card oracle kill gate.
Router-specific leakage/controls tests become applicable only if the oracle gate passes.
"""
import json,csv,hashlib
from pathlib import Path
import numpy as np
import pytest
from backtesting.last_shot08.core import ROOT,EXPERTS,PARENT,kill_gate,select_whole_card,require_pre
from backtesting.last_shot08.oracle_audit import summarize,concentration
R=ROOT/'backtesting/last_shot08/results'
def read(n):return json.loads((R/n).read_text())
@pytest.mark.parametrize('n',[0,1,2])
def test_minimum_library(n):assert kill_gate(n)=='LIBRARY_TOO_THIN'
@pytest.mark.parametrize('ratio',[.750001,.8,1.,2.])
def test_insufficient_oracle_stops(ratio):assert kill_gate(5,ratio)=='INSUFFICIENT_EXISTING_EXPERT_HEADROOM'
@pytest.mark.parametrize('ratio',[.75,.70,.1])
def test_gate_boundary_fixed(ratio):assert kill_gate(5,ratio)is None
@pytest.mark.parametrize('i',[0,1,2])
def test_full_paired_card_selection(i):
 arrays=[np.arange(2000*6).reshape(2000,2,3)+j for j in range(3)]
 selected=select_whole_card(arrays,i);assert selected is arrays[i] and np.array_equal(selected,arrays[i])
def test_library_precedes_losses():
 s=read('expert_library_spec.json');assert s['selection_before_losses']and s['primary_library']==list(EXPERTS)
def test_immutable_parent():assert read('lineage_manifest.json')['parent_result_sha']==PARENT or read('lineage_manifest.json').get('parent_RESULT_SHA')==PARENT
def test_feature_identity():
 m=read('feature_manifest.json');assert m['exact_inherited_arrays']and not m['new_features']and len(m['columns']['T0'])==36
 assert all(not any(x in name.lower()for x in ['card_id','winner','loss','truth'])for name in m['columns']['T0'])
@pytest.mark.parametrize('e',EXPERTS)
def test_full_card_coverage(e):
 m=read('expert_reproduction_manifest.json');assert len(m['cards'])==24
 assert all(e in c['forecast_hashes']and c['shape'][0]==2000 for c in m['cards'])
def test_no_duplicate_whole_library_identity():
 m=read('expert_reproduction_manifest.json');profiles=[tuple(c['forecast_hashes'][e]for c in m['cards'])for e in EXPERTS]
 assert len(set(profiles))==len(EXPERTS)
def test_non_eligible_models_never_promoted():
 rows=list(csv.DictReader((R/'expert_inventory.csv').open()));assert {r['expert']for r in rows if r['eligible']=='True'}==set(EXPERTS)
def test_pre_receipt_required(tmp_path):
 with pytest.raises(FileNotFoundError):require_pre(tmp_path)
def test_no_forecast_model_or_router_before_gate():
 import inspect,backtesting.last_shot08.core as core
 assert 'sklearn'not in inspect.getsource(core)
def test_conditional_spec_fixed():
 s=read('experiment_spec.json');assert s['model']['alpha']==1 and s['controls']['seed']==31808 and s['bootstrap']['replicates']==5000
 assert s['primary_folds'].startswith('Four family')and s['oracle_kill_if_geometric_composite_greater_than']==.75
@pytest.mark.parametrize('key',['comparative_losses_opened','truth_deserialized'])
def test_pre_freeze_no_outcomes(key):assert read('pre_result_manifest.json')[key]is False
def test_all_oracle_historical_components_exact_when_evaluated():
 p=R/'library_oracle_summary.json'
 if not p.exists():pytest.skip('POST_PRE gate stage not executed yet')
 assert read('expert_reproduction_manifest.json')['verified_card_count']==24
 assert read('library_oracle_summary.json')['whole_card_selection']
def test_stop_artifacts_if_killed():
 p=R/'final_decision.json'
 if not p.exists():pytest.skip('POST_RESULT stage not executed yet')
 d=read('final_decision.json')
 if d['LAST_SHOT08_RESULT']=='INSUFFICIENT_EXISTING_EXPERT_HEADROOM':assert read('primary_router_summary.json')['status']=='NOT_RUN_KILL_GATE'

"""Executive summary: source schemas and exact parent/main protection declarations."""
import json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'backtesting/location02/results'


def test_source_schema_ready_and_parent():
    manifest=json.loads((OUT/'ecb_dataset_readiness.json').read_text())
    assert manifest['DATASET_READY'] and not manifest['critical_failures']
    spec=json.loads((OUT/'experiment_spec.json').read_text())
    assert spec['parent_result_sha']=='43a154ab419b6f3e3f4fc903db40d8c2e319f6bf'
    assert spec['asset']=='EUR' and spec['alpha']==1.0 and spec['source_age_max_business_days']==90
    fields=pd.read_csv(OUT/'ecb_field_ledger.csv')
    assert set(['round_id','variable','target_calendar_year','point_forecast','source_sha256']).issubset(fields.columns)
    assert fields.groupby(['round_id','variable','target_calendar_year']).size().eq(1).all()
    assert set(fields.variable)=={'HICP','GDP'}


def test_pre_and_main_protection():
    env=json.loads((OUT/'environment_audit.json').read_text())
    assert env['main_unchanged_at_start'] and env['main_before']=='e1b5cf3b3a87966e902332ef3cc5c0ed2dbffee8'
    pre=json.loads((OUT/'pre_result_manifest.json').read_text())
    assert pre['Gate_A_passed'] and not pre['outcomes_loaded'] and pre['fits']==0
    assert pre['original_ledger_sha256']=='5a421fa5c10745c69469c683797bf42f4abf54288e8082984bcf39fda76968a6'

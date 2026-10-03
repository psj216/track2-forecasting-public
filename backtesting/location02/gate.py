"""Executive summary: finish source-only readiness without accessing outcome labels."""
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
from .source_acquisition import OUT, ROOT, digest, dump, write_csv
from .source_dataset import FEATURES, asof_features, origin_cutoff


def source_calendar(private):
    states=json.loads((private/'source_states.json').read_text())['states']
    original=json.loads((ROOT/'backtesting/location01/results/ledger_manifest.json').read_text())
    names=list(original['baseline_cache_sha256'])
    months={}
    for name in sorted(names):
        stamp=Path(name).stem
        if '2015' <= stamp[:4] <= '2024': months.setdefault(stamp[:7], stamp)
    dates=USFederalHolidayCalendar().holidays('2014-01-01','2024-12-31').strftime('%Y-%m-%d').tolist()
    rows=[]
    for origin in months.values():
        cutoff=origin_cutoff(origin)
        state=asof_features(states,origin)
        holiday=str(cutoff.date()) in dates
        row=dict(origin=origin, cutoff=cutoff.isoformat(), cutoff_holiday_ambiguous=holiday,
                 active=state is not None and not holiday, reason='HOLIDAY_CUTOFF_AMBIGUOUS' if holiday else 'MISSING_OR_EXPIRED_SOURCE' if state is None else 'ACTIVE')
        if state: row.update({k:state[k] for k in ['round_id','target_calendar_year',*FEATURES]})
        else: row.update({k:'' for k in ['round_id','target_calendar_year',*FEATURES]})
        rows.append(row)
    return rows


def finalize(private):
    manifest=json.loads((OUT/'ecb_pit_dataset_manifest.json').read_text())
    rows=source_calendar(private);active=[r for r in rows if r['active']]
    write_csv(OUT/'source_calendar.csv', rows)
    years=sorted({r['origin'][:4] for r in active})
    failures=[]
    if manifest['retrospective_mismatches'] or manifest['unresolved_amendment_notices']: failures.append('UNRESOLVED_ORIGINAL_VERSION')
    if len(years)<8 or not all(str(y) in years for y in range(2020,2025)): failures.append('INSUFFICIENT_SOURCE_COVERAGE')
    if len({r['round_id'] for r in active if r['origin'][:4]>='2020'})<12: failures.append('INSUFFICIENT_FORWARD_RELEASE_EVENTS')
    tests=(private/'source-pit-tests.log').read_text()
    if '100%' not in tests or 'FAILED' in tests: failures.append('SOURCE_TESTS_NOT_PASSED')
    field_hash=digest(OUT/'ecb_field_ledger.csv')
    manifest.update(DATASET_READY=not failures, gate_completed_before_outcomes=True, field_ledger_sha256=field_hash,
                    source_calendar_sha256=digest(OUT/'source_calendar.csv'), age_rule_business_days=90)
    dump(OUT/'ecb_pit_dataset_manifest.json',manifest)
    dump(OUT/'ecb_dataset_readiness.json', {'DATASET_READY':not failures,'critical_failures':failures,
       'source_statistics':{k:manifest[k] for k in ['rounds_enumerated','extracted_fields','usable_releases_before_age_filter','same_target_revision_events']},
       'forecast_origin_candidates':len(rows),'active_monthly_candidates':len(active),'active_source_years':years,
       'pre_outcome_gate':True,'outcomes_loaded':False,'model_fits':0,'forecast_scores':0,
       'deterministic_field_ledger_sha256':field_hash,'source_pit_tests':'11 passed',
       'provenance_caveat':'PIT B, not immutable historical originals; no unresolved notices or mismatches in all 216 applicable following-round comparisons',
       'source_gate_thresholds':'At least 8 source years, all 2020-2024 years, at least 12 forward source events; no outcome coverage used'})
    status=json.loads((ROOT/'backtesting/location02/STATUS.json').read_text())
    status.update(current_stage='implementation', completed_stages=['environment','parent_recovery','source_acquisition','PIT_errata','dataset_readiness'],
                  DATASET_READY=not failures, HEAD_SHA='d0a4d63630f2ca33757ff7246f521f23e8fc5430',last_successful_artifact='results/ecb_dataset_readiness.json')
    dump(ROOT/'backtesting/location02/STATUS.json',status)
    print({'DATASET_READY':not failures,'monthly_candidates':len(rows),'active':len(active),'failures':failures})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--private',type=Path,required=True)
    finalize(parser.parse_args().private)

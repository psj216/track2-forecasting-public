"""Executive summary: pre-outcome publication, rollover, expiry and rebuild guards."""
import copy
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from backtesting.location02.source_dataset import (activation, asof_features, origin_cutoff,
    release_states, same_target_revision, parse_table)


def sample_states():
    universe = [dict(round_id='2023Q4', year=2023, publication_date='2023-10-27'),
                dict(round_id='2024Q1', year=2024, publication_date='2024-01-26')]
    fields = [dict(round_id=r, variable=v, target_calendar_year=y, point_forecast=x)
       for r, values in [('2023Q4', [(2023,2.), (2024,3.), (2025,4.)]),
                         ('2024Q1', [(2024,3.5), (2025,5.), (2026,6.)])]
       for v in ('HICP', 'GDP') for y,x in values]
    return release_states(universe, fields)


def test_same_target_rollover():
    states=sample_states()
    assert states[1]['HICP_NCY_REV_SAME_TARGET'] == 1.0  # 2025 minus 2025, never 2024
    assert not states[0]['eligible']
    assert same_target_revision({('HICP',2025):4}, {('HICP',2024):3}, 'HICP',2025) is None


def test_publication_cutoff_and_no_future_activation():
    states=sample_states()
    assert asof_features(states, '2024-01-29') is None  # Friday NY16 precedes Berlin EOD
    assert asof_features(states, '2024-01-30')['round_id'] == '2024Q1'
    assert activation('2024-01-26') > origin_cutoff('2024-01-29').tz_convert('UTC')


def test_age_90_exact_and_expiry():
    state=sample_states()[1]
    release=pd.Timestamp(state['publication_date'])
    for days in (90,91):
        origin=release+pd.offsets.BDay(days+1)
        observed=asof_features([state],origin)
        assert (observed is not None)==(days==90)


def test_future_mutation_bitwise_and_determinism():
    states=sample_states(); cutoff='2024-01-30'
    before=json.dumps(asof_features(states,cutoff),sort_keys=True)
    future=copy.deepcopy(states[-1]);future.update(round_id='2024Q2',available_at=activation('2024-04-12').isoformat(),HICP_NCY=999.)
    assert json.dumps(asof_features(states+[future],cutoff),sort_keys=True)==before
    assert sample_states()==sample_states()


def test_later_erratum_is_distinct_event():
    states=sample_states(); old=copy.deepcopy(states[-1])
    correction=copy.deepcopy(old);correction.update(available_at=activation('2024-02-12').isoformat(),HICP_NCY=99.)
    assert asof_features(states+[correction],'2024-02-01')['HICP_NCY']==old['HICP_NCY']
    assert asof_features(states+[correction],'2024-02-14')['HICP_NCY']==99.


def test_explicit_year_table_not_core():
    text='''2019 2020 2021 Longer term
HICP inflation
Q1 2019 SPF 1.5 1.6 1.7 1.8
Previous SPF (Q4 2018) 1.7 1.7 - 1.9
Memo: HICP inflation excluding energy
Q1 2019 SPF 8.0 8.0 8.0 8.0
Real GDP growth
Q1 2019 SPF 1.5 1.5 1.4 1.5
Previous SPF (Q4 2018) 1.8 1.6 - 1.6
'''
    fields=parse_table(text,'2019Q1')
    assert len(fields)==6
    assert [r['point_forecast'] for r in fields if r['variable']=='HICP']==[1.5,1.6,1.7]
    with pytest.raises(ValueError): parse_table(text.replace('2019 2020 2021','2019 2021 2022'),'2019Q1')


def test_outcome_mutation_not_source_features():
    states=sample_states(); first=asof_features(states,'2024-02-01')
    outcomes=np.arange(100.);outcomes[:]=999.
    assert first==asof_features(states,'2024-02-01')

"""Executive summary: fail-closed operational gates, with no Docker or forecasting calls."""
import json
from pathlib import Path
import pytest
from backtesting.v51_delivery_emergency11 import runner as r


def test_exact_frozen_identity():
    assert r.SPEC['source_SHA'] == '47194f28d5188b87cdca1d591d86b9eeda86f7cf'
    assert r.IMAGE == 'docker.io/jotj216/track2-f4-approved@sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874'
    assert r.SPEC['common_version'] == '2.4.2'
    assert r.SPEC['parent_RESULT_SHA'] == 'd37c1a922b9dac750309e41e1569851bf7060db2'
    assert not r.SPEC['rebuild_allowed'] and not r.SPEC['scores_allowed']


def test_branch_push_only_and_read_only():
    s = (r.ROOT / '.github/workflows/v51-delivery-emergency11.yml').read_text()
    assert 'workflow_dispatch' not in s and 'pull_request:' not in s
    assert 'track2/v51-delivery-emergency-11' in s
    assert 'contents: read' in s
    for forbidden in ['contents: write', 'packages: write', 'id-token:', 'secrets.', 'docker login', 'docker build', 'docker push']:
        assert forbidden not in s
    assert 'persist-credentials: false' in s


def test_permanent_pull_no_retry(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(r, 'WORK', tmp_path)
    monkeypatch.setattr(r, 'save', lambda *x: None)
    def command(args, *unused):
        calls.append(args)
        return {'exit_code': 1, 'stderr': 'manifest unknown'}
    monkeypatch.setattr(r, 'command', command)
    assert r.pull() is False
    assert calls == [['docker', 'pull', r.IMAGE]]


def test_transient_pull_one_retry(monkeypatch, tmp_path):
    codes = iter([{'exit_code': 1, 'stderr': 'connection reset'}, {'exit_code': 0, 'stderr': ''}])
    monkeypatch.setattr(r, 'WORK', tmp_path)
    monkeypatch.setattr(r, 'save', lambda *x: None)
    monkeypatch.setattr(r, 'command', lambda *x: next(codes))
    assert r.pull() is True
    with pytest.raises(StopIteration):
        next(codes)


def test_pull_error_classification():
    assert r.pull_failure('unauthorized: authentication required') == 'AUTH_REQUIRED'
    assert r.pull_failure('manifest unknown') == 'MANIFEST_UNKNOWN'
    assert r.pull_failure('no matching manifest for linux/amd64') == 'ARCHITECTURE_UNAVAILABLE'
    assert r.pull_failure('503 service unavailable') == 'NETWORK_FAILURE'


def test_inspect_digest_fail_closed(monkeypatch):
    fake = {'RepoDigests': ['repo@sha256:wrong'], 'Os': 'linux', 'Architecture': 'amd64', 'Config': {'User': 'runner'}}
    monkeypatch.setattr(r, 'save', lambda *x: None)
    monkeypatch.setattr(r, 'command', lambda *x: {'exit_code': 0, 'stdout': json.dumps([fake])})
    with pytest.raises(AssertionError, match='digest mismatch'):
        r.inspect_image()


def _repeats(changed=False, serialization=False):
    return [{'unit': name, 'mode': 'text-first-v5.1', 'repetition': i,
             'numeric_array_SHA256': 'same' if not changed or i != 3 else 'different',
             'draw_order_SHA256': 'same', 'normalized_meta_SHA256': 'same',
             'hashes': {'forecast.parquet': str(i) if serialization else 'same', 'forecast_rationale.md': 'same'}}
            for name in r.SPEC['representatives'] for i in (1,2,3)]


def test_numerical_difference_blocks(monkeypatch):
    monkeypatch.setattr(r, 'save', lambda *x: None)
    with pytest.raises(AssertionError, match='NONDETERMINISTIC_FORECAST'):
        r.determinism(_repeats(changed=True))


def test_serialization_difference_separate(monkeypatch):
    monkeypatch.setattr(r, 'save', lambda *x: None)
    d = r.determinism(_repeats(serialization=True))
    assert d['pass'] and all(not x['parquet_byte_identical'] for x in d['units'])


def test_all_four_families_three_repeats_frozen():
    assert len(r.SPEC['units']) == 5
    assert len(r.SPEC['representatives']) == 4
    assert {name.split('-')[1] for name in r.SPEC['representatives']} == {'F1','F2','F3','F4'}
    assert r.SPEC['required_repetitions'] == 3


def test_no_score_or_candidate_build_calls():
    code = Path(r.__file__).read_text()
    for forbidden in ['build_verifier(', '_score(', 'qfbench2-smoke', "'docker', 'build'", "'docker', 'push'", "'docker', 'login'"]:
        assert forbidden not in code
    assert 'array.tobytes()' in code


def test_secret_redaction():
    token = 'ghp_' + 'A' * 40
    assert token not in r.SECRET.sub('[REDACTED]', token)


def test_precedes_trigger():
    pre = json.loads((r.ROOT / 'backtesting/v51_delivery_emergency11/results/pre_result_manifest.json').read_text())
    assert pre['Docker_results_exist'] is False
    assert pre['parent_SHA'] == 'd37c1a922b9dac750309e41e1569851bf7060db2'

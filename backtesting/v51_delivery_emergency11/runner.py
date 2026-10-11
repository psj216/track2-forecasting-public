"""Validate the frozen image on a Docker runner without fitting, scoring or submission.

Executive summary: anonymous digest pull precedes inspection and isolated fixture runs.
Evidence is incremental and fail closed; no image build, login, push or score is invoked.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import time
import tomllib

ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / 'backtesting/v51_delivery_emergency11/results/delivery_spec.json'
SPEC = json.loads(SPEC_PATH.read_text())
IMAGE = SPEC['image_reference']
EVIDENCE = Path(os.environ.get('EM11_EVIDENCE', str(ROOT / 'emergency11-evidence'))).resolve()
WORK = Path(os.environ.get('RUNNER_TEMP', '/tmp')) / 'emergency11-work'
SECRET = re.compile(r'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name: str, obj: object) -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    p = EVIDENCE / name
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')
    tmp.replace(p)


def command(args: list[str], log: str, timeout: int = 600) -> dict:
    start = time.monotonic()
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        code, stdout, stderr = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as exc:
        code, stdout, stderr = 124, '', 'Execution timeout'
        if exc.stdout:
            stdout = exc.stdout.decode(errors='replace') if isinstance(exc.stdout, bytes) else exc.stdout
    result = {'command': args, 'exit_code': code, 'wall_seconds': time.monotonic() - start,
              'stdout': SECRET.sub('[REDACTED]', stdout), 'stderr': SECRET.sub('[REDACTED]', stderr)}
    save('logs/' + log + '.json', result)
    return result


def pull_failure(text: str) -> str:
    s = text.lower()
    if any(x in s for x in ('unauthorized', 'authentication required', 'denied:')):
        return 'AUTH_REQUIRED'
    if 'manifest unknown' in s:
        return 'MANIFEST_UNKNOWN'
    if 'no matching manifest' in s:
        return 'ARCHITECTURE_UNAVAILABLE'
    if 'not found' in s:
        return 'REGISTRY_NOT_FOUND'
    if any(x in s for x in ('timeout', 'timed out', 'connection reset', 'temporary failure', '503', '502')):
        return 'NETWORK_FAILURE'
    return 'OTHER'


def pull() -> bool:
    anonymous = WORK / 'anonymous-docker-config'
    anonymous.mkdir(parents=True, exist_ok=True)
    os.environ['DOCKER_CONFIG'] = str(anonymous)
    attempts = []
    for n in range(2):
        r = command(['docker', 'pull', IMAGE], f'pull-{n + 1}')
        r['failure_category'] = None if r['exit_code'] == 0 else pull_failure(r['stderr'])
        attempts.append(r)
        save('pull-result.json', {'image': IMAGE, 'anonymous': True, 'attempts': attempts,
                                'EXACT_PREPARATION_IMAGE_RECOVERED': r['exit_code'] == 0})
        if r['exit_code'] == 0:
            return True
        if r['failure_category'] != 'NETWORK_FAILURE':
            break
    return False


def inspect_image() -> dict:
    r = command(['docker', 'image', 'inspect', IMAGE], 'image-inspect')
    assert r['exit_code'] == 0, 'docker image inspect failed'
    image = json.loads(r['stdout'])[0]
    save('image-inspect.json', image)
    digest = IMAGE.split('@')[1]
    assert any(x.split('@')[-1] == digest for x in image.get('RepoDigests', [])), 'digest mismatch'
    assert (image['Os'], image['Architecture']) == ('linux', 'amd64'), 'platform mismatch'
    assert image['Config'].get('User') not in ('', '0', 'root', '0:0'), 'root image user'
    return image


def source_dependencies() -> dict:
    script = '''import hashlib, pathlib, json, sys, importlib.metadata as m
import qfbench2_common, qfbench2_track_forecasting
p=pathlib.Path(qfbench2_track_forecasting.__file__).parent
files={str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file() and '__pycache__' not in f.parts}
print(json.dumps({'python':sys.version.split()[0], 'versions':{k:m.version(k) for k in ['qfbench2-common','numpy','pandas','pyarrow','jsonschema']},'package_files':files,'common_file':qfbench2_common.__file__,'package_file':str(p)}))'''
    r = command(['docker', 'run', '--rm', '--network=none', '--read-only', '--tmpfs', '/tmp', IMAGE,
                 'python3', '-c', script], 'dependency-source-identity')
    assert r['exit_code'] == 0, 'dependency/source inspection failed'
    d = json.loads(r['stdout'])
    assert d['python'].startswith('3.13.'), 'Python version mismatch'
    expected = {'qfbench2-common': '2.4.2', 'numpy': '2.1.3', 'pandas': '2.2.3',
                'pyarrow': '18.1.0', 'jsonschema': '4.23.0'}
    assert d['versions'] == expected, 'dependency mismatch'
    source = ROOT / 'preparation-source/qfbench2_track_forecasting'
    local = {str(f.relative_to(source)): sha(f) for f in source.rglob('*')
             if f.is_file() and '__pycache__' not in f.parts}
    d['source_SHA'] = SPEC['source_SHA']
    d['source_files_match'] = local == d['package_files']
    save('source-identity.json', d)
    assert local and d['source_files_match'], 'exact source package hashes differ'
    return d


def security(image: dict) -> dict:
    config = image['Config']
    hits = []
    for v in config.get('Env', []):
        name = v.split('=', 1)[0].upper()
        if name.endswith(('TOKEN', 'PASSWORD', 'SECRET', 'API_KEY')) or SECRET.search(v):
            hits.append({'kind': 'environment', 'field': name})
    create = command(['docker', 'create', IMAGE], 'security-create')
    assert create['exit_code'] == 0
    cid = create['stdout'].strip()
    archive = WORK / 'filesystem.tar'
    try:
        exported = command(['docker', 'export', '--output', str(archive), cid], 'security-export')
        assert exported['exit_code'] == 0, 'filesystem security inventory unavailable'
        count = scanned = 0
        with tarfile.open(archive) as tf:
            for member in tf:
                count += 1
                n = member.name.lstrip('./')
                application = n.startswith(('opt/', 'work/', 'home/', 'root/'))
                suspicious = application and (Path(n).name in ('.env', 'id_rsa', 'id_ed25519')
                    or '/.docker/config.json' in n or '/.ssh/' in n
                    or any(x in n.lower() for x in ('hidden_labels', 'private_truth', 'private-recovery', 'realized.parquet')))
                if suspicious:
                    hits.append({'kind': 'path', 'path': n})
                if member.isfile() and application and 0 < member.size <= 2 * 1024 * 1024:
                    f = tf.extractfile(member)
                    if f:
                        raw = f.read(); scanned += 1
                        if SECRET.search(raw.decode('utf-8', errors='ignore')):
                            hits.append({'kind': 'secret_signature', 'path': n})
        d = {'pass': not hits, 'hits': hits, 'inventory_members': count, 'content_files_scanned': scanned,
             'scope': 'full filesystem path inventory; bounded app/work/home/root contents + metadata',
             'limitations': 'pattern inspection is not a proof against every possible secret encoding'}
        save('security-summary.json', d)
        assert d['pass'], 'security inspection failed'
        return d
    finally:
        command(['docker', 'rm', cid], 'security-remove')
        archive.unlink(missing_ok=True)


def validate_output(out: Path, unit: Path, asof: str) -> dict:
    import jsonschema
    import numpy as np
    import pyarrow.parquet as pq
    from qfbench2_common.taskcard import load_schema
    from qfbench2_track_forecasting.grid import grid_from_card, check_declared_grid, build_sample_matrix
    from qfbench2_track_forecasting.limits import DEFAULT_LIMITS, inspect_parquet
    from qfbench2_track_forecasting.cutoff import bind_metadata, scan_text_corpus_cutoff
    card = tomllib.loads((unit / 'card.toml').read_text())
    meta = json.loads((out / 'forecast_meta.json').read_text())
    jsonschema.validate(meta, load_schema('forecast.schema.json'))
    spec = grid_from_card(card)
    check_declared_grid(meta, spec)
    bind_metadata(meta, card, unit_handle=unit.name)
    facts = inspect_parquet(out / 'forecast.parquet', what='forecast.parquet', limits=DEFAULT_LIMITS)
    array = build_sample_matrix(out / 'forecast.parquet', facts, spec, meta['n_draws'], limits=DEFAULT_LIMITS)
    assert np.isfinite(array).all()
    panel_max = {}
    for p in unit.glob('*.parquet'):
        table = pq.read_table(p, columns=['date'])
        dates = [str(x)[:10] for x in table.column('date').to_pylist() if x is not None]
        assert dates and max(dates) <= asof, 'future panel data'
        panel_max[p.name] = max(dates)
    assert panel_max, 'no fixture panels'
    scan_text_corpus_cutoff(unit / 'text', asof)
    t = pq.read_table(out / 'forecast.parquet')
    order = {'draw': t['draw'].to_pylist(), 'asset': t['asset'].to_pylist(), 'horizon': t['horizon'].to_pylist()}
    rationale = out / 'forecast_rationale.md'
    hashes = {p.name: sha(p) for p in (out / 'forecast.parquet', out / 'forecast_meta.json', rationale) if p.is_file()}
    return {'schema_pass': True, 'asof': asof, 'assets': list(spec.assets), 'horizons': list(spec.horizons),
            'shape': list(array.shape), 'n_draws': meta['n_draws'], 'finite': True, 'input_cutoff_pass': True,
            'panel_latest_dates': panel_max, 'rationale_present_nonempty': rationale.is_file() and rationale.stat().st_size > 0,
            'hashes': hashes, 'numeric_array_SHA256': hashlib.sha256(array.tobytes()).hexdigest(),
            'draw_order_SHA256': hashlib.sha256(json.dumps(order, separators=(',', ':')).encode()).hexdigest(),
            'normalized_meta_SHA256': hashlib.sha256(json.dumps(meta, sort_keys=True, separators=(',', ':')).encode()).hexdigest()}


def run_unit(name: str, mode: str, repetition: int) -> dict:
    unit = ROOT / 'units' / name
    card = tomllib.loads((unit / 'card.toml').read_text())
    asof = card['provenance']['data_cutoff']
    out = WORK / 'outputs' / name / mode / str(repetition)
    out.mkdir(parents=True, exist_ok=False)
    out.chmod(0o777)
    cidfile = WORK / f'{name}-{mode}-{repetition}.cid'
    args = ['docker', 'run', '--cidfile', str(cidfile), '--network=none', '--read-only',
            '--tmpfs', SPEC['resource_limits']['tmpfs'], '--cpus=2', '--memory=8g', '--pids-limit=256',
            '-e', 'FORECAST_MODE=' + mode, '-v', str(unit) + ':/input:ro', '-v', str(out) + ':/output',
            IMAGE, 'forecast', '--panels', '/input', '--text', '/input/text', '--asof', asof,
            '--out', '/output/forecast.parquet']
    r = command(args, f'run-{name}-{mode}-{repetition}', SPEC['resource_limits']['timeout_seconds_per_container'])
    d = {'unit': name, 'mode': mode, 'repetition': repetition, 'exit_code': r['exit_code'],
         'wall_seconds': r['wall_seconds'], 'output_bytes': sum(p.stat().st_size for p in out.iterdir() if p.is_file()),
         'peak_memory_bytes': None, 'peak_memory_note': 'not sampled; memory limited to 8GiB', 'out': str(out)}
    if cidfile.exists():
        cid = cidfile.read_text().strip()
        command(['docker', 'inspect', cid], f'container-{name}-{mode}-{repetition}')
        command(['docker', 'rm', '-f', cid], f'remove-{name}-{mode}-{repetition}')
    if r['exit_code'] == 0:
        d.update(validate_output(out, unit, asof))
    save(f'unit-receipts/{name}-{mode}-{repetition}.json', d)
    assert r['exit_code'] == 0, 'runtime failed: ' + name
    return d


def routes(runs: list[dict]) -> dict:
    records = []
    for name in SPEC['units']:
        rows = [x for x in runs if x['unit'] == name and x['repetition'] == 1]
        base = next(x for x in rows if x['mode'] == 'numeric')
        text = next(x for x in rows if x['mode'] == 'text-first-v5.1')
        meta = json.loads((Path(text['out']) / 'forecast_meta.json').read_text())
        equal = base['hashes']['forecast.parquet'] == text['hashes']['forecast.parquet']
        active = '-F1-' in name or '-F4-' in name
        passed = equal if not active else not equal and bool(meta.get('reasoning_applied')) and bool(meta.get('forecast_adjustment_applied'))
        ev = meta.get('rationale', {}).get('text_evidence', {})
        if active:
            passed = passed and ev.get('currentness') in (['DOCUMENT_DELTA'] if '-F1-' in name else ['CURRENT', 'FORWARD'])
            passed = passed and bool(ev.get('last_world_date')) and ev['last_world_date'] <= text['asof']
            passed = passed and bool(ev.get('evidence_ids')) and bool(ev.get('evidence_excerpt')) and bool(ev.get('directions'))
            passed = passed and 0 < ev.get('sleeve_fraction', 0) <= 0.20
            if '-F4-' in name:
                passed = passed and meta['n_draws'] >= 1000
        records.append({'unit': name, 'expected_active': active, 'numeric_text_byte_identical': equal,
                        'pass': bool(passed), 'evidence': ev})
    d = {'pass': all(x['pass'] for x in records), 'units': records}
    save('route-invariants.json', d)
    assert d['pass'], 'historical route invariant failed'
    return d


def determinism(runs: list[dict]) -> dict:
    records = []
    for name in SPEC['representatives']:
        rows = [x for x in runs if x['unit'] == name and x['mode'] == 'text-first-v5.1']
        assert len(rows) == 3, 'missing repeat'
        numeric = len({x['numeric_array_SHA256'] for x in rows}) == 1
        order = len({x['draw_order_SHA256'] for x in rows}) == 1
        byte = len({x['hashes']['forecast.parquet'] for x in rows}) == 1
        meta = len({x['normalized_meta_SHA256'] for x in rows}) == 1
        rationale = len({x['hashes'].get('forecast_rationale.md') for x in rows}) == 1
        records.append({'unit': name, 'numeric_bitwise_identical': numeric, 'draw_order_identical': order,
                        'parquet_byte_identical': byte, 'normalized_meta_identical': meta,
                        'rationale_identical': rationale, 'hashes': [x['hashes'] for x in rows],
                        'numeric_hashes': [x['numeric_array_SHA256'] for x in rows]})
    d = {'pass': all(x['numeric_bitwise_identical'] and x['draw_order_identical'] for x in records), 'units': records}
    save('determinism.json', d)
    assert d['pass'], 'NONDETERMINISTIC_FORECAST'
    return d


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    receipt = {'GITHUB_SHA': os.environ.get('GITHUB_SHA'), 'run_id': os.environ.get('GITHUB_RUN_ID'),
               'runner_OS': os.environ.get('RUNNER_OS'), 'source_SHA': SPEC['source_SHA'], 'image': IMAGE}
    save('runner-receipt.json', receipt)
    verdict, stage, runs = 'INCONCLUSIVE', 'pull', []
    try:
        if not pull():
            verdict = 'SAFE_DELIVERY_BLOCKED_IMAGE_UNAVAILABLE'
            return 1
        stage = 'image/source identity'
        image = inspect_image()
        source_dependencies()
        stage = 'security'
        security(image)
        stage = 'runtime/schema'
        for name in SPEC['units']:
            for mode in ['numeric', 'text-first-v5.1']:
                print(f'stage=runtime completed={len(runs)}/18 elapsed={time.monotonic()-start:.1f} unit={name} mode={mode} output={EVIDENCE}', flush=True)
                runs.append(run_unit(name, mode, 1))
                save('runtime-matrix.json', runs)
        stage = 'route invariants'
        routes(runs)
        stage = 'runtime/schema'
        for name in SPEC['representatives']:
            for repetition in (2, 3):
                print(f'stage=repeat completed={len(runs)}/18 elapsed={time.monotonic()-start:.1f} unit={name} repeat={repetition} output={EVIDENCE}', flush=True)
                runs.append(run_unit(name, 'text-first-v5.1', repetition))
                save('runtime-matrix.json', runs)
        stage = 'determinism'
        determinism(runs)
        stage = 'resources'
        resource_pass = all(x['wall_seconds'] < 600 and x['output_bytes'] < 64*1024*1024 for x in runs)
        save('resource-summary.json', {'pass': resource_pass, 'image_size_bytes': image.get('Size'),
             'limits': SPEC['resource_limits'], 'units': [{k: x[k] for k in ('unit','mode','repetition','wall_seconds','exit_code','output_bytes','peak_memory_bytes')} for x in runs]})
        assert resource_pass, 'resource gate failed'
        save('output-hashes.json', [{k: x[k] for k in ('unit','mode','repetition','hashes','numeric_array_SHA256','draw_order_SHA256')} for x in runs])
        stage = 'current contract'
        config = image['Config']
        image_contract = not config.get('Volumes') and config.get('Labels', {}).get('qfbench2.interface_version') == '2.0'
        sidecars = all(x['rationale_present_nonempty'] for x in runs)
        save('current-contract.json', {'interface_label_pass': image_contract, 'rationale_pass': sidecars,
                                     'core_valid': True, 'no_volumes': not bool(config.get('Volumes')),
                                     'descriptor_team_identity_not_invented': True})
        verdict = 'SAFE_CANDIDATE_READY_EXACT_IMAGE' if image_contract and sidecars else 'FORECAST_CORE_VALID_CURRENT_CONTRACT_GAP'
        return 0
    except Exception as exc:
        mapping = {'security': 'SAFE_DELIVERY_BLOCKED_SECURITY', 'route invariants': 'SAFE_DELIVERY_BLOCKED_RUNTIME',
                   'determinism': 'SAFE_DELIVERY_BLOCKED_NONDETERMINISM', 'resources': 'SAFE_DELIVERY_BLOCKED_RESOURCES'}
        if stage == 'runtime/schema':
            verdict = 'SAFE_DELIVERY_BLOCKED_RUNTIME' if 'runtime failed:' in str(exc) else 'SAFE_DELIVERY_BLOCKED_SCHEMA'
        else:
            verdict = mapping.get(stage, 'INCONCLUSIVE')
        save('failure.json', {'stage': stage, 'exception_type': type(exc).__name__, 'reason': SECRET.sub('[REDACTED]', str(exc))})
        return 1
    finally:
        receipt.update({'verdict': verdict, 'last_stage': stage, 'completed_runs': len(runs),
                        'elapsed_seconds': time.monotonic()-start, 'new_score': False, 'submission': False,
                        'rebuilt': False, 'forecast_code_changed': False})
        save('final-receipt.json', receipt)
        for name in ('image-inspect.json','runtime-matrix.json','route-invariants.json','determinism.json','security-summary.json','resource-summary.json','output-hashes.json'):
            if not (EVIDENCE/name).exists():
                save(name, {'status': 'NOT_EXECUTED', 'reason': 'stopped at ' + stage})
        print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    sys.exit(main())

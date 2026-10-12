"""## Executive summary (read this first)
Exercise A-E against synthetic local proxy/House responses, never live services.
Persist per-case receipts and compare the unchanged frozen forecast semantics.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import select
import socket
import ssl
import subprocess
import threading
import time
import tomllib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import pandas as pd
import pytest

from backtesting.moonshot15.runtime.synthetic import reply
from moonshot15_engine import cli, engine, official_transport as transport

ROOT = Path(__file__).parents[1]
CTX = {'card': {'assets': ['UST_2Y', 'EUR'], 'horizons': [5, 63]}}
PROXY_AUTH = 'Basic ' + base64.b64encode(b'synthetic-user:synthetic-pass').decode()
TOKEN = 'synthetic-house-token'
CASES = {
    'normal': None, 'uppercase_only': None, 'lowercase_only': None,
    'both_equal': None, 'both_conflicting': 'proxy_configuration_conflict',
    'https_proxy_only': None, 'http_endpoint': None, 'https_endpoint': None,
    'endpoint_missing': 'endpoint_missing', 'token_missing': 'token_missing',
    'model_missing': 'model_name_missing', 'proxy_missing': 'proxy_missing',
    'invalid_proxy_credentials': 'proxy_credentials_invalid',
    'proxy_auth_failure': 'proxy_authentication_failure',
    'http_401': 'http_401', 'http_403': 'http_403', 'http_429': 'http_429',
    'http_503': 'http_503', 'timeout': 'timeout',
    'malformed_outer': 'malformed_outer_json', 'malformed_json': 'malformed_model_content',
    'code_fence': 'code_fenced_json', 'duplicate_model_keys': 'duplicate_model_json_keys',
    'duplicate_outer_keys': 'duplicate_outer_json_keys', 'schema_mismatch': 'schema_rejection',
    'length': 'response_incomplete', 'socket_truncation': 'response_incomplete',
    'malformed_envelope': 'malformed_response', 'response_too_large': 'response_too_large',
    'redirect': 'redirect_rejected', 'normal_adjustment': None,
    'https_proxy_scheme': 'proxy_configuration_invalid', 'tls_invalid': 'tls_validation_failure',
}


class MockState:
    def reset(self, variant, case):
        self.variant, self.case, self.calls, self.connects = variant, case, 0, 0
        self.origin_proxy_header_seen = False
        self.contract_ok = True

    def response(self, request):
        self.calls += 1
        assert request['model'] == 'synthetic-model'
        assert request['max_tokens'] == 4000 and request['temperature'] == 0
        assert request['chat_template_kwargs'] == {'enable_thinking': False}
        context = json.loads(request['messages'][0]['content'].split('\nCONTEXT_JSON\n', 1)[1])
        kind = ('E1' if self.calls == 1 else 'E2') if self.variant == 'E' else self.variant
        content = json.dumps(reply(kind, context))
        status, finish = 200, 'stop'
        if self.case.startswith('http_') and self.case != 'http_endpoint':
            status = int(self.case.split('_')[1])
        if self.case == 'second_call_error' and self.calls == 2:
            status = 503
        if self.case == 'redirect':
            status = 307
        if self.case == 'timeout':
            time.sleep(0.4)  # test-only deadline injection; production constant stays 60
        if self.case == 'malformed_json':
            content = 'synthetic malformed model content'
        elif self.case == 'code_fence':
            content = '```json\n' + content + '\n```'
        elif self.case == 'duplicate_model_keys':
            content = '{"x":1,"x":2}'
        elif self.case == 'schema_mismatch':
            obj = json.loads(content)
            obj['unexpected'] = True
            content = json.dumps(obj)
        elif self.case == 'length':
            finish = 'length'
        raw = json.dumps({'choices': [{'finish_reason': finish,
                                      'message': {'content': content}}]}).encode()
        if self.case == 'malformed_outer':
            raw = b'{incomplete outer JSON'
        elif self.case == 'duplicate_outer_keys':
            raw = b'{"choices":[],"choices":[]}'
        elif self.case == 'malformed_envelope':
            raw = b'{"wrong":true}'
        elif self.case == 'response_too_large':
            raw = b' ' * (transport._RESPONSE_BYTES + 2)
        return status, raw


@pytest.fixture(scope='module')
def mock_route(tmp_path_factory):
    state = MockState()
    state.reset('A', 'normal')
    certdir = tmp_path_factory.mktemp('synthetic_tls')
    cert, key = certdir / 'cert.pem', certdir / 'key.pem'
    subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                    '-keyout', str(key), '-out', str(cert), '-days', '1',
                    '-subj', '/CN=house.mock', '-addext', 'subjectAltName=DNS:house.mock'],
                   check=True, capture_output=True, timeout=15)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            proxy_mode = self.server is proxy
            if proxy_mode and self.headers.get('Proxy-Authorization') != PROXY_AUTH:
                self.send_error(407)
                return
            if self.headers.get('Authorization') != 'Bearer ' + TOKEN:
                self.send_error(401)
                return
            wanted = ('http://house.mock:8000/v1/chat/completions' if proxy_mode
                      else '/v1/chat/completions')
            state.contract_ok &= self.path == wanted
            if not proxy_mode:
                state.origin_proxy_header_seen |= 'Proxy-Authorization' in self.headers
            body = self.rfile.read(int(self.headers['Content-Length']))
            try:
                status, raw = state.response(json.loads(body))
                self.send_response(status)
                self.send_header('Content-Length', str(len(raw) +
                                 (10 if state.case == 'socket_truncation' else 0)))
                if state.case == 'redirect':
                    self.send_header('Location', 'http://never-contact.invalid/')
                self.end_headers()
                self.wfile.write(raw)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_CONNECT(self):
            state.connects += 1
            if self.headers.get('Proxy-Authorization') != PROXY_AUTH:
                self.send_error(407)
                return
            assert self.path == 'house.mock:' + str(origin.server_port)
            self.send_response(200)
            self.end_headers()
            self.wfile.flush()
            with socket.create_connection(('127.0.0.1', origin.server_port), timeout=2) as peer:
                sockets = [self.connection, peer]
                while True:
                    readable, _, _ = select.select(sockets, [], [], 2)
                    if not readable:
                        break
                    for stream in readable:
                        try:
                            data = stream.recv(65536)
                            if not data:
                                return
                            (peer if stream is self.connection else self.connection).sendall(data)
                        except OSError:
                            return

    origin = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.load_cert_chain(cert, key)
    origin.socket = tls.wrap_socket(origin.socket, server_side=True)
    proxy = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threads = [threading.Thread(target=s.serve_forever, daemon=True) for s in (origin, proxy)]
    for thread in threads:
        thread.start()
    state.proxy_url = f'http://synthetic-user:synthetic-pass@127.0.0.1:{proxy.server_port}'
    state.https_endpoint = f'https://house.mock:{origin.server_port}'
    state.cert = cert
    yield state
    for server in (proxy, origin):
        server.shutdown()
        server.server_close()


def grant(monkeypatch, route, variant, case):
    route.reset(variant, case)
    for name in ('HTTP_PROXY', 'http_proxy', 'HTTPS_PROXY', 'https_proxy',
                 'MODEL_ENDPOINT', 'MODEL_NAME', 'MODEL_TOKEN', 'MODEL_API_KEY'):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv('MODEL_ENDPOINT', 'http://house.mock:8000')
    monkeypatch.setenv('MODEL_NAME', 'synthetic-model')
    monkeypatch.setenv('MODEL_TOKEN', TOKEN)
    monkeypatch.setenv('M15_VARIANT', variant)
    monkeypatch.setenv('FORECAST_MODE', 'text-first-v5.1')
    monkeypatch.setenv('NO_PROXY', '*')  # must never bypass the explicit audited proxy
    names = ['http_proxy'] if case == 'lowercase_only' else ['HTTP_PROXY']
    if case == 'both_equal':
        names = ['HTTP_PROXY', 'http_proxy', 'HTTPS_PROXY', 'https_proxy']
    if case == 'https_proxy_only':
        names = ['HTTPS_PROXY']
    for name in names:
        monkeypatch.setenv(name, route.proxy_url)
    if case == 'both_conflicting':
        monkeypatch.setenv('http_proxy', 'http://different:grant@127.0.0.1:9')
    if case == 'endpoint_missing':
        monkeypatch.delenv('MODEL_ENDPOINT')
    if case == 'token_missing':
        monkeypatch.delenv('MODEL_TOKEN')
    if case == 'model_missing':
        monkeypatch.delenv('MODEL_NAME')
    if case == 'proxy_missing':
        monkeypatch.delenv('HTTP_PROXY')
    if case == 'invalid_proxy_credentials':
        monkeypatch.setenv('HTTP_PROXY', 'http://127.0.0.1:8080')
    if case == 'proxy_auth_failure':
        monkeypatch.setenv('HTTP_PROXY', route.proxy_url.replace('synthetic-pass', 'wrong-pass'))
    if case == 'https_proxy_scheme':
        monkeypatch.setenv('HTTP_PROXY', route.proxy_url.replace('http:', 'https:'))
    if case in ('https_endpoint', 'tls_invalid'):
        monkeypatch.setenv('MODEL_ENDPOINT', route.https_endpoint)
        if case == 'https_endpoint':
            trusted = ssl.create_default_context(cafile=str(route.cert))
            monkeypatch.setattr(transport.ssl, 'create_default_context', lambda: trusted)
    if case == 'timeout':
        monkeypatch.setattr(transport, '_TIMEOUT_SEC', 0.1)


@pytest.mark.parametrize('kind', ['A', 'B', 'C', 'D', 'E1', 'E2'])
@pytest.mark.parametrize('case', ['normal', 'malformed_outer', 'malformed_json', 'code_fence',
                                  'duplicate_model_keys', 'duplicate_outer_keys',
                                  'schema_mismatch', 'length', 'malformed_envelope'])
def test_parser_receipts(kind, case, mock_route, monkeypatch):
    grant(monkeypatch, mock_route, 'E' if kind.startswith('E') else kind, case)
    if kind == 'E2':
        mock_route.calls = 1
    receipt = transport.new_call_receipt()
    if CASES[case] is None:
        assert engine.request(kind, CTX, receipt) == reply(kind, CTX)
        assert receipt['response_validated'] is True
    else:
        with pytest.raises(transport.HouseError) as caught:
            engine.request(kind, CTX, receipt)
        assert caught.value.category == CASES[case]
        assert receipt['response_validated'] is False
    assert receipt['request_sent'] is True and receipt['response_received'] is True


@pytest.fixture(scope='module')
def baseline_fixture(tmp_path_factory):
    unit = ROOT / 'units/t2-F1-patient-dropped-2015'
    asof = str(tomllib.loads((unit / 'card.toml').read_text())['provenance']['data_cutoff'])
    directory = tmp_path_factory.mktemp('exact_offline_V51')
    out = directory / 'forecast.parquet'
    args = ['--panels', str(unit), '--text', str(unit / 'text'), '--asof', asof,
            '--card', str(unit / 'card.toml'), '--out', str(out)]
    # Avoid changing global environment outside a reversible monkeypatch context.
    with pytest.MonkeyPatch.context() as patch:
        for name in ('MODEL_ENDPOINT', 'MODEL_NAME', 'MODEL_TOKEN', 'MODEL_API_KEY'):
            patch.delenv(name, raising=False)
        patch.setenv('FORECAST_MODE', 'text-first-v5.1')
        assert cli.baseline_main(args) == 0
    return args, out.read_bytes(), pd.read_parquet(out)


@pytest.mark.parametrize('variant', list('ABCDE'))
@pytest.mark.parametrize('case', list(CASES))
def test_runtime_matrix(variant, case, mock_route, monkeypatch, tmp_path, baseline_fixture):
    grant(monkeypatch, mock_route, variant, case)
    args, base_bytes, base_frame = baseline_fixture
    output = tmp_path / 'forecast.parquet'
    run_args = list(args)
    run_args[-1] = str(output)
    assert cli.main(run_args) == 0
    meta_text = (tmp_path / 'forecast_meta.json').read_text()
    meta = json.loads(meta_text)
    receipt = meta['moonshot15']
    frame = pd.read_parquet(output)
    success = CASES[case] is None
    assert receipt['failure_category'] == CASES[case]
    assert receipt['response_validated'] == success
    assert receipt['adjustment_applied'] == success
    assert receipt['fallback_used'] == (not success)
    assert receipt['applied'] == success
    assert len(frame) == len(base_frame) and np.isfinite(frame['value']).all()
    assert np.array_equal(frame[['draw', 'asset', 'horizon']], base_frame[['draw', 'asset', 'horizon']])
    if success:
        assert output.read_bytes() != base_bytes
        assert not np.array_equal(frame['value'], base_frame['value'])
        assert mock_route.calls == (2 if variant == 'E' else 1)
        assert receipt['request_sent'] is True and receipt['response_received'] is True
        assert receipt['location_shift_statistics'] == receipt['geometry']
        assert mock_route.contract_ok and not mock_route.origin_proxy_header_seen
    else:
        assert output.read_bytes() == base_bytes
        assert hashlib.sha256(output.read_bytes()).hexdigest() == receipt['baseline_parquet_SHA256']
        assert receipt['location_shift_statistics'] is None
    if case in ('endpoint_missing', 'token_missing', 'model_missing', 'proxy_missing',
                'both_conflicting', 'invalid_proxy_credentials', 'https_proxy_scheme'):
        assert receipt['request_attempted'] is False and receipt['request_sent'] is False
        assert mock_route.calls == 0
    if case == 'tls_invalid':
        assert receipt['request_sent'] == 'unknown' and mock_route.calls == 0
    text = meta_text + (tmp_path / 'forecast_rationale.md').read_text()
    for secret in (TOKEN, 'synthetic-pass', 'wrong-pass', PROXY_AUTH):
        assert secret not in text
    record = {'executive_summary': 'Synthetic local proxy/House case; no actual service evidence.',
              'variant': variant, 'case': case, 'passed': True, 'wire_House_requests': mock_route.calls,
              'CONNECT_requests': mock_route.connects, 'receipt': receipt,
              'baseline_exact': output.read_bytes() == base_bytes,
              'forecast_SHA256': hashlib.sha256(output.read_bytes()).hexdigest(),
              'rows': len(frame), 'finite': True,
              'timeout_test_override_seconds': 0.1 if case == 'timeout' else None}
    if os.environ.get('M16_MATRIX_DIR'):
        folder = Path(os.environ['M16_MATRIX_DIR'])
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f'{variant}-{case}.json').write_text(json.dumps(record, indent=2) + '\n')


def test_second_call_failure_is_atomic(mock_route, monkeypatch, tmp_path, baseline_fixture):
    grant(monkeypatch, mock_route, 'E', 'second_call_error')
    args, base_bytes, _ = baseline_fixture
    output = tmp_path / 'forecast.parquet'
    args = [*args[:-1], str(output)]
    assert cli.main(args) == 0
    m = json.loads((tmp_path / 'forecast_meta.json').read_text())['moonshot15']
    assert mock_route.calls == 2 and output.read_bytes() == base_bytes
    assert m['requests'][0]['response_validated'] is True
    assert m['requests'][1]['response_validated'] is False
    assert not m['response_validated'] and not m['adjustment_applied'] and m['fallback_used']
    assert m['failure_category'] == 'http_503'
    if os.environ.get('M16_MATRIX_DIR'):
        (Path(os.environ['M16_MATRIX_DIR']) / 'E-second_call_error.json').write_text(
            json.dumps({'executive_summary': 'Synthetic second-call failure preserves exact baseline.',
                        'variant': 'E', 'case': 'second_call_error', 'passed': True,
                        'baseline_exact': True, 'receipt': m}, indent=2) + '\n')


@pytest.mark.parametrize('variant', list('ABCDE'))
def test_deterministic_repeat(variant, mock_route, monkeypatch, tmp_path, baseline_fixture):
    args, _, _ = baseline_fixture
    blobs = []
    for repeat in range(3):
        grant(monkeypatch, mock_route, variant, 'normal')
        folder = tmp_path / str(repeat)
        folder.mkdir()
        assert cli.main([*args[:-1], str(folder / 'forecast.parquet')]) == 0
        blobs.append(tuple((folder / name).read_bytes() for name in
                           ('forecast.parquet', 'forecast_meta.json', 'forecast_rationale.md')))
    assert blobs[0] == blobs[1] == blobs[2]


def test_forecast_functions_are_frozen():
    import ast
    frozen = json.loads((ROOT / 'tests/fixtures/moonshot16_frozen_source.json').read_text())
    old = frozen['engine_source']
    raw = old.encode()
    assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == frozen['engine_blob_sha']
    before = {n.name: ast.dump(n) for n in ast.parse(old).body if isinstance(n, ast.FunctionDef)}
    after = {n.name: ast.dump(n) for n in ast.parse((ROOT / 'moonshot15_engine/engine.py').read_text()).body
             if isinstance(n, ast.FunctionDef)}
    assert set(before) == set(after)
    for name in before:
        if name != 'request':
            assert before[name] == after[name]
    for name, digest in frozen['protected_SHA256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('variant', list('ABCDE'))
def test_old_and_repaired_transform_identical(variant):
    import types
    frozen = json.loads((ROOT / 'tests/fixtures/moonshot16_frozen_source.json').read_text())
    old = types.ModuleType('moonshot15_engine.frozen_engine')
    old.__file__ = str(ROOT / 'moonshot15_engine/engine.py')
    old.__package__ = 'moonshot15_engine'
    exec(compile(frozen['engine_source'], old.__file__, 'exec'), old.__dict__)
    base = np.random.default_rng(318).normal(size=(500, 2, 2))
    r = reply('E2' if variant == 'E' else variant, CTX)
    before, before_meta = old.transform(base, variant, r, CTX['card']['assets'], CTX['card']['horizons'])
    after, after_meta = engine.transform(base, variant, r, CTX['card']['assets'], CTX['card']['horizons'])
    assert np.array_equal(before, after) and before_meta == after_meta
    assert np.array_equal(before.mean(0), after.mean(0))
    assert np.array_equal(before.std(0), after.std(0))
    assert np.array_equal(np.cov(before.reshape(500, -1).T), np.cov(after.reshape(500, -1).T))

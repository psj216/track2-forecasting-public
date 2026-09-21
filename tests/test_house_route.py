"""## Executive summary (read this first)

Exercise the organizer's origin + /v1 + bearer contract against a loopback HTTP server.
No real credentials, market documents, or external model calls are used.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from qfbench2_track_forecasting import text_evidence


@pytest.fixture
def house_server(monkeypatch):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append((self.path, self.headers.get("Authorization"), body))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({"choices": [{"message": {"content": "{}"}}]}).encode())

        def log_message(self, *_args):
            pass

    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    monkeypatch.setenv("no_proxy", "127.0.0.1")
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    monkeypatch.setenv("MODEL_ENDPOINT", f"http://127.0.0.1:{server.server_port}/")
    monkeypatch.setenv("MODEL_NAME", "injected-house-alias")
    monkeypatch.setenv("MODEL_TOKEN", "synthetic-house-token")
    monkeypatch.setenv("MODEL_API_KEY", "must-not-use-legacy-key")
    yield requests
    server.shutdown()
    server.server_close()
    worker.join(timeout=2)


def test_house_origin_path_and_bearer(house_server):
    assert text_evidence.call_evidence_model("synthetic input") == ({}, "", "injected-house-alias")
    path, auth, body = house_server[0]
    assert path == "/v1/chat/completions"
    assert auth == "Bearer synthetic-house-token"
    assert body["model"] == "injected-house-alias"
    assert body["temperature"] == 0
    assert body["chat_template_kwargs"] == {"enable_thinking": False}
    assert "tools" not in body


def test_missing_house_token_falls_back_without_request(house_server, monkeypatch):
    monkeypatch.delenv("MODEL_TOKEN")
    assert text_evidence.call_evidence_model("synthetic") == (
        None,
        "MODEL_TOKEN is unset",
        "injected-house-alias",
    )
    assert not house_server


@pytest.mark.parametrize("suffix", ["/v1", "/chat/completions", "?key=bad", "#fragment"])
def test_house_requires_origin_only(house_server, monkeypatch, suffix):
    endpoint = text_evidence.os.environ["MODEL_ENDPOINT"].rstrip("/")
    monkeypatch.setenv("MODEL_ENDPOINT", endpoint + suffix)
    result, error, _ = text_evidence.call_evidence_model("synthetic")
    assert result is None
    assert error == "MODEL_ENDPOINT must be an HTTP(S) origin without credentials or path"
    assert not house_server


def test_public_proxy_call_contract_is_unchanged(house_server):
    endpoint = text_evidence.os.environ["MODEL_ENDPOINT"].rstrip("/") + "/v1"
    assert text_evidence.call_openai_compatible_evidence_model(
        "synthetic", endpoint=endpoint, model="proxy-model", api_key="proxy-key"
    ) == ({}, "", "proxy-model")
    path, auth, body = house_server[0]
    assert path == "/v1/chat/completions"
    assert auth == "Bearer proxy-key"
    assert body["model"] == "proxy-model"

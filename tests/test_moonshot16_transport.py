"""## Executive summary (read this first)
Prove explicit uppercase proxy compatibility before and after the minimal repair.
"""

import json

import pytest

from moonshot15_engine import official_transport as transport


@pytest.fixture(autouse=True)
def clean_grants(monkeypatch):
    for key in (
        "HTTP_PROXY",
        "http_proxy",
        "HTTPS_PROXY",
        "https_proxy",
        "MODEL_ENDPOINT",
        "MODEL_TOKEN",
        "MODEL_NAME",
    ):
        monkeypatch.delenv(key, raising=False)


@pytest.mark.parametrize(
    "names",
    [
        ["HTTP_PROXY"],
        ["http_proxy"],
        ["HTTP_PROXY", "http_proxy"],
        ["HTTPS_PROXY"],
        ["https_proxy"],
        ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy"],
    ],
)
def test_proxy_aliases(names, monkeypatch):
    for name in names:
        monkeypatch.setenv(name, "http://u:p@localhost:8000")
    assert transport._proxy_url() == "http://u:p@localhost:8000"
    assert all(__import__("os").environ[name] == "http://u:p@localhost:8000" for name in names)


@pytest.mark.parametrize("pair", [("HTTP_PROXY", "http_proxy"), ("HTTP_PROXY", "HTTPS_PROXY")])
def test_proxy_conflict(pair, monkeypatch):
    monkeypatch.setenv(pair[0], "http://u:p@localhost:8000")
    monkeypatch.setenv(pair[1], "http://u:p@localhost:9000")
    with pytest.raises(transport.HouseError, match="proxy_configuration_conflict"):
        transport._proxy_url()


@pytest.mark.parametrize(
    "endpoint, category",
    [
        ("", "endpoint_missing"),
        ("http://u:p@house.test", "endpoint_invalid"),
        ("http://house.test/v1", "endpoint_invalid"),
        ("http://house.test/other", "endpoint_invalid"),
        ("http://house.test?key=value", "endpoint_invalid"),
        ("http://house.test#fragment", "endpoint_invalid"),
        ("ftp://house.test", "endpoint_invalid"),
        ("http://house.test:bad", "configuration_invalid"),
    ],
)
def test_endpoint_guard(endpoint, category, monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://u:p@localhost:8000")
    with pytest.raises(transport.HouseError, match=category):
        transport._house_reply(endpoint, "synthetic-token", b"{}")


def test_cannot_override_injected_endpoint(monkeypatch):
    monkeypatch.setenv("MODEL_ENDPOINT", "http://house.test")
    with pytest.raises(transport.HouseError, match="endpoint_not_injected"):
        transport._house_reply("http://vendor.test", "synthetic-token", b"{}")


def test_production_timeout_and_response_budget():
    assert transport._TIMEOUT_SEC == 60
    assert transport._RESPONSE_BYTES == 1024 * 1024


def test_https_connect_and_origin_header_separation(monkeypatch):
    observed = {}
    monkeypatch.setenv("HTTP_PROXY", "http://u:p@proxy.test:8080")
    monkeypatch.setenv("MODEL_ENDPOINT", "https://house.test:8443")

    class Connection:
        def __init__(self, host, port, timeout, context):
            observed["proxy"] = (host, port)
            assert context.check_hostname
            assert context.verify_mode == transport.ssl.CERT_REQUIRED

        def set_tunnel(self, host, port, headers):
            observed["tunnel"] = (host, port, headers)

        def request(self, method, path, body, headers):
            observed["origin"] = (method, path, headers)

        def getresponse(self):
            return self

        status = 200

        def read(self, limit):
            return b"{}"

        def close(self):
            pass

    monkeypatch.setattr(transport.http.client, "HTTPSConnection", Connection)
    receipt = transport.new_call_receipt()
    assert (
        transport._house_reply("https://house.test:8443", "synthetic-token", b"{}", receipt) == {}
    )
    assert observed["proxy"] == ("proxy.test", 8080)
    assert observed["tunnel"][:2] == ("house.test", 8443)
    assert "Proxy-Authorization" in observed["tunnel"][2]
    assert observed["origin"][:2] == ("POST", "/v1/chat/completions")
    assert "Proxy-Authorization" not in observed["origin"][2]
    assert receipt["request_sent"] is True and receipt["response_received"] is True
    assert receipt["response_validated"] is False  # transport alone does not validate model schema


@pytest.mark.parametrize(
    "error, category, sent",
    [
        (TimeoutError("credential-must-not-log"), "timeout", "unknown"),
        (
            OSError("Tunnel connection failed: 407 synthetic-secret"),
            "proxy_authentication_failure",
            "unknown",
        ),
        (
            OSError("Tunnel connection failed: 403 synthetic-secret"),
            "proxy_connect_http_error",
            "unknown",
        ),
        (OSError("synthetic-secret"), "network_error", "unknown"),
    ],
)
def test_credential_free_network_failures(error, category, sent, monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://u:p@proxy.test:8080")

    class Connection:
        def __init__(self, *args, **kwargs):
            pass

        def request(self, *args, **kwargs):
            raise error

        def close(self):
            pass

    monkeypatch.setattr(transport.http.client, "HTTPConnection", Connection)
    receipt = transport.new_call_receipt()
    with pytest.raises(transport.HouseError) as caught:
        transport._house_reply("http://house.test", "synthetic-token", b"{}", receipt)
    assert str(caught.value) == category
    assert receipt["failure_category"] == category
    assert receipt["request_sent"] == sent
    assert "synthetic-secret" not in json.dumps(receipt)
    assert "credential-must-not-log" not in json.dumps(receipt)


def test_uppercase_proxy_success(monkeypatch):
    for key in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "MODEL_ENDPOINT"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("HTTP_PROXY", "http://synthetic-user:synthetic-pass@proxy.test:8080")

    class Connection:
        def __init__(self, host, port, timeout):
            assert (host, port) == ("proxy.test", 8080)

        def request(self, method, path, body, headers):
            assert method == "POST"
            assert path == "http://house.test:8000/v1/chat/completions"

        def getresponse(self):
            return self

        status = 200

        def read(self, limit):
            return b'{"ok":true}'

        def close(self):
            pass

    monkeypatch.setattr(transport.http.client, "HTTPConnection", Connection)
    assert transport._house_reply("http://house.test:8000", "synthetic-token", b"{}")["ok"]

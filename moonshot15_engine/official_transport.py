"""## Executive summary (read this first)
Literal official House-only transport; no vendor fallback or credential logging.
"""
from __future__ import annotations
import base64
import http.client
import json
import os
from typing import Any
from urllib.parse import unquote, urlsplit
_TIMEOUT_SEC = 60
_RESPONSE_BYTES = 1024 * 1024

def _house_reply(endpoint: str, token: str, body: bytes) -> Any:
    """Use the supplied receipt proxy, without direct fallback, bypasses or redirects."""
    target = urlsplit(endpoint)
    proxy = urlsplit(os.environ.get("http_proxy", ""))
    if (
        target.scheme != "http"
        or not target.hostname
        or target.username is not None
        or target.password is not None
        or target.path.rstrip("/") not in ("", "/v1")
        or target.query
        or target.fragment
        or proxy.scheme != "http"
        or not proxy.hostname
        or not proxy.port
        or proxy.path not in ("", "/")
        or proxy.query
        or proxy.fragment
        or not proxy.username
        or not proxy.password
        or not token
        or any(ord(c) < 33 or ord(c) > 126 for c in token)
    ):
        raise ValueError("invalid House model or proxy configuration")
    credentials = unquote(proxy.username) + ":" + unquote(proxy.password)
    if any(ord(c) < 32 or ord(c) > 126 for c in credentials):
        raise ValueError("invalid House proxy credentials")
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token,
        "Proxy-Authorization": "Basic " + base64.b64encode(credentials.encode()).decode(),
    }
    connection = http.client.HTTPConnection(proxy.hostname, proxy.port, timeout=_TIMEOUT_SEC)
    try:
        connection.request(
            "POST", target.scheme + "://" + target.netloc + "/v1/chat/completions", body, headers
        )
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError("House model request was refused")
        raw = response.read(_RESPONSE_BYTES + 1)
        if len(raw) > _RESPONSE_BYTES:
            raise ValueError("House model response was too large")
        return json.loads(raw)
    finally:
        connection.close()

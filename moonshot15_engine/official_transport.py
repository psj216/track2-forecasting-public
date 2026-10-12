"""## Executive summary (read this first)
Call only the injected House origin through its authenticated audited proxy.
Receipts record local observations without credentials, retries or redirects.
"""

from __future__ import annotations

import base64
import http.client
import json
import os
import re
import ssl
from typing import Any
from urllib.parse import unquote, urlsplit

_TIMEOUT_SEC = 60
_RESPONSE_BYTES = 1024 * 1024


class HouseError(ValueError):
    """A credential-free closed failure category; no server/exception text."""

    def __init__(self, category: str, status: int | None = None):
        super().__init__(category)
        self.category = category
        self.status = status


def new_call_receipt() -> dict[str, Any]:
    return {
        "request_attempted": False,
        "request_sent": False,
        "response_received": False,
        "response_validated": False,
        "http_status": None,
        "failure_category": None,
    }


def _proxy_url() -> str:
    # One audited route; never arbitrarily choose conflicting proxy grants.
    values = [
        os.environ.get(k, "") for k in ("http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY")
    ]
    supplied = [v for v in values if v]
    if not supplied:
        raise HouseError("proxy_missing")
    if len(set(supplied)) != 1:
        raise HouseError("proxy_configuration_conflict")
    return supplied[0]


def _configuration(endpoint: str, token: str):
    if not endpoint:
        raise HouseError("endpoint_missing")
    if not token:
        raise HouseError("token_missing")
    if any(ord(c) < 33 or ord(c) > 126 for c in token):
        raise HouseError("token_invalid")
    injected = os.environ.get("MODEL_ENDPOINT")
    if injected is not None and endpoint != injected:
        raise HouseError("endpoint_not_injected")
    try:
        target = urlsplit(endpoint)
        proxy = urlsplit(_proxy_url())
        target_port = target.port
        proxy_port = proxy.port
    except HouseError:
        raise
    except ValueError:
        raise HouseError("configuration_invalid") from None
    if (
        target.scheme not in ("http", "https")
        or not target.hostname
        or target.username is not None
        or target.password is not None
        or target.path not in ("", "/")
        or target.query
        or target.fragment
        or any(ord(c) <= 32 or ord(c) >= 127 for c in endpoint)
    ):
        raise HouseError("endpoint_invalid")
    # HTTPS must be bound to the exact organizer-injected origin.
    if target.scheme == "https" and injected is None:
        raise HouseError("endpoint_not_injected")
    if (
        proxy.scheme != "http"
        or not proxy.hostname
        or not proxy_port
        or proxy.path not in ("", "/")
        or proxy.query
        or proxy.fragment
        or any(ord(c) <= 32 or ord(c) >= 127 for c in proxy.geturl())
    ):
        raise HouseError("proxy_configuration_invalid")
    if not proxy.username or not proxy.password:
        raise HouseError("proxy_credentials_invalid")
    credentials = unquote(proxy.username) + ":" + unquote(proxy.password)
    if any(ord(c) < 32 or ord(c) > 126 for c in credentials):
        raise HouseError("proxy_credentials_invalid")
    auth = "Basic " + base64.b64encode(credentials.encode()).decode()
    return target, target_port, proxy, proxy_port, auth


def _outer_pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise HouseError("duplicate_outer_json_keys")
        obj[key] = value
    return obj


def _nonfinite(_value):
    raise HouseError("malformed_outer_json")


def _house_reply(
    endpoint: str, token: str, body: bytes, receipt: dict[str, Any] | None = None
) -> Any:
    """No direct fallback, NO_PROXY bypass, redirects, retries or exception text."""
    receipt = new_call_receipt() if receipt is None else receipt
    connection = None
    try:
        target, target_port, proxy, proxy_port, proxy_auth = _configuration(endpoint, token)
        headers = {"Content-Type": "application/json", "Authorization": "Bearer " + token}
        if target.scheme == "https":
            # HTTP CONNECT via the granted proxy; TLS checks certificate and hostname.
            # Proxy auth is on CONNECT only, never exposed to the House origin.
            connection = http.client.HTTPSConnection(
                proxy.hostname,
                proxy_port,
                timeout=_TIMEOUT_SEC,
                context=ssl.create_default_context(),
            )
            connection.set_tunnel(
                target.hostname, target_port or 443, headers={"Proxy-Authorization": proxy_auth}
            )
            path = "/v1/chat/completions"
        else:
            connection = http.client.HTTPConnection(
                proxy.hostname, proxy_port, timeout=_TIMEOUT_SEC
            )
            headers["Proxy-Authorization"] = proxy_auth
            path = target.scheme + "://" + target.netloc + "/v1/chat/completions"
        receipt["request_attempted"] = True
        # A partial socket write does not prove completed submission to the proxy.
        receipt["request_sent"] = "unknown"
        connection.request("POST", path, body, headers)
        receipt["request_sent"] = True
        response = connection.getresponse()
        receipt["response_received"] = True
        receipt["http_status"] = response.status
        if response.status != 200:
            category = (
                "proxy_authentication_failure"
                if response.status == 407
                else "redirect_rejected"
                if 300 <= response.status < 400
                else "http_" + str(response.status)
            )
            raise HouseError(category, response.status)
        raw = response.read(_RESPONSE_BYTES + 1)
        if len(raw) > _RESPONSE_BYTES:
            raise HouseError("response_too_large")
        length = getattr(response, "getheader", lambda _key: None)("Content-Length")
        if length is not None:
            try:
                declared = int(length)
            except ValueError:
                raise HouseError("malformed_response") from None
            if declared != len(raw):
                raise HouseError("response_incomplete")
        try:
            return json.loads(raw, object_pairs_hook=_outer_pairs, parse_constant=_nonfinite)
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise HouseError("malformed_outer_json") from None
    except HouseError as exc:
        receipt["failure_category"] = exc.category
        raise
    except TimeoutError:
        receipt["failure_category"] = "timeout"
        raise HouseError("timeout") from None
    except ssl.SSLError:
        receipt["failure_category"] = "tls_validation_failure"
        raise HouseError("tls_validation_failure") from None
    except http.client.IncompleteRead:
        receipt["failure_category"] = "response_incomplete"
        raise HouseError("response_incomplete") from None
    except (OSError, http.client.HTTPException) as exc:
        # Only inspect the stdlib CONNECT status. Never persist proxy-controlled text.
        match = re.match(r"^Tunnel connection failed: ([0-9]{3})\b", str(exc))
        status = int(match[1]) if match else None
        category = (
            "proxy_authentication_failure"
            if status == 407
            else "proxy_connect_http_error"
            if status
            else "network_error"
        )
        if status:
            receipt["proxy_connect_status"] = status
        receipt["failure_category"] = category
        raise HouseError(category, status) from None
    finally:
        if connection is not None:
            connection.close()

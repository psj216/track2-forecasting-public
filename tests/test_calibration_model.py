"""## Executive summary (read this first)

Prove the development proxy is isolated from submission settings and never serializes credentials.
The tests make no network calls.  They also pin deterministic public metadata and explicit failure
when the calibration endpoint or model name is absent.
"""

from __future__ import annotations

import inspect
import json

import pytest

from backtesting.calibration_model import CalibrationModelClient
from qfbench2_track_forecasting import cli


def test_calibration_endpoint_unset_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CALIBRATION_MODEL_ENDPOINT", raising=False)
    monkeypatch.setenv("CALIBRATION_MODEL_NAME", "test-model")

    with pytest.raises(RuntimeError, match="CALIBRATION_MODEL_ENDPOINT is unset"):
        CalibrationModelClient.from_environment()


def test_calibration_model_name_unset_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CALIBRATION_MODEL_ENDPOINT", "http://127.0.0.1:8000/v1")
    monkeypatch.delenv("CALIBRATION_MODEL_NAME", raising=False)

    with pytest.raises(RuntimeError, match="CALIBRATION_MODEL_NAME is unset"):
        CalibrationModelClient.from_environment()


def test_credentials_are_not_represented_or_serialized() -> None:
    secret = "not-for-output"
    client = CalibrationModelClient("https://proxy.invalid/v1", "nvidia/test-model", api_key=secret)

    assert secret not in repr(client)
    assert secret not in json.dumps(client.public_metadata(), sort_keys=True)
    assert client.public_metadata() == {
        "max_tokens": 5000,
        "model_name": "nvidia/test-model",
        "thinking": False,
        "timeout_seconds": 90,
    }


def test_public_metadata_is_deterministic() -> None:
    first = CalibrationModelClient("http://localhost:8000/v1", "test-model")
    second = CalibrationModelClient("http://localhost:8000/v1", "test-model")

    assert first.public_metadata() == second.public_metadata()


def test_submission_cli_does_not_read_calibration_environment() -> None:
    source = inspect.getsource(cli)

    assert "CALIBRATION_MODEL_" not in source

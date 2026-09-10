"""## Executive summary (read this first)

Connect development-only evidence replay to an explicitly configured OpenAI-compatible model.
This module reads only ``CALIBRATION_MODEL_*`` variables.  The submission CLI never imports it,
so the organizer ``MODEL_ENDPOINT`` contract stays independent.  Credentials are held in memory,
excluded from representations, and never returned as replay metadata.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from urllib.parse import urlparse

from qfbench2_track_forecasting.text_evidence import call_openai_compatible_evidence_model

_DEFAULT_MAX_TOKENS = 5_000
_DEFAULT_TIMEOUT_SECONDS = 90


def _positive_integer(name: str, default: int) -> int:
    raw = os.environ.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


@dataclass(frozen=True)
class CalibrationModelClient:
    """In-memory configuration for one development-only evidence model."""

    endpoint: str = field(repr=False)
    model_name: str
    api_key: str = field(default="", repr=False)
    max_tokens: int = _DEFAULT_MAX_TOKENS
    thinking: bool = False
    timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS

    @classmethod
    def from_environment(cls) -> CalibrationModelClient:
        """Load the isolated calibration contract and fail before any model request."""
        endpoint = os.environ.get("CALIBRATION_MODEL_ENDPOINT", "").strip()
        model_name = os.environ.get("CALIBRATION_MODEL_NAME", "").strip()
        if not endpoint:
            raise RuntimeError(
                "CALIBRATION_MODEL_ENDPOINT is unset; refusing to manufacture proxy evidence"
            )
        if not model_name:
            raise RuntimeError(
                "CALIBRATION_MODEL_NAME is unset; refusing to create an unpinned replay"
            )
        parsed = urlparse(endpoint)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("CALIBRATION_MODEL_ENDPOINT must be an absolute HTTP(S) URL")
        thinking = os.environ.get("CALIBRATION_MODEL_THINKING", "off").strip().lower() in {
            "1",
            "on",
            "true",
        }
        return cls(
            endpoint=endpoint,
            model_name=model_name,
            api_key=os.environ.get("CALIBRATION_MODEL_API_KEY", "").strip(),
            max_tokens=_positive_integer("CALIBRATION_MODEL_MAX_TOKENS", _DEFAULT_MAX_TOKENS),
            thinking=thinking,
            timeout_seconds=_positive_integer(
                "CALIBRATION_MODEL_TIMEOUT_SECONDS", _DEFAULT_TIMEOUT_SECONDS
            ),
        )

    def call(self, prompt: str) -> tuple[object | None, str, str]:
        """Request strict evidence JSON without exposing endpoint configuration downstream."""
        return call_openai_compatible_evidence_model(
            prompt,
            endpoint=self.endpoint,
            model=self.model_name,
            api_key=self.api_key,
            max_tokens=self.max_tokens,
            thinking=self.thinking,
            timeout_seconds=self.timeout_seconds,
        )

    def public_metadata(self) -> dict[str, object]:
        """Return deterministic, credential-free provenance for reports and tests."""
        return {
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "thinking": self.thinking,
            "timeout_seconds": self.timeout_seconds,
        }

"""Explicit artifact loading; fitting never occurs in the runtime."""

import json
from pathlib import Path


def load(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text())
    if payload.get("schema") != "v12-reconstructed-1":
        raise ValueError("Incompatible V12 reconstructed artifact")
    if len(payload["assets"]) != len(payload["decoder_loadings"]):
        raise ValueError("Decoder asset axis mismatch")
    return payload

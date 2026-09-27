"""## Executive summary (read this first)

Read checksum-bound, dated event features. The catalog contains no market responses;
those are reconstructed only from the forecasting unit's cutoff-safe panel.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from ..v6.fingerprint import Fingerprint

ALLOWED_HOSTS = {"www.federalreserve.gov", "www.bls.gov", "www.ecb.europa.eu"}


@dataclass(frozen=True)
class Event:
    published_at: str
    episode_id: str
    fingerprint: Fingerprint
    source_url: str
    source_sha256: str
    text: str
    doc_type: str
    event_type: str
    region: str
    timestamp_precision: str


def load_catalog(root: Path, cutoff: str) -> tuple[list[Event], dict]:
    date.fromisoformat(cutoff[:10])
    manifest = json.loads((root / "catalog_manifest.json").read_text())
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported V7 catalog schema")
    index_raw = (root / "index.json").read_bytes()
    if hashlib.sha256(index_raw).hexdigest() != manifest["index_sha256"]:
        raise ValueError("V7 catalog index checksum mismatch")
    index = json.loads(index_raw)
    events = []
    seen = set()
    for entry in index:
        date.fromisoformat(entry["published_at"])
        if entry["published_at"] > cutoff[:10]:
            continue
        path = (root / entry["file"]).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("V7 catalog path escapes root")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
            raise ValueError("V7 event checksum mismatch")
        row = json.loads(raw)
        if row["published_at"] != entry["published_at"]:
            raise ValueError("V7 event date mismatch")
        if urlparse(row["source_url"]).hostname not in ALLOWED_HOSTS:
            raise ValueError("V7 source outside provenance policy")
        if hashlib.sha256(row["text"].encode()).hexdigest() != row["text_sha256"]:
            raise ValueError("V7 event text checksum mismatch")
        if len(row["source_sha256"]) != 64:
            raise ValueError("V7 source checksum missing")
        if row["episode_id"] in seen:
            raise ValueError("duplicate V7 episode")
        seen.add(row["episode_id"])
        events.append(
            Event(
                row["published_at"],
                row["episode_id"],
                Fingerprint(**row["fingerprint"]),
                row["source_url"],
                row["source_sha256"],
                row["text"],
                row["doc_type"],
                row["event_type"],
                row["region"],
                row["timestamp_precision"],
            )
        )
    return events, manifest

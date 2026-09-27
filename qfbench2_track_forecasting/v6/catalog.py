"""## Executive summary (read this first)

Read a checksum-bound event calendar. Date metadata is checked before opening each
feature record, so future document features never enter inference or retrieval.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from .fingerprint import Fingerprint


@dataclass(frozen=True)
class EventRecord:
    published_at: str
    episode_id: str
    fingerprint: Fingerprint
    source_url: str
    source_sha256: str
    text: str
    doc_type: str


def load_catalog(root: Path, asof: str) -> list[EventRecord]:
    date.fromisoformat(asof)
    index = json.loads((root / "index.json").read_text())
    if index.get("schema_version") != 1:
        raise ValueError("unsupported event catalog schema")
    records = []
    seen = set()
    for entry in index["records"]:
        date.fromisoformat(entry["published_at"])
        if entry["published_at"] > asof:
            continue
        path = (root / entry["file"]).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("catalog path escapes root")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
            raise ValueError("catalog feature checksum mismatch")
        row = json.loads(raw)
        if row["published_at"] != entry["published_at"] or row["published_at"] > asof:
            raise ValueError("catalog publication date mismatch")
        if (
            not row.get("license_basis")
            or not row.get("retrieved_at")
            or len(row["source_sha256"]) != 64
        ):
            raise ValueError("catalog provenance missing")
        if urlparse(row["source_url"]).hostname not in {"www.federalreserve.gov"}:
            raise ValueError("source not covered by provenance policy")
        if hashlib.sha256(row["text"].encode()).hexdigest() != row["text_sha256"]:
            raise ValueError("catalog text checksum mismatch")
        key = (row["published_at"], row["source_sha256"])
        if key in seen:
            continue
        seen.add(key)
        records.append(
            EventRecord(
                row["published_at"],
                row["episode_id"],
                Fingerprint(**row["fingerprint"]),
                row["source_url"],
                row["source_sha256"],
                row["text"],
                row["doc_type"],
            )
        )
    return sorted(records, key=lambda r: (r.published_at, r.source_url))

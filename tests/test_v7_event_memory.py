"""## Executive summary (read this first)

Check V7's cutoff firewall, exact F2 abstention, independent response support,
and preservation of every non-F2 family.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from qfbench2_track_forecasting.v6.fingerprint import Fingerprint
from qfbench2_track_forecasting.v7.catalog import load_catalog
from qfbench2_track_forecasting.v7.encoder import Query
from qfbench2_track_forecasting.v7.engine import apply_v7


def _catalog(root: Path, n: int = 10) -> None:
    (root / "records").mkdir()
    records = []
    for i in range(n):
        day = (pd.Timestamp("2016-01-01") + pd.Timedelta(days=i * 90)).date().isoformat()
        text = "The committee raised the target range for the federal funds rate."
        row = {
            "published_at": day,
            "episode_id": f"FED:{i}",
            "doc_type": "fomc_statement",
            "event_type": "POLICY_DECISION",
            "region": "US",
            "timestamp_precision": "date",
            "text": text,
            "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "source_url": "https://www.federalreserve.gov/policy.htm",
            "source_sha256": "1" * 64,
            "fingerprint": Fingerprint(
                "policy", "FED", "US", "CURRENT", 0.95, {"policy": 1.0}
            ).payload(),
        }
        raw = (json.dumps(row) + "\n").encode()
        file = f"records/{i}.json"
        (root / file).write_bytes(raw)
        records.append(
            {"published_at": day, "file": file, "sha256": hashlib.sha256(raw).hexdigest()}
        )
    index = (json.dumps(records) + "\n").encode()
    (root / "index.json").write_bytes(index)
    (root / "catalog_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "catalog_version": "test",
                "event_count": n,
                "index_sha256": hashlib.sha256(index).hexdigest(),
            }
        )
    )


def test_future_record_not_opened(tmp_path: Path) -> None:
    _catalog(tmp_path, 2)
    (tmp_path / "records/1.json").unlink()
    events, _ = load_catalog(tmp_path, "2016-02-01")
    assert len(events) == 1
    # The missing future source cannot affect an earlier forecast.


def test_f2_analog_activation_and_exact_family_fallback(tmp_path: Path, monkeypatch) -> None:
    _catalog(tmp_path)
    query = Query(
        Fingerprint(
            "policy",
            "FED",
            "US",
            "CURRENT",
            0.95,
            {"policy": 1.0},
            evidence="policy rate increased",
        ),
        "POLICY_DECISION",
        "2020-01-01",
        "query",
    )
    monkeypatch.setattr(
        "qfbench2_track_forecasting.v7.engine.current_queries", lambda *args: [query]
    )
    days = pd.bdate_range("2015-01-01", "2020-02-01")
    history = {"A": pd.Series(np.sin(np.arange(len(days)) / 50), index=days)}
    base = np.zeros((500, 1, 1))
    args = (base, history, ["A"], [5], "level", "daily")
    out, meta = apply_v7(*args, "T2-F2", "2020-01-01", 17, tmp_path, tmp_path)
    assert meta["applied"]
    assert meta["max_response_date"] < "2020-01-01"
    assert 0 < np.count_nonzero(out != base) <= 60
    frozen, frozen_meta = apply_v7(*args, "T2-F3", "2020-01-01", 17, tmp_path, tmp_path)
    assert frozen is base and not frozen_meta["applied"]


def test_weak_support_exact_fallback(tmp_path: Path, monkeypatch) -> None:
    _catalog(tmp_path, 1)
    query = Query(
        Fingerprint("policy", "FED", "US", "CURRENT", 0.95, {"policy": 1.0}),
        "POLICY_DECISION",
        "2020-01-01",
        "query",
    )
    monkeypatch.setattr(
        "qfbench2_track_forecasting.v7.engine.current_queries", lambda *args: [query]
    )
    days = pd.bdate_range("2015-01-01", "2020-02-01")
    history = {"A": pd.Series(np.arange(len(days), dtype=float), index=days)}
    base = np.zeros((500, 1, 1))
    out, meta = apply_v7(
        base, history, ["A"], [5], "level", "daily", "T2-F2", "2020-01-01", 17, tmp_path, tmp_path
    )
    assert out is base and not meta["applied"]

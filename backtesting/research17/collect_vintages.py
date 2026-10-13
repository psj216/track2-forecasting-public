"""## Executive summary (read this first)

Download only specified public ALFRED previous-day vintages. Reject mixed/latest
headers and future nonmissing values. Store raw values outside this public repo.
No credentials, forecasts, model fitting or scores.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def collect(origin: str, output: Path) -> dict:
    vintage = (pd.Timestamp(origin) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    stamp = vintage.replace("-", "")
    url = (
        "https://alfred.stlouisfed.org/graph/alfredgraph.csv?"
        f"id=DGS2,DGS5,DGS10&vintage_date={vintage},{vintage},{vintage}"
        f"&cosd=2000-01-01&coed={vintage}"
    )
    path = output / f"{origin}.csv"
    cached = path.exists()
    if cached:
        raw = path.read_bytes()
    else:
        req = urllib.request.Request(url, headers={"User-Agent": "R17 public PIT research audit"})
        with urllib.request.urlopen(req, timeout=35) as response:
            assert response.status == 200
            raw = response.read(2_000_001)
        assert len(raw) <= 2_000_000
        path.write_bytes(raw)
    frame = pd.read_csv(io.BytesIO(raw))
    headers = ["observation_date"] + [f"{s}_{stamp}" for s in ["DGS2", "DGS5", "DGS10"]]
    assert list(frame.columns) == headers, (origin, list(frame.columns))
    dates = pd.to_datetime(frame["observation_date"])
    nonmissing = frame[headers[1:]].notna().any(axis=1)
    assert dates[nonmissing].max() <= pd.Timestamp(vintage), origin
    assert not dates.duplicated().any()
    past = frame.loc[(dates >= "2000-01-01") & (dates < origin)]
    assert len(past.dropna()) >= 180, origin
    receipt = {
        "origin": origin,
        "vintage": vintage,
        "url": url,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "headers": headers,
        "strictly_previous_day": True,
        "future_nonmissing_values": 0,
        "usable_complete_past_rows": len(past.dropna()),
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "cached": cached,
    }
    (output / f"{origin}.receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--lock", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--start", type=int, required=True)
    p.add_argument("--stop", type=int, required=True)
    a = p.parse_args()
    lock = json.loads(a.lock.read_text())
    origins = (lock["training_origins"] + lock["evaluation_origins"])[a.start : a.stop]
    a.output.mkdir(parents=True, exist_ok=True)
    errors = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(collect, o, a.output): o for o in origins}
        done = 0
        for f in as_completed(futures):
            done += 1
            try:
                r = f.result()
                if done % 8 == 0 or done == len(origins):
                    print(
                        json.dumps(
                            {
                                "stage": "PIT_DOWNLOAD",
                                "completed": done,
                                "batch_size": len(origins),
                                "last_origin": r["origin"],
                            }
                        ),
                        flush=True,
                    )
            except Exception as e:
                errors.append({"origin": futures[f], "error": type(e).__name__, "message": str(e)})
                print(json.dumps(errors[-1]), flush=True)
                if len(errors) >= 2:
                    for pending in futures:
                        pending.cancel()
                    break
    (a.output / f"batch-{a.start}-{a.stop}.json").write_text(
        json.dumps({"requested": origins, "errors": errors, "passed": not errors}, indent=2) + "\n"
    )
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

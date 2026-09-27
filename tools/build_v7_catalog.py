"""## Executive summary (read this first)

Build a text-only event memory from official Fed, BLS and ECB archives. Release
dates come from dated archive URLs and are cross-checked against the release body.
Raw pages are cached outside the repository; no asset data or future returns enter
the catalog. The builder records skipped sources and source provenance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bs4 import BeautifulSoup

from qfbench2_track_forecasting.v6.catalog import load_catalog as load_fed
from qfbench2_track_forecasting.v7.encoder import fingerprint_for

BLS = "https://www.bls.gov"
ECB = "https://www.ecb.europa.eu"
INDEXES = {
    "CPI_RELEASE": BLS + "/bls/news-release/cpi.htm",
    "EMPLOYMENT_RELEASE": BLS + "/bls/news-release/empsit.htm",
    "POLICY_DECISION": ECB + "/press/govcdec/mopo/previous/html/index.en.html",
}


def fetch(url: str, cache: Path) -> bytes:
    path = cache / (hashlib.sha256(url.encode()).hexdigest() + ".html")
    if path.is_file():
        return path.read_bytes()
    req = urllib.request.Request(url, headers={"User-Agent": "Track2 event-catalog research/1.0"})
    with urllib.request.urlopen(req, timeout=25) as response:
        raw = response.read()
    path.write_bytes(raw)
    return raw


def discover(cache: Path, start: int, end: int) -> tuple[list[dict], dict]:
    sources, hashes = [], {}
    for event_type, url in INDEXES.items():
        raw = fetch(url, cache)
        hashes[url] = hashlib.sha256(raw).hexdigest()
        soup = BeautifulSoup(raw, "html.parser")
        for a in soup.select("a[href]"):
            href = a["href"]
            if event_type.startswith("CPI"):
                match = re.search(r"/news\.release/archives/cpi_(\d{8})\.htm$", href)
            elif event_type.startswith("EMPLOYMENT"):
                match = re.search(r"/news\.release/archives/empsit_(\d{8})\.htm$", href)
            else:
                if a.get_text(" ", strip=True).lower() != "monetary policy decisions":
                    continue
                match = re.search(r"/press/pr/date/\d{4}/html/pr(\d{6})\.en\.html$", href)
            if not match:
                continue
            fmt = "%m%d%Y" if event_type != "POLICY_DECISION" else "%y%m%d"
            published = datetime.strptime(match[1], fmt).date().isoformat()
            if not start <= int(published[:4]) <= end:
                continue
            source_url = urljoin(url, href)
            sources.append(
                {
                    "published_at": published,
                    "source_url": source_url,
                    "event_type": event_type,
                    "index_url": url,
                }
            )
    # ECB's current listing is loaded from official year-specific HTML fragments.
    for year in range(max(2017, start), end + 1):
        url = ECB + f"/press/govcdec/mopo/{year}/html/index_include.en.html"
        try:
            raw = fetch(url, cache)
        except Exception:
            continue
        hashes[url] = hashlib.sha256(raw).hexdigest()
        soup = BeautifulSoup(raw, "html.parser")
        for a in soup.select("a[href]"):
            if a.get_text(" ", strip=True).lower() != "monetary policy decisions":
                continue
            href = a["href"]
            match = re.search(
                r"/press/pr/date/\d{4}/html/ecb\.mp(\d{6})~[a-z0-9]+\.en\.html$", href
            )
            if not match:
                continue
            published = datetime.strptime(match[1], "%y%m%d").date().isoformat()
            sources.append(
                {
                    "published_at": published,
                    "source_url": urljoin(ECB, href),
                    "event_type": "POLICY_DECISION",
                    "index_url": url,
                }
            )
    return list({s["source_url"]: s for s in sources}.values()), hashes


def download(source: dict, cache: Path) -> tuple[dict, str] | None:
    try:
        raw = fetch(source["source_url"], cache)
        soup = BeautifulSoup(raw, "html.parser")
        if source["event_type"] == "POLICY_DECISION":
            body = soup.select_one("main") or soup.select_one("#content")
            text = body.get_text(" ", strip=True)[:1800] if body else ""
            region, publisher, precision = "EU", "ECB", "date"
        else:
            body = soup.select_one("#bodytext pre") or soup.select_one("#bodytext")
            text = body.get_text(" ", strip=True) if body else ""
            region, publisher, precision = "US", "BLS", "date"
            # The opening release paragraph carries contemporaneous values and direction.
            text = text[:4000]
            if re.search(r"\b8:30\s*a\.m\.", text[:500], re.I):
                precision = "08:30 America/New_York"
        if len(text) < 150:
            return None
        if source["event_type"] != "POLICY_DECISION":
            stamp = datetime.strptime(source["published_at"], "%Y-%m-%d").strftime("%B %-d, %Y")
            head = re.sub(r"\s+", " ", text[:1600])
            if stamp not in head and source["published_at"] not in head:
                return None
        kind = source["event_type"]
        fp = fingerprint_for(text, source["published_at"], publisher, source["source_url"], kind)
        if fp is None:
            return None
        row = {
            **source,
            "episode_id": f"{publisher}:{kind}:{source['published_at']}",
            "doc_type": kind.lower(),
            "region": region,
            "publisher": publisher,
            "timestamp_precision": precision,
            "text": text,
            "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "fingerprint": fp.payload(),
            "surprise": "unknown",
        }
        return row, ""
    except Exception:
        return None


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--cache", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--fed", type=Path, default=Path("data/v6"))
    p.add_argument("--start", type=int, default=2005)
    p.add_argument("--end", type=int, default=2025)
    p.add_argument("--workers", type=int, default=10)
    args = p.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    args.out.mkdir(parents=True, exist_ok=True)
    sources, index_hashes = discover(args.cache, args.start, args.end)
    print(f"Discovered {len(sources)} BLS/ECB releases", flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        fetched = []
        for i, row in enumerate(pool.map(lambda source: download(source, args.cache), sources)):
            if row is not None:
                fetched.append(row[0])
            if (i + 1) % 50 == 0:
                print(f"Fetched {i + 1}/{len(sources)} accepted={len(fetched)}", flush=True)
    # Statement and later-published minutes are separate information releases.
    # Keep their common meeting prefix for purged validation grouping.
    fed = {}
    for event in load_fed(args.fed, f"{args.end}-12-31"):
        if not args.start <= int(event.published_at[:4]) <= args.end:
            continue
        if event.doc_type not in {"fomc_statement", "fomc_minutes"}:
            continue
        event_type = "POLICY_DECISION" if event.doc_type == "fomc_statement" else "POLICY_MINUTES"
        row = {
            "published_at": event.published_at,
            "episode_id": event.episode_id + ":" + event_type,
            "event_cluster": event.episode_id,
            "event_type": event_type,
            "doc_type": event.doc_type,
            "region": "US",
            "publisher": "Federal Reserve Board",
            "timestamp_precision": "date",
            "source_url": event.source_url,
            "source_sha256": event.source_sha256,
            "text": event.text,
            "text_sha256": hashlib.sha256(event.text.encode()).hexdigest(),
            "fingerprint": event.fingerprint.payload(),
            "surprise": "unknown",
        }
        fed[row["episode_id"]] = row
    unique = {}
    for row in [*fed.values(), *fetched]:
        # One announcement per publisher/type/date even when two official listing
        # pages point to the same event under different URL conventions.
        old = unique.get(row["episode_id"])
        if old is None or (len(row["text"]), row["source_url"]) > (
            len(old["text"]),
            old["source_url"],
        ):
            unique[row["episode_id"]] = row
    rows = sorted(unique.values(), key=lambda r: (r["published_at"], r["episode_id"]))
    entries = []
    (args.out / "records").mkdir(exist_ok=True)
    for row in rows:
        raw = (json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n").encode()
        relative = "records/" + hashlib.sha256(row["episode_id"].encode()).hexdigest() + ".json"
        (args.out / relative).write_bytes(raw)
        entries.append(
            {
                "published_at": row["published_at"],
                "file": relative,
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    index = (json.dumps(entries, sort_keys=True, indent=2) + "\n").encode()
    (args.out / "index.json").write_bytes(index)
    referenced = {entry["file"] for entry in entries}
    for stale in (args.out / "records").glob("*.json"):
        if stale.relative_to(args.out).as_posix() not in referenced:
            stale.unlink()
    types = Counter(r["event_type"] for r in rows)
    regions = Counter(r["region"] for r in rows)
    manifest = {
        "schema_version": 1,
        "catalog_version": "event-memory-1.0",
        "build_date": datetime.now(UTC).isoformat(),
        "parser_version": 1,
        "feature_schema_version": 1,
        "index_sha256": hashlib.sha256(index).hexdigest(),
        "event_count": len(rows),
        "type_counts": dict(types),
        "region_counts": dict(regions),
        "index_hashes": index_hashes,
        "fed_catalog_index_sha256": hashlib.sha256(
            (args.fed / "index.json").read_bytes()
        ).hexdigest(),
        "source_counts": {"FED": len(fed), "BLS_ECB": len(fetched)},
        "discovered_sources": len(sources),
        "excluded_sources": len(sources) - len(fetched),
        "market_responses_stored": 0,
    }
    (args.out / "catalog_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()

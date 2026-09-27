"""## Executive summary (read this first)

Build a reproducible event-only library from official FOMC historical pages.
Statements use their release date; minutes use the explicitly printed release date,
never their meeting date. Cache raw source bytes outside the repository. No prices,
unit identifiers, later outcomes, transcripts or delayed archival materials are used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bs4 import BeautifulSoup

from qfbench2_track_forecasting.text_evidence import _safe_excerpt
from qfbench2_track_forecasting.v6.fingerprint import interpret, with_delta

BASE = "https://www.federalreserve.gov"
MONTHS = (
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
)


def fetch(url: str, cache: Path) -> bytes:
    name = cache / (hashlib.sha256(url.encode()).hexdigest() + ".html")
    if name.exists():
        return name.read_bytes()
    request = urllib.request.Request(
        url, headers={"User-Agent": "V6 research archive; public FOMC statements"}
    )
    with urllib.request.urlopen(request, timeout=40) as response:
        raw = response.read()
    name.write_bytes(raw)
    return raw


def source_links(year: int, cache: Path) -> list[dict]:
    index_url = (
        f"{BASE}/monetarypolicy/fomchistorical{year}.htm"
        if year <= 2020
        else f"{BASE}/monetarypolicy/fomccalendars.htm"
    )
    try:
        soup = BeautifulSoup(fetch(index_url, cache), "html.parser")
    except Exception as exc:
        print(f"index unavailable {year}: {type(exc).__name__}", flush=True)
        return []
    records = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        label = a.get_text(" ", strip=True)
        if "#" in href or not href.lower().endswith((".htm", ".html", "/")):
            continue
        dates = re.findall(r"(?:19|20)\d{6}", href)
        if not dates:
            continue
        meeting = dates[-1]
        if int(meeting[:4]) != year:
            continue
        if label == "Statement" or (year > 2020 and re.search(r"monetary[0-9]{8}a.htm$", href)):
            released = datetime.strptime(meeting, "%Y%m%d").date().isoformat()
            doc_type = "fomc_statement"
        elif "minutes" in href.lower() or re.search(r"/\d{8}min\.", href, re.I):
            paragraph = a.find_parent("p") if year <= 2020 else a.find_parent("div")
            context = paragraph.get_text(" ", strip=True) if paragraph else ""
            match = re.search(r"Released\s+(" + MONTHS + r"\s+\d{1,2},\s*\d{4})", context, re.I)
            if not match:
                continue
            released = (
                datetime.strptime(re.sub(r"\s+", " ", match[1]), "%B %d, %Y").date().isoformat()
            )
            doc_type = "fomc_minutes"
        else:
            continue
        records.append(
            dict(
                source_url=urljoin(BASE, href),
                published_at=released,
                episode_id=f"FED:{meeting}",
                doc_type=doc_type,
                index_url=index_url,
            )
        )
    return records


def download(source: dict, cache: Path) -> tuple[dict, str] | None:
    try:
        raw = fetch(source["source_url"], cache)
        soup = BeautifulSoup(raw, "html.parser")
        content = soup.find(id="article") or soup.find(id="content") or soup.body or soup
        for el in content.select("script,style,nav,footer,.lastUpdate,.shareDL"):
            el.decompose()
        text = _safe_excerpt(content.get_text(" ", strip=True))
        if len(text) < 200:
            return None
        # Prefer explicit article publication date when present; reject a mismatch.
        time = soup.select_one(".article__time")
        if time:
            match = re.search(MONTHS + r"\s+\d{1,2},\s*\d{4}", time.get_text(" ", strip=True))
            if (
                match
                and datetime.strptime(match[0], "%B %d, %Y").date().isoformat()
                != source["published_at"]
            ):
                raise ValueError("publication date conflict")
        return {
            **source,
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        }, text
    except Exception as exc:
        print(f"document excluded {source['source_url']}: {type(exc).__name__}", flush=True)
        return None


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--cache", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--start", type=int, default=1994)
    p.add_argument("--end", type=int, default=2025)
    args = p.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    args.out.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=6) as pool:
        groups = list(
            pool.map(lambda y: source_links(y, args.cache), range(args.start, args.end + 1))
        )
        sources = {s["source_url"]: s for group in groups for s in group}
        print(f"Discovered {len(sources)} independently dated official documents", flush=True)
        fetched = []
        for i, result in enumerate(pool.map(lambda s: download(s, args.cache), sources.values())):
            if result:
                fetched.append(result)
            if (i + 1) % 50 == 0:
                print(f"Downloaded {i+1}/{len(sources)}", flush=True)
    fetched.sort(key=lambda pair: (pair[0]["published_at"], pair[0]["source_url"]))
    previous = {}
    entries = []
    excluded = 0
    retrieval = datetime.now(UTC).isoformat()
    for source, text in fetched:
        fp = interpret(text, source["published_at"], "Federal Reserve", source["source_url"])
        if fp is None:
            excluded += 1
            continue
        key = source["doc_type"]
        prev = previous.get(key)
        if prev and prev[0] < source["published_at"]:
            fp = with_delta(fp, prev[1])
        previous[key] = (source["published_at"], fp)
        row = {
            **source,
            "text": text,
            "publisher": "Federal Reserve Board",
            "retrieved_at": retrieval,
            "license_basis": (
                "US federal government work; " "Federal Reserve Board official publication"
            ),
            "fingerprint": fp.payload(),
        }
        relative = f"records/{source['published_at']}-{source['source_sha256'][:12]}.json"
        raw = (json.dumps(row, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode()
        path = args.out / relative
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(raw)
        entries.append(
            {
                "published_at": source["published_at"],
                "file": relative,
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    index = {
        "schema_version": 1,
        "description": "Official event features only; no panel values or outcomes.",
        "sources_discovered": len(sources),
        "documents_downloaded": len(fetched),
        "documents_without_qualified_event": excluded,
        "records": entries,
    }
    (args.out / "index.json").write_text(json.dumps(index, sort_keys=True, indent=2) + "\n")
    (args.out / "event_sources.json").write_text(
        json.dumps(list(sources.values()), indent=2) + "\n"
    )
    print(f"Catalog has {len(entries)} feature records; {excluded} documents abstained", flush=True)


if __name__ == "__main__":
    main()

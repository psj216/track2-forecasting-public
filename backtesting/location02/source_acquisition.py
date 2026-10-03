"""Executive summary: acquire official original releases, with restartable byte receipts.

This module never imports forecasting labels, fitting or scoring. Enumerate actual
archive entries instead of assuming a quarterly count. A failed transfer leaves a
receipt and stops; completed exact-byte files are reused.
"""
import argparse
import csv
import hashlib
import json
import re
import subprocess
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "backtesting/location02/results"
ARCHIVE_URL = "https://www.ecb.europa.eu/stats/ecb_surveys/survey_of_professional_forecasters/html/all-releases.en.html"
SUMMARY = "Official ECB release acquisition only; no forecasting outcomes, fitting or scores."


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, data):
    Path(path).write_text(json.dumps({"executive_summary": SUMMARY, **data}, indent=2, allow_nan=False) + "\n")


def write_csv(path, rows, columns=None):
    with Path(path).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns or list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def enumerate_archive(body):
    soup = BeautifulSoup(body, "html.parser")
    rows = []
    for entry in soup.find_all("dd"):
        anchor = entry.select_one(".title a")
        if not anchor:
            continue
        match = re.search(r"spf(20\d\d)q([1-4])", anchor["href"], re.I)
        if not match or not 2015 <= int(match[1]) <= 2024:
            continue
        date_entry = entry.find_previous_sibling("dt")
        if date_entry is None:
            raise ValueError("Official archive publication date absent")
        date_text = date_entry.get_text(" ", strip=True)
        release_date = datetime.strptime(date_text, "%d %B %Y").date().isoformat()
        pdf = entry.select_one("a.pdf")
        primary = urljoin(ARCHIVE_URL, anchor["href"])
        rows.append({"round_id": match[1] + "Q" + match[2], "year": int(match[1]),
                     "quarter": int(match[2]), "publication_date": release_date,
                     "publication_evidence": "Dated official archive entry: " + date_text,
                     "archive_url": ARCHIVE_URL, "original_url": primary,
                     "pdf_url": urljoin(ARCHIVE_URL, pdf["href"]) if pdf else "",
                     "html_url": primary if ".html" in primary else ""})
    identifiers = [row["round_id"] for row in rows]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Duplicate official round")
    if not rows:
        raise ValueError("Empty official release universe")
    return sorted(rows, key=lambda row: (row["publication_date"], row["round_id"]))


def fetch(url, cache, name):
    if urlsplit(url).hostname != "www.ecb.europa.eu":
        raise ValueError("Only official ECB bytes are admitted")
    target = cache / name
    receipt_path = cache / (name + ".receipt.json")
    if target.exists() and receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if receipt.get("status") == "OK" and receipt.get("sha256") == digest(target):
            return receipt
        raise ValueError("Existing receipt/hash mismatch: " + name)
    started = time.monotonic()
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (bounded academic source audit)"})
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read(8_000_001)
            resolved = response.url
            code = response.status
        if len(content) > 8_000_000 or not content:
            raise ValueError("Invalid bounded response length")
        if urlsplit(resolved).hostname != "www.ecb.europa.eu":
            raise ValueError("Nonofficial redirect")
        temporary = target.with_suffix(target.suffix + ".partial")
        temporary.write_bytes(content)
        temporary.replace(target)
        receipt = {"url": url, "resolved_url": resolved, "status": "OK", "http_status": code,
                   "retrieved_at": datetime.now(timezone.utc).isoformat(), "bytes": len(content),
                   "sha256": digest(target), "elapsed_seconds": time.monotonic() - started,
                   "representation": "Original HTTP bytes retrieved now; not immutable historical vintage proof"}
        dump(receipt_path, receipt)
        return receipt
    except Exception as error:
        dump(receipt_path, {"url": url, "status": "FAILED", "error": str(error),
                            "retrieved_at": datetime.now(timezone.utc).isoformat()})
        raise


def acquire(private, start, stop):
    cache = private / "source_cache"
    cache.mkdir(parents=True, exist_ok=True)
    index = cache / "all-releases.html"
    if not index.exists():
        fetch(ARCHIVE_URL, cache, index.name)
    rows = enumerate_archive(index.read_bytes())
    write_csv(OUT / "ecb_release_universe.csv", rows)
    dump(OUT / "ecb_pit_dataset_manifest.json", {"stage": "ACQUISITION", "rounds_enumerated": len(rows),
         "archive_sha256": digest(index), "admitted_period": ["2015-01-23", "2024-10-18"],
         "no_current_csv_or_microdata": True, "DATASET_READY": False})
    started = time.monotonic()
    def one_round(row):
        for kind in ("pdf", "html"):
            if row[kind + "_url"]:
                fetch(row[kind + "_url"], cache, row["round_id"] + "." + kind)
        return row

    stop = min(stop, len(rows))
    with ThreadPoolExecutor(max_workers=4) as pool:
      futures = [pool.submit(one_round, row) for row in rows[start:stop]]
      for done, future in enumerate(as_completed(futures), 1):
        row = future.result()
        completed = [r["round_id"] for r in rows if all(not r[k + "_url"] or
                     (cache / (r["round_id"] + "." + k)).exists() for k in ("pdf", "html"))]
        status_path = ROOT / "backtesting/location02/STATUS.json"
        status = json.loads(status_path.read_text())
        status.update(current_stage="source_acquisition", source_rounds_completed=len(completed),
                      completed_source_rounds=completed,
                      source_rounds_total=len(rows), last_successful_artifact="source_cache/" + row["round_id"],
                      last_update_time=datetime.now(timezone.utc).isoformat())
        dump(status_path, status)
        print(f"stage=ECB_acquisition completed={len(completed)}/{len(rows)} chunk={done}/{stop-start} elapsed={time.monotonic()-started:.1f}s round={row['round_id']} output={cache}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--private", type=Path, required=True)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--stop", type=int, default=0)
    args = parser.parse_args()
    acquire(args.private, args.start, args.stop)

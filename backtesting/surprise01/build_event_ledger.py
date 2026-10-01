"""## Executive summary (read this first)

Extract latest-period first-release values from archived agency releases only.
Record failures before any market evaluation. Future revisions are never consulted.
"""

import argparse
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
import io
import json
from pathlib import Path
import re
import subprocess
import tempfile
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
import numpy as np
from pypdf import PdfReader

from qfbench2_track_forecasting.surprise01.event_schema import ReleaseEvent
from qfbench2_track_forecasting.surprise01.surprise import standardized

MONTHS = "January February March April May June July August September October November December".split()
MONTH = "(" + "|".join(MONTHS) + ")"
NUMBER = r"[-+]?\d*\.?\d+"


def signed(word, value):
    negative = any(w in word.lower() for w in ("declin", "fell", "decreas", "down", "drop"))
    return -abs(float(value)) if negative else float(value)


def text_from_bytes(raw, path):
    if path.endswith(".pdf") or raw.startswith(b"%PDF"):
        text = PdfReader(io.BytesIO(raw)).pages[0].extract_text()
        if len(text.strip()) < 100:
            result = subprocess.run(["pdftotext", "-f", "1", "-l", "1", "-layout", "-", "-"],
                                    input=raw, capture_output=True, check=True)
            text = result.stdout.decode("utf-8", errors="replace")
        if len(text.strip()) < 100:
            # Some original Census releases are scanned images. OCR is an
            # acquisition step; retain the scan and text together outside Git.
            cached = Path(path + ".ocr.txt")
            if cached.exists():
                text = cached.read_text()
            else:
                with tempfile.TemporaryDirectory() as directory:
                    stem = str(Path(directory) / "page")
                    subprocess.run(["pdftoppm", "-f", "1", "-l", "1", "-r", "180", "-png", "-singlefile", path, stem],
                                   check=True, capture_output=True, timeout=30)
                    result = subprocess.run(["tesseract", stem + ".png", "stdout", "--psm", "6"],
                                            check=True, capture_output=True, timeout=30)
                    text = result.stdout.decode("utf-8", errors="replace")
                    cached.write_text(text)
        return text, None
    if path.endswith(".txt"):
        return raw.decode("utf-8", errors="replace"), None
    soup = BeautifulSoup(raw, "html.parser")
    return soup.get_text(" ", strip=True), soup


def cpi_values(text, soup):
    if soup:
        for table in soup.find_all("table"):
            if "All items less food and energy" not in table.get_text(" ", strip=True):
                continue
            result = {}
            for row in table.find_all("tr"):
                cells = row.find_all(["th", "td"], recursive=False)
                if not cells:
                    continue
                label = cells[0].get_text(" ", strip=True)
                if label not in {"All items", "All items less food and energy"}:
                    continue
                vals = []
                for cell in cells[1:]:
                    try:
                        vals.append(float(cell.get_text(" ", strip=True).replace("−", "-")))
                    except ValueError:
                        pass
                if len(vals) >= 3:
                    offset = 3 if "Compound annual" in table.get_text(" ", strip=True) else 2
                    result["CPI" if label == "All items" else "Core CPI"] = vals[-offset]
            if len(result) == 2:
                return result
    # Older official archives retain Table A as fixed-width text, not HTML
    # cells. Its last columns are annual rates, never the monthly target.
    table = re.search(r"Table A\.(.*?)(?:The food|Consumer Price Index Data|Year in Review|Footnotes|$)", text, re.S | re.I)
    if table:
        t = re.sub(r"\s+", " ", table[1])
        result = {}
        for key, label in (("CPI", r"All items\.*"),
                           ("Core CPI", r"All items less\s+food\s+(?:and|&)\s+energy\.*")):
            row = re.search(label + r"\s+((?:" + NUMBER + r"\s+){7,9})", t, re.I)
            if row:
                vals = [float(v) for v in row[1].split()]
                offset = 3 if "Compound" in t[:1800] else 2
                if len(vals) in (8, 9):
                    result[key] = vals[-offset]
        if len(result) == 2:
            return result
    t = re.sub(r"\s+", " ", text)
    verbs = r"(rose|increased|declined|decreased|fell|advanced|dropped)"
    headline = re.search(r"(?:On a seasonally adjusted basis,? the CPI-U|seasonally adjusted CPI-U) " + verbs + r" (" + NUMBER + r") percent", t, re.I)
    if not headline:
        headline = re.search(r"Consumer Price Index for All Urban Consumers \(CPI-U\) " + verbs + r" (" + NUMBER + r") percent[^.]{0,60}seasonally adjusted", t, re.I)
    core = re.search(r"(?:Excluding food and energy,? the CPI-U|index for all items less food and energy|index for all items excluding food and energy|index for all items less food and energy \(core\)) " + verbs + r" (" + NUMBER + r") percent", t, re.I)
    if not headline or not core:
        raise ValueError("CPI first-release monthly value not unambiguously parsed")
    return {"CPI": signed(headline[1], headline[2]), "Core CPI": signed(core[1], core[2])}


def employment_values(text):
    t = re.sub(r"\s+", " ", text)
    p = re.search(r"(?:THE )?EMPLOYMENT SITUATION\s*[-:]*\s*" + MONTH, t, re.I)
    if not p:
        raise ValueError("Employment release title absent")
    t = t[p.start():]
    verbs = r"(rose|increased|declined|decreased|fell|dropped|was down|was up|edged up|edged down|grew)"
    pay = re.search(r"(?:total )?(?:nonfarm payroll employment|payroll employment|nonfarm employment) " + verbs + r"(?: by| a further| another)? (" + NUMBER + r"(?:,\d{3})*)\s*(million|thousand)?", t, re.I)
    if pay:
        value = float(pay[2].replace(",", ""))
        if pay[3] and pay[3].lower() == "million":
            value *= 1000
        elif not pay[3]:
            value /= 1000
        payroll = signed(pay[1], value)
    else:
        stable = re.search(r"(?:nonfarm payroll employment|payroll employment|nonfarm employment|nonfarm payroll)[^;]{0,130}?\((" + NUMBER + r"(?:,\d{3})*)\)", t[:18000], re.I)
        if stable:
            payroll = float(stable[1].replace(",", "")) / 1000
        else:
            row = re.search(r"Nonfarm employment\.{2,}([^A-Za-z]*?)(?=Goods-producing)", t, re.I)
            if not row:
                # The summary table explicitly labels its preliminary monthly
                # employment change; this is the printed first-release change.
                row = re.search(r"Nonfarm employment\.{2,}([|\spc\-\d,]+)(?=Goods-producing)", t, re.I)
            if not row:
                raise ValueError("Payroll first estimate not unambiguously parsed")
            nums = re.findall(r"[-+]?\d[\d,]*", row[1])
            payroll = float(nums[-1].replace(",", ""))
    ur = re.search(r"unemployment rate.{0,160}?percent", t, re.I)
    if not ur:
        raise ValueError("Unemployment rate absent")
    values = re.findall(r"\d+\.\d+", ur[0])
    if not values:
        raise ValueError("Unemployment numeric first estimate absent")
    return {"Payrolls": payroll, "Unemployment": float(values[-1])}


def retail_value(text):
    t = re.sub(r"\s+", " ", text)
    for old, new in (("in crease", "increase"), ("incr ease", "increase"),
                     ("de crease", "decrease"), ("retail a nd", "retail and"),
                     ("retai l", "retail"), ("est imates", "estimates"),
                     ("ad vance", "advance"), ("adv ance", "advance"),
                     ("estimates cf", "estimates of")):
        t = t.replace(old, new)
    start = re.search(r"Advance estimates of U\.S[.,] retail and food services sales", t, re.I)
    if not start:
        raise ValueError("Advance retail sales statement absent")
    excerpt = t[start.start():start.start() + 900]
    end = re.search(r"from the previous month|from (?:January|February|March|April|May|June|July|August|September|October|November|December)", excerpt, re.I)
    if end:
        excerpt = excerpt[:end.start()]
    value = re.search(r"(up|down|increase of|decrease of|increased|decreased|rose|fell)\s+(" + NUMBER + r")\s*(?:percent|%)", excerpt, re.I)
    if value:
        return signed(value[1], value[2])
    if "unchanged" in excerpt.lower():
        return 0.0
    raise ValueError("Retail advance monthly change absent")


def ip_value(text):
    t = re.sub(r"\s+", " ", text)
    t = t.replace("\ufffd", " ")
    verbs = r"(rose|increased|declined|decreased|fell|dropped|moved down|moved up|edged down|edged up|advanced|gained|expanded|rebounded|fell back)"
    subject = r"(?:Total )?industrial (?:production|output)(?: \(IP\))?(?: and manufacturing production both)?"
    p = re.search(subject + r" " + verbs + r" (" + NUMBER + r")\s+percent (?:in|for) " + MONTH, t, re.I)
    if p:
        return signed(p[1], p[2])
    p = re.search(r"In " + MONTH + r",? " + subject + r" " + verbs + r" (" + NUMBER + r") percent", t, re.I)
    if p:
        return signed(p[2], p[3])
    stable = re.search(r"(?:Total )?industrial production(?: \(IP\))? (?:was )?(?:unchanged|remained unchanged|held steady|stalled) in " + MONTH, t, re.I)
    if stable:
        return 0.0
    # Qualitative "little changed" is not necessarily zero.
    row = re.search(r"Total index\s+((?:[-+.\d]+\s+){8,16})(?:Previous estimates|Major market)", t, re.I)
    if row:
        values = row[1].split()
        if len(values) in (9, 13, 15):
            return float(values[-2])
    # Original fixed-width G.17 summary separates monthly percent changes
    # from index levels and year-on-year growth in pipe-delimited columns.
    row = re.search(r"Total index\s*\|[^|]+\|\s*([-+.\d\s]+)\|", t, re.I)
    if row:
        values = row[1].split()
        if 3 <= len(values) <= 7:
            return float(values[-1])
    raise ValueError("IP first-release monthly change absent")


def parse_archive(row):
    raw = Path(row["path"]).read_bytes()
    text, soup = text_from_bytes(raw, row["path"])
    text = text.replace("−", "-").replace("\u2011", "-")
    if row["kind"] in {"cpi", "employment"}:
        title = re.search(r"(?:CONSUMER PRICE INDEX|THE EMPLOYMENT SITUATION)\s*[-:–]*\s*" + MONTH + r"\s+(\d{4})", re.sub(r"\s+", " ", text), re.I)
        if not title:
            raise ValueError("Reference-period title not found")
        reference = f"{title[2]}-{MONTHS.index(title[1].capitalize())+1:02d}"
        date = row["key"]
        values = cpi_values(text, soup) if row["kind"] == "cpi" else employment_values(text)
        source = "BLS"
    elif row["kind"] == "retail":
        reference = row["key"]
        found = re.search(MONTH + r"\s+(\d{1,2}),?\s+(\d{4})", re.sub(r"\s+", " ", text), re.I)
        if not found:
            raise ValueError("Retail release date absent")
        date = f"{found[3]}-{MONTHS.index(found[1].capitalize())+1:02d}-{int(found[2]):02d}"
        values, source = {"Retail Sales": retail_value(text)}, "U.S. Census Bureau"
    else:
        date = row["key"]
        yyyy, month, _ = map(int, date.split("-"))
        reference = f"{yyyy if month>1 else yyyy-1}-{month-1 if month>1 else 12:02d}"
        values, source = {"Industrial Production": ip_value(text)}, "Federal Reserve Board"
    compact = re.sub(r"\s+", " ", text)
    # Only an explicit embargo/release header establishes current timing.
    # A next-release time elsewhere in the archive cannot establish it.
    header = re.search(r"(?:embargoed until|FOR RELEASE AT|FOR IMMEDIATE RELEASE|FOR WIRE TRANSMISSION|For release at).{0,130}?(8:30|9:15)\s*(?:a\.?m\.?|AM)", compact, re.I)
    time = {"8:30": "08:30", "9:15": "09:15"}.get(header[1]) if header else None
    timestamp = datetime.fromisoformat(date + "T" + time).replace(tzinfo=ZoneInfo("America/New_York")).isoformat() if time else None
    return [ReleaseEvent(event_id=row["kind"] + ":" + date, event_type=k,
                         reference_period=reference, release_date=date,
                         release_timestamp=timestamp, actual_first_release=float(v),
                         expected_value=None, source=source, source_url=row["url"],
                         retrieval_date="2026-10-01",
                         unit="thousand_persons" if k == "Payrolls" else "percentage_points").validate().as_dict()
            for k, v in values.items() if date < "2025-01-01"]


def _parse_result(row):
    if row["status"] != "OK":
        return [], {k: row[k] for k in ("kind", "key", "url", "error") if k in row}
    try:
        return parse_archive(row), None
    except Exception as e:
        return [], {"kind": row["kind"], "key": row["key"], "url": row["url"], "error": str(e)}


def build(raw_manifest, output, audit_out):
    raw = json.loads(Path(raw_manifest).read_text())
    events, errors = [], []
    with ProcessPoolExecutor(max_workers=6) as pool:
        for i, (parsed, error) in enumerate(pool.map(_parse_result, raw)):
            events.extend(parsed)
            if error:
                errors.append(error)
            if i % 100 == 0:
                print(f"parsed {i+1}/{len(raw)} source archives", flush=True)
    events.sort(key=lambda e: (e["release_date"], e["event_type"]))
    past, history = {}, {}
    for e in events:
        k = e["event_type"]
        previous = past.get(k)
        e["expected_value"] = previous
        error = e["actual_first_release"] - previous if previous is not None else None
        e["raw_innovation"] = error
        e["standardized_surprise"] = standardized(error, history.get(k, [])) if error is not None else None
        if error is not None:
            history.setdefault(k, []).append(error)
        past[k] = e["actual_first_release"]
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(events, indent=2, allow_nan=False) + "\n")
    Path(audit_out).write_text(json.dumps(errors, indent=2) + "\n")
    return {"events": len(events), "parse_errors": len(errors),
            "family_counts": {k: sum(e["event_type"] == k for e in events) for k in sorted(history)},
            "eligible_events": sum(e["standardized_surprise"] is not None and e["release_date"] >= "2001-01-01" for e in events)}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--raw-manifest", required=True)
    p.add_argument("--private-out", required=True)
    p.add_argument("--audit-out", required=True)
    a = p.parse_args()
    print(json.dumps(build(a.raw_manifest, a.private_out, a.audit_out), indent=2))

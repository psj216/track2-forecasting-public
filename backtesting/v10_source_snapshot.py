"""## Executive summary (read this first)

Download full public source series outside this repository for V10-DATA.
Record byte hashes and coverage without committing post-card outcomes. These
current historical files are not real-time vintages and cannot pass the FINAL
as-of gate by themselves. ALFRED vintage observations need a registered key.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import urllib.parse
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path

FRED_SERIES = {
    "DEXUSAL": ("FX", "AUD", "USD per AUD"),
    "DEXCAUS": ("FX", "CAD", "CAD per USD"),
    "DEXSZUS": ("FX", "CHF", "CHF per USD"),
    "DEXUSEU": ("FX", "EUR", "USD per EUR"),
    "DEXJPUS": ("FX", "JPY", "JPY per USD"),
    "DEXDNUS": ("FX", "DKK", "DKK per USD"),
    "DGS2": ("rates", "UST_2Y", "percent per annum"),
    "DGS10": ("rates", "UST_10Y", "percent per annum"),
    "CPIAUCSL": ("macro", "CPI_ALL", "1982-84 = 100"),
    "UNRATE": ("macro", "UNRATE", "percent U-3"),
}
FRENCH_FILES = {
    "MKT": "F-F_Research_Data_Factors_daily_CSV.zip",
    "MOM": "F-F_Momentum_Factor_daily_CSV.zip",
}
FRED_GRAPH = "https://fred.stlouisfed.org/graph/fredgraph.csv"
FRENCH_BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
USER_AGENT = "V10-DATA research snapshot (source integrity and as-of audit)"


def _fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=45) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status} for {url}")
        return response.read()


def _fred_coverage(data: bytes, expected_series: str) -> dict:
    text = data.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    if rows[0] not in (["DATE", expected_series], ["observation_date", expected_series]):
        raise ValueError(f"unexpected FRED graph header: {rows[0]}")
    dated = [(day, value) for day, value in rows[1:] if re.fullmatch(r"\d{4}-\d\d-\d\d", day)]
    observed = [day for day, value in dated if value not in ("", ".")]
    if not dated or not observed:
        raise ValueError(f"no usable dates for {expected_series}")
    return {"first_date": dated[0][0], "last_date": dated[-1][0],
            "first_observed": observed[0], "last_observed": observed[-1],
            "date_rows": len(dated), "nonmissing_rows": len(observed)}


def _french_coverage(data: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        if len(names) != 1:
            raise ValueError(f"unexpected French archive members: {names}")
        text = archive.read(names[0]).decode("latin-1")
    # Both daily source files have a delimited YYYYMMDD first field. The
    # monthly and annual tables in some archives are ignored here.
    dates = [match.group(1) for line in text.splitlines()
             if (match := re.match(r"^\s*(\d{8})\s*,", line))]
    if not dates:
        raise ValueError("no daily factor rows")
    return {"archive_member": names[0], "first_observed": dates[0],
            "last_observed": dates[-1], "daily_rows": len(dates)}


def snapshot(out: Path, through: str) -> dict:
    out = out.resolve()
    if out == Path.cwd().resolve() or Path.cwd().resolve() in out.parents:
        raise ValueError("raw source data must stay outside the public repository")
    out.mkdir(parents=True, exist_ok=True)
    sources = []
    for series, (group, target, units) in FRED_SERIES.items():
        query = urllib.parse.urlencode({"id": series, "cosd": "1900-01-01", "coed": through})
        url = FRED_GRAPH + "?" + query
        raw = _fetch(url)
        coverage = _fred_coverage(raw, series)
        path = out / f"fred_{series}.csv"
        path.write_bytes(raw)
        sources.append({"series": series, "group": group, "target": target,
                        "units": units, "url": url, "file": path.name,
                        "sha256": hashlib.sha256(raw).hexdigest(),
                        "bytes": len(raw), **coverage,
                        "reliability": "current_history_only; as-of vintage not established"})
        print(f"{series}: {coverage['first_observed']}..{coverage['last_observed']}", flush=True)
    for target, filename in FRENCH_FILES.items():
        url = FRENCH_BASE + filename
        raw = _fetch(url)
        coverage = _french_coverage(raw)
        path = out / filename
        path.write_bytes(raw)
        sources.append({"series": filename, "group": "factor", "target": target,
                        "units": "daily percent simple return; transform must be audited",
                        "url": url, "file": path.name,
                        "sha256": hashlib.sha256(raw).hexdigest(),
                        "bytes": len(raw), **coverage,
                        "reliability": (
                            "secondary only; updated historical returns, no as-of snapshot"
                        )})
        print(f"{target}: {coverage['first_observed']}..{coverage['last_observed']}", flush=True)
    metadata = {
        "## Executive summary (read this first)": (
            "Public source bytes and coverage; not an as-of safe validation benchmark."
        ),
        "snapshot_utc": datetime.now(UTC).isoformat(),
        "fred_through_requested": through,
        "factor_archives_can_extend_after_fred_through": True,
        "fred_api_key_configured": bool(os.getenv("FRED_API_KEY")),
        "alfred_vintage_observations_fetched": False,
        "sources": sources,
        "limits": [
            "Current historical files can contain revised values and should not be used "
            "as real-time feature vintages.",
            "Neither factor archive is a point-in-time downloadable snapshot.",
            "A registered FRED API key is required for ALFRED realtime_start/realtime_end.",
        ],
    }
    (out / "source_snapshot.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--through", default="2025-12-31")
    args = parser.parse_args()
    snapshot(args.out, args.through)


if __name__ == "__main__":
    main()

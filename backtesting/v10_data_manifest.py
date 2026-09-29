"""## Executive summary (read this first)

Freeze provisional F1 shadow origins from independently downloaded source date
indexes. Exclude all previously scored market-year episodes, not just exact
origin dates. Inspect date availability only; never score, fit a model, or open
FINAL outcomes. Current-history and revised factor sources cannot qualify as
an as-of-safe FINAL benchmark without archived vintages.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import tomllib
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from backtesting.universe_backtest import (
    _observation_period_business_days,
    cutoff_dates,
    load_universe,
)
from backtesting.v9_manifest import _interval
from backtesting.v10_source_snapshot import FRED_SERIES

SOURCES = {target: series for series, (_, target, _) in FRED_SERIES.items()}
SOURCES.update({"MKT": "F-F_Research_Data_Factors_daily_CSV.zip",
                "MOM": "F-F_Momentum_Factor_daily_CSV.zip"})
PREVIOUS_CUTOFF_COUNTS = (3, 5, 6, 8, 12)
MIN_YEARS_PER_SPLIT = 5
MIN_TEMPLATES_PER_SPLIT = 3
SUMMARY = "Provisional F1 external-source dates only; FINAL remains unscored."


def _hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _source_dates(raw: Path, series: str) -> pd.DatetimeIndex:
    if series.endswith(".zip"):
        with zipfile.ZipFile(raw / series) as archive:
            names = archive.namelist()
            if len(names) != 1:
                raise ValueError("unexpected factor archive")
            lines = archive.read(names[0]).decode("latin-1").splitlines()
        dates = [match.group(1) for line in lines
                 if (match := re.match(r"^\s*(\d{8})\s*,", line))]
        return pd.DatetimeIndex(pd.to_datetime(dates, format="%Y%m%d"))
    frame = pd.read_csv(raw / f"fred_{series}.csv", dtype=str)
    if list(frame.columns) not in (["DATE", series], ["observation_date", series]):
        raise ValueError(f"unexpected FRED source {series}")
    return pd.DatetimeIndex(pd.to_datetime(frame.loc[frame[series].ne(".") &
                                                      frame[series].notna(), frame.columns[0]]))


def _exposed_years(root: Path) -> tuple[set[int], dict]:
    v9 = json.loads((root / "backtesting/v9_frozen_origins.json").read_text())
    v10 = json.loads((root / "backtesting/v10_shadow/v10_shadow_audit.json").read_text())
    exposed: set[int] = set()
    for row in v9["entries"]:
        if row["split"] != "purged":
            exposed.update(range(int(row["cutoff"][:4]), int(row["end"][:4]) + 1))
    # The legacy date protocols were scored too. Their exact origin lists are
    # reconstructed from the frozen public card histories, but no outcomes.
    legacy: set[int] = set()
    for case in load_universe(root):
        aligned = pd.DataFrame(case.histories).dropna()
        dates = pd.DatetimeIndex(pd.to_datetime(aligned.index))
        period = _observation_period_business_days(aligned)
        for count in PREVIOUS_CUTOFF_COUNTS:
            for day in cutoff_dates(case, count):
                start, end = _interval(dates, int(dates.get_loc(pd.Timestamp(day))),
                                       max(case.horizons), period)
                if end < len(dates):
                    legacy.update(range(dates[start].year, dates[end].year + 1))
    exposed |= legacy
    inspected_only = set()
    with (root / "backtesting/v10_shadow/v10_shadow_manifest.csv").open() as handle:
        rows = csv.DictReader(line for line in handle if not line.startswith("#"))
        for row in rows:
            inspected_only.update(range(int(row["origin"][:4]),
                                        int(row["evaluation_end"][:4]) + 1))
    exposed |= inspected_only
    return exposed, {"v9_manifest_rows_sha256": v9["entries_sha256"],
                     "v10_shadow_rows_sha256": v10["manifest_rows_sha256"],
                     "legacy_years": sorted(legacy),
                     "v9_scored_and_v10_inspected_years": sorted(exposed),
                     "v6_v7_event_origin_ledger_complete": False}


def _split(year: int) -> str:
    if 1971 <= year <= 1980:
        return "FIT"
    if year == 1981:
        return "PURGED_EMBARGO"
    if 1982 <= year <= 1987:
        return "SELECT"
    if year == 1988:
        return "PURGED_EMBARGO"
    if 1989 <= year <= 1993:
        return "FINAL"
    if year == 2025:
        return "PROSPECTIVE_SINGLE_YEAR"
    return "OUTSIDE_PROVISIONAL_SPLIT"


def build(root: Path, raw: Path) -> tuple[list[dict], dict]:
    root, raw = root.resolve(), raw.resolve()
    if root == raw or root in raw.parents:
        raise ValueError("raw source data cannot live inside the public repository")
    source = json.loads((raw / "source_snapshot.json").read_text())
    for item in source["sources"]:
        actual = hashlib.sha256((raw / item["file"]).read_bytes()).hexdigest()
        if actual != item["sha256"]:
            raise ValueError(f"source bytes changed for {item['series']}")
    exposed, exposure = _exposed_years(root)
    all_dates = {series: _source_dates(raw, series) for series in sorted(set(SOURCES.values()))}
    rows: list[dict] = []
    excluded: Counter[str] = Counter()
    templates = []
    for path in sorted((root / "units").glob("t2-F1-*/card.toml")):
        card = tomllib.loads(path.read_text())
        targets = card["targets"]
        assets = tuple(targets["asset_ids"])
        series = [SOURCES[asset] for asset in assets]
        frequency = targets.get("target_frequency", "daily")
        grade = ("secondary_revised_factor" if any(s.endswith(".zip") for s in series)
                 else "vintage_required_monthly" if frequency == "monthly"
                 else "provisional_current_history_market")
        templates.append({"unit_id": path.parent.name, "assets": assets,
                          "horizons": tuple(targets["horizons"]),
                          "frequency": frequency, "target_type": targets["target_type"],
                          "source_series": series, "reliability": grade})
        dates = all_dates[series[0]]
        for next_series in series[1:]:
            dates = dates.intersection(all_dates[next_series])
        dates = dates[(dates.year >= 1971) & (dates.year <= 2025)]
        if frequency == "monthly":
            excluded["monthly_release_vintage_missing"] += 1
            continue
        for year in sorted(set(dates.year)):
            if year in exposed:
                excluded["prior_market_episode_year"] += 1
                continue
            split = _split(year)
            if split not in ("FIT", "SELECT", "FINAL", "PROSPECTIVE_SINGLE_YEAR"):
                excluded[split] += 1
                continue
            # Only dates and missingness determine the forecast origin. The
            # longest result window must close within this market-year episode.
            options = []
            for pos in range(140, len(dates) - max(targets["horizons"])):
                if dates[pos].year != year:
                    continue
                end = dates[pos + max(targets["horizons"])]
                if end.year == year:
                    options.append((str(dates[pos].date()), str(end.date())))
            if not options:
                excluded["insufficient_history_or_full_horizon"] += 1
                continue
            origin, end = min(options, key=lambda pair: (_hash([
                path.parent.name, series, targets["horizons"], pair[0]]), pair[0]))
            rows.append({
                "template_unit_id": path.parent.name,
                "family": "T2-F1", "assets": ";".join(assets),
                "horizons_bd": ";".join(map(str, targets["horizons"])),
                "target_type": targets["target_type"], "frequency": frequency,
                "single_cell": int(len(assets) * len(targets["horizons"]) == 1),
                "source_series": ";".join(series), "reliability": grade,
                "origin": origin, "evaluation_end": end,
                "episode_year": year, "split": split,
            })
    rows.sort(key=lambda row: (row["origin"], row["template_unit_id"]))
    by = defaultdict(lambda: {"origins": 0, "templates": set(), "years": set()})
    for row in rows:
        group = by[(row["reliability"], row["split"])]
        group["origins"] += 1
        group["templates"].add(row["template_unit_id"])
        group["years"].add(row["episode_year"])
        if row["episode_year"] in exposed:
            raise AssertionError("exposed market episode in new manifest")
        if row["evaluation_end"][:4] != row["origin"][:4]:
            raise AssertionError("forecast horizon crosses episode year")
    summary = [{"reliability": grade, "split": split,
                "origins": group["origins"], "templates": len(group["templates"]),
                "episode_years": sorted(group["years"])}
               for (grade, split), group in sorted(by.items())]
    strictly_eligible = [row for row in rows if row["reliability"] == "archived_asof_vintage"]
    strict_split = {split: {
        "episode_years": len({row["episode_year"] for row in strictly_eligible
                              if row["split"] == split}),
        "templates": len({row["template_unit_id"] for row in strictly_eligible
                          if row["split"] == split}),
    } for split in ("SELECT", "FINAL")}
    gate_pass = all(
        counts["episode_years"] >= MIN_YEARS_PER_SPLIT
        and counts["templates"] >= MIN_TEMPLATES_PER_SPLIT
        for counts in strict_split.values()
    ) and len(strictly_eligible) > 0
    audit = {
        "## Executive summary (read this first)": SUMMARY,
        "protocol": "v10-data-external-dates-1",
        "outcome_magnitudes_or_scores_used": False,
        "source_snapshot_sha256": hashlib.sha256(
            (raw / "source_snapshot.json").read_bytes()).hexdigest(),
        "exposure": exposure,
        "exposed_market_years": sorted(exposed),
        "safe_years_in_2000_2025": sorted(set(range(2000, 2026)) - exposed),
        "pre1994_provisional_split": {
            "FIT": "1971-1980", "embargo_1": 1981, "SELECT": "1982-1987",
            "embargo_2": 1988, "FINAL": "1989-1993", "prospective": 2025},
        "template_count": len(templates),
        "source_grade_counts": dict(Counter(template["reliability"] for template in templates)),
        "excluded_template_years": dict(sorted(excluded.items())),
        "coverage": summary,
        "rows_sha256": _hash(rows),
        "strictly_eligible_asof_origin_count": len(strictly_eligible),
        "strict_split_counts": strict_split,
        "gate": "PASS" if gate_pass else "FAIL: independent as-of-safe F1 validation insufficient",
        "blocking_reasons": [
            "1994-2024 market-year episodes already exposed by V9 and legacy studies; "
            "2000-2025 has at most one remaining year.",
            "No archived as-of snapshots are available for current-history H.10/H.15 files.",
            "CPI/UNRATE ALFRED vintage retrieval requires a registered FRED API key.",
            "French factor files reconstruct history and remain secondary without archives.",
            "An exhaustive V6/V7 event-origin interval ledger is unavailable.",
            "Pre-1994 provisional splits omit EUR and cannot represent all F1 strata.",
        ],
    }
    return rows, audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("backtesting/v10_data"))
    args = parser.parse_args()
    rows, audit = build(args.root, args.sources)
    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / "v10_data_shadow_manifest.csv"
    with path.open("w", newline="") as handle:
        handle.write("# ## Executive summary (read this first): " + SUMMARY + "\n")
        writer = csv.DictWriter(handle, lineterminator="\n", fieldnames=(
            "template_unit_id", "family", "assets", "horizons_bd", "target_type",
            "frequency", "single_cell", "source_series", "reliability", "origin",
            "evaluation_end", "episode_year", "split"))
        writer.writeheader()
        writer.writerows(rows)
    audit["manifest_file_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (args.out / "v10_data_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps({"gate": audit["gate"], "rows": len(rows),
                      "safe_years_2000_2025": audit["safe_years_in_2000_2025"],
                      "coverage": audit["coverage"],
                      "checksum": audit["manifest_file_sha256"]}, indent=2))


if __name__ == "__main__":
    main()

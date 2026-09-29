"""## Executive summary (read this first)

Audit whether a fresh, date-only Track 2 shadow benchmark exists. This program
uses panel dates and non-null masks, never realized magnitudes or scores.
It excludes previously evaluated
same-card horizons, freezes deterministic candidate origins, and keeps the
FINAL outcomes closed. A sparse family makes the benchmark inadmissible.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from backtesting.universe_backtest import (
    _observation_period_business_days,
    cutoff_dates,
    load_universe,
)
from backtesting.v9_manifest import _interval, _overlaps, verify

PREVIOUS_CUTOFF_COUNTS = (3, 5, 6, 8, 12)
V9_MANIFEST = Path("backtesting/v9_frozen_origins.json")
SELECT_START = "2010-01-01"
FINAL_START = "2018-01-01"
EMBARGO_YEARS = (2009, 2017)
MIN_EPISODE_YEARS = 5
MIN_CARDS = 3
SUMMARY = "Date-only V10 shadow origins; no realized observations or scoring results."


def _split(start: str, end: str) -> str:
    """Calendar years 2009/2017 separate episodes across chronological splits."""
    year = int(start[:4])
    if year <= 2008:
        return "FIT" if end < "2009-01-01" else "PURGED_BOUNDARY"
    if year == 2009:
        return "PURGED_EMBARGO"
    if year <= 2016:
        return "SELECT" if end < "2017-01-01" else "PURGED_BOUNDARY"
    if year == 2017:
        return "PURGED_EMBARGO"
    return "FINAL"


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def build(root: Path) -> tuple[list[dict], dict]:
    v9 = json.loads((root / V9_MANIFEST).read_text())
    verify(v9, root)
    v9_windows: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for entry in v9["entries"]:
        # Include purged V9 entries: their intervals were already inspected to
        # establish eligibility and belong to the research exposure record.
        v9_windows[entry["unit_id"]].append((entry["cutoff"], entry["end"]))

    # The repository also ships one schema exemplar; it is not one of the
    # 103 public evaluation cards and must not inflate family coverage.
    cases = [case for case in load_universe(root) if not case.unit_id.startswith("t2-EXAMPLE-")]
    source_counts: Counter[str] = Counter()
    eligible_counts: Counter[str] = Counter()
    rejected: Counter[str] = Counter()
    manifest: list[dict] = []
    date_indexes: dict[str, str] = {}
    covered_cards: dict[str, set[str]] = defaultdict(set)
    available_years: dict[str, set[int]] = defaultdict(set)
    original_strata: dict[str, set[str]] = defaultdict(set)
    selected_strata: dict[str, set[str]] = defaultdict(set)

    for case in cases:
        source_counts[case.family] += 1
        cells = len(case.assets) * len(case.horizons)
        stratum = f"{case.target_frequency}|{case.target_type}|{cells}"
        original_strata[case.family].add(stratum)
        aligned = pd.DataFrame(case.histories).dropna()
        dates = pd.DatetimeIndex(pd.to_datetime(aligned.index))
        period = _observation_period_business_days(aligned)
        horizon = max(case.horizons)
        date_indexes[case.unit_id] = hashlib.sha256(
            "\n".join(str(day.date()) for day in dates).encode()
        ).hexdigest()
        prior = []
        for count in PREVIOUS_CUTOFF_COUNTS:
            prior.extend(
                _interval(dates, int(dates.get_loc(pd.Timestamp(day))), horizon, period)
                for day in cutoff_dates(case, count)
            )
        prior.extend(
            (int(dates.get_loc(pd.Timestamp(start))), int(dates.get_loc(pd.Timestamp(end))))
            for start, end in v9_windows[case.unit_id]
        )
        by_year: dict[int, list[tuple[int, int, str, str]]] = defaultdict(list)
        first = 140 if len(dates) > 150 else 30
        for position in range(first, len(dates)):
            start, end = _interval(dates, position, horizon, period)
            if end >= len(dates):
                rejected["no_future_date"] += 1
                continue
            if _overlaps((start, end), prior):
                rejected["prior_same_card_window"] += 1
                continue
            start_day, end_day = str(dates[start].date()), str(dates[end].date())
            eligible_counts[case.family] += 1
            covered_cards[case.family].add(case.unit_id)
            available_years[case.family].add(int(start_day[:4]))
            split = _split(start_day, end_day)
            if split.startswith("PURGED"):
                rejected[split] += 1
                continue
            by_year[int(start_day[:4])].append((start, end, start_day, end_day))

        selected: list[tuple[int, int]] = []
        for year in sorted(by_year):
            # The hash is fixed before scores and retains one origin per card
            # and calendar-year episode. Never choose based on realized values.
            options = sorted(by_year[year], key=lambda record: (
                _digest([case.unit_id, case.family, case.assets, case.horizons,
                         case.target_type, case.target_frequency, record[2]]), record[2]
            ))
            for start, end, start_day, end_day in options:
                if _overlaps((start, end), selected):
                    continue
                selected.append((start, end))
                split = _split(start_day, end_day)
                selected_strata[case.family].add(stratum)
                manifest.append({
                    "unit_id": case.unit_id,
                    "family": case.family,
                    "asset_count": len(case.assets),
                    "horizons_bd": ";".join(map(str, case.horizons)),
                    "target_type": case.target_type,
                    "frequency": case.target_frequency,
                    "target_cells": len(case.assets) * len(case.horizons),
                    "single_cell": int(len(case.assets) * len(case.horizons) == 1),
                    "origin": start_day,
                    "evaluation_end": end_day,
                    "episode_year": year,
                    "split": split,
                    "date_index_sha256": date_indexes[case.unit_id],
                })
                break

    manifest.sort(key=lambda entry: (entry["origin"], entry["unit_id"]))
    # The global market episode key is the calendar year, shared by all cards.
    # Every episode year belongs to exactly one split; the 2009/2017 embargo
    # also prevents a long outcome window from spanning a split boundary.
    episode_assignments: dict[int, set[str]] = defaultdict(set)
    selected_by_card: dict[str, list[tuple[str, str]]] = defaultdict(list)
    dimensions: Counter[tuple[str, str, str, str, str, str]] = Counter()
    for entry in manifest:
        episode_assignments[entry["episode_year"]].add(entry["split"])
        interval = (entry["origin"], entry["evaluation_end"])
        if any(interval[0] <= old_end and old_start <= interval[1]
               for old_start, old_end in selected_by_card[entry["unit_id"]]):
            raise AssertionError("selected intervals overlap within a card")
        selected_by_card[entry["unit_id"]].append(interval)
        for horizon in entry["horizons_bd"].split(";"):
            horizon_days = int(horizon)
            bucket = "1-5" if horizon_days <= 5 else "6-21" if horizon_days <= 21 else "22+"
            dimensions[(entry["family"], entry["split"], bucket, entry["frequency"],
                        entry["target_type"], str(entry["single_cell"]))] += 1
    if any(len(splits) != 1 for splits in episode_assignments.values()):
        raise AssertionError("episode assigned to more than one split")
    rows = Counter((entry["family"], entry["split"]) for entry in manifest)
    cards_by_split: dict[tuple[str, str], set[str]] = defaultdict(set)
    episodes_by_split: dict[tuple[str, str], set[int]] = defaultdict(set)
    for entry in manifest:
        key = (entry["family"], entry["split"])
        cards_by_split[key].add(entry["unit_id"])
        episodes_by_split[key].add(entry["episode_year"])
    feasibility = {}
    for family in ("T2-F1", "T2-F2", "T2-F3", "T2-F4"):
        feasibility[family] = {
            "baseline_cards": source_counts[family],
            "remaining_cards": len(covered_cards[family]),
            "remaining_origin_positions": eligible_counts[family],
            "remaining_calendar_years": sorted(available_years[family]),
            "original_strata": sorted(original_strata[family]),
            "represented_strata": sorted(selected_strata[family]),
            "splits": {split: {"origins": rows[(family, split)],
                               "cards": len(cards_by_split[(family, split)]),
                               "episode_years": sorted(episodes_by_split[(family, split)])}
                       for split in ("FIT", "SELECT", "FINAL")},
        }
    failures = []
    for family, info in feasibility.items():
        for split in ("SELECT", "FINAL"):
            stats = info["splits"][split]
            if len(stats["episode_years"]) < MIN_EPISODE_YEARS or stats["cards"] < MIN_CARDS:
                failures.append(
                    f"{family} {split}: {len(stats['episode_years'])} episodes / "
                    f"{stats['cards']} cards"
                )
        missing = sorted(set(info["original_strata"]) - set(info["represented_strata"]))
        if missing:
            failures.append(f"{family} missing target strata: {', '.join(missing)}")

    audit = {
        "## Executive summary (read this first)": SUMMARY,
        "protocol": "v10-0-date-only-shadow-feasibility-1",
        "outcome_magnitudes_or_scores_used": False,
        "source_commit": "7a0c6ec",
        "previous_cutoff_counts": list(PREVIOUS_CUTOFF_COUNTS),
        "v9_manifest_sha256": v9["entries_sha256"],
        "calendar_splits": {"FIT": "2000-2008", "embargo_1": 2009,
                            "SELECT": "2010-2016", "embargo_2": 2017,
                            "FINAL": "2018 onward"},
        "minimums_predeclared": {"episode_years_per_family_select_final": MIN_EPISODE_YEARS,
                                 "cards_per_family_select_final": MIN_CARDS,
                                 "baseline_target_strata_represented": True},
        "excluded_position_counts": dict(sorted(rejected.items())),
        "overlap_audit": {
            "prior_same_card_windows_excluded": rejected["prior_same_card_window"],
            "selected_vs_prior_same_card_intersections": 0,
            "selected_within_card_intersections": 0,
            "cross_split_episode_year_intersections": 0,
            "boundary_crossing_positions_excluded": rejected["PURGED_BOUNDARY"],
            "embargo_year_positions_excluded": rejected["PURGED_EMBARGO"],
        },
        "episodes_assigned_to_multiple_splits": 0,
        "selected_origin_count": len(manifest),
        "manifest_rows_sha256": _digest(manifest),
        "family_split_horizon_frequency_type_cell_counts": [
            {"family": key[0], "split": key[1], "horizon_bucket": key[2],
             "frequency": key[3], "target_type": key[4], "single_cell": bool(int(key[5])),
             "target_rows": count}
            for key, count in sorted(dimensions.items())
        ],
        "feasibility": feasibility,
        "gate": "FAIL: independent validation insufficient" if failures else "PASS",
        "failures": failures,
        "limitations": [
            "Public historical panels can contain revisions and do not preserve real-time "
            "vintages.",
            "V6/V7 event-oriented evaluation origins lack a complete per-card interval ledger "
            "here; "
            "their exposure cannot be proved absent.",
            "Common market episodes remain dependent even after calendar-year grouping.",
            "The date-only FINAL manifest is frozen, but no FINAL outcome or score is opened.",
        ],
    }
    return manifest, audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, default=Path("backtesting/v10_shadow"))
    args = parser.parse_args()
    manifest, audit = build(args.root)
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    path = out / "v10_shadow_manifest.csv"
    with path.open("w", newline="") as handle:
        handle.write("# ## Executive summary (read this first): " + SUMMARY + "\n")
        writer = csv.DictWriter(handle, lineterminator="\n", fieldnames=(
            "unit_id", "family", "asset_count", "horizons_bd", "target_type",
            "frequency", "target_cells", "single_cell", "origin", "evaluation_end",
            "episode_year", "split", "date_index_sha256",
        ))
        writer.writeheader()
        writer.writerows(manifest)
    audit["manifest_file_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (out / "v10_shadow_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps({"gate": audit["gate"], "rows": len(manifest),
                      "file_sha256": audit["manifest_file_sha256"],
                      "failures": audit["failures"]}, indent=2))


if __name__ == "__main__":
    main()

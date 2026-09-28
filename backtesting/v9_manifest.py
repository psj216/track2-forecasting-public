"""## Executive summary (read this first)

Freeze new pseudo-asof origins using public date indexes alone. Exclude the
evaluation intervals used by prior 6-, 8-, and 12-cutoff studies on the same
card. New intervals do not overlap one another within a card. This reduces
repeat testing; it cannot make revised public histories an independent holdout.
No realized values or private reference data enter the manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from backtesting.universe_backtest import (
    _observation_period_business_days,
    cutoff_dates,
    load_universe,
)

PREVIOUS_CUTOFF_COUNTS = (6, 8, 12)
MAX_NEW_PER_CARD = 12


def _interval(dates: pd.DatetimeIndex, position: int, horizon: int, period: int):
    end = (
        position + horizon
        if period <= 2
        else int(dates.searchsorted(dates[position] + pd.offsets.BDay(horizon)))
    )
    return position, end


def _overlaps(interval: tuple[int, int], exclusions: list[tuple[int, int]]) -> bool:
    return any(interval[0] <= end and start <= interval[1] for start, end in exclusions)


def _origins_for_card(case) -> tuple[list[dict], dict]:
    aligned = pd.DataFrame(case.histories).dropna()
    dates = pd.DatetimeIndex(pd.to_datetime(aligned.index))
    period = _observation_period_business_days(aligned)
    maximum = max(case.horizons)
    exposed: list[tuple[int, int]] = []
    for count in PREVIOUS_CUTOFF_COUNTS:
        for cutoff in cutoff_dates(case, count):
            position = int(dates.get_loc(pd.Timestamp(cutoff)))
            exposed.append(_interval(dates, position, maximum, period))
    unique_exposed = sorted(set(exposed))
    first = 140 if len(dates) > 150 else 30
    eligible = []
    for position in range(first, len(dates)):
        interval = _interval(dates, position, maximum, period)
        if interval[1] >= len(dates) or _overlaps(interval, unique_exposed):
            continue
        eligible.append(interval)
    # Uniform targets are chosen from eligible calendar positions. The nearest
    # disjoint interval is selected with a deterministic early-date tie-break.
    selected: list[tuple[int, int]] = []
    if eligible:
        eligible_positions = {interval[0]: index for index, interval in enumerate(eligible)}
        target_positions = np.linspace(0, len(eligible) - 1, min(MAX_NEW_PER_CARD, len(eligible)))
        for target in target_positions:
            for interval in sorted(eligible, key=lambda pair: (
                abs(eligible_positions[pair[0]] - target), pair[0]
            )):
                if interval not in selected and not _overlaps(interval, selected):
                    selected.append(interval)
                    break
    selected.sort()
    rows = [{
        "unit_id": case.unit_id, "family": case.family,
        "cutoff": str(dates[start].date()), "end": str(dates[end].date()),
        "target_cells": len(case.assets) * len(case.horizons),
    } for start, end in selected]
    provenance = {"unit_id": case.unit_id, "date_index_sha256": hashlib.sha256(
        "\n".join(str(day.date()) for day in dates).encode()
    ).hexdigest(), "old_windows": len(unique_exposed), "safe_positions": len(eligible)}
    return rows, provenance


def build(root: Path) -> dict:
    entries = []
    sources = []
    for case in load_universe(root):
        rows, provenance = _origins_for_card(case)
        entries.extend(rows)
        sources.append(provenance)
    # Several public cards share identical grids and past data. Count a dated
    # asset/horizon/family target only once; choice is by sorted unit ID.
    cases_by_key: dict[tuple, dict] = {}
    universe = {case.unit_id: case for case in load_universe(root)}
    for row in sorted(entries, key=lambda record: (record["cutoff"], record["unit_id"])):
        case = universe[row["unit_id"]]
        key = (case.family, tuple(case.assets), tuple(case.horizons),
               case.target_type, case.target_frequency, row["cutoff"])
        cases_by_key.setdefault(key, row)
    selected = sorted(cases_by_key.values(), key=lambda r: (r["cutoff"], r["unit_id"]))
    dates = sorted({row["cutoff"] for row in selected})
    if len(dates) < 10:
        raise ValueError("too few distinct new dates to split")
    select_start = dates[int(0.4 * len(dates))]
    later_start = dates[int(0.7 * len(dates))]
    for row in selected:
        if row["cutoff"] < select_start:
            row["split"] = "fit" if row["end"] < select_start else "purged"
        elif row["cutoff"] < later_start:
            row["split"] = "select" if row["end"] < later_start else "purged"
        else:
            row["split"] = "later"
    payload = json.dumps(selected, sort_keys=True, separators=(",", ":"))
    return {
        "## Executive summary (read this first)": (
            "Frozen public date-only V9 research origins. No realized observations or scores."
        ),
        "protocol": "v9-0-dates-only-1",
        "prior_cutoff_counts": PREVIOUS_CUTOFF_COUNTS,
        "maximum_origins_per_card": MAX_NEW_PER_CARD,
        "split_boundaries": {"select": select_start, "later": later_start},
        "entries_sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "source_date_indexes": sources,
        "entries": selected,
        "limits": (
            "New evaluation intervals are disjoint from prior same-card 6/8/12 cutoff intervals; "
            "other experiments and revised public histories prevent truly independent validation."
        ),
    }


def verify(manifest: dict, root: Path | None = None) -> None:
    entries = manifest["entries"]
    payload = json.dumps(entries, sort_keys=True, separators=(",", ":"))
    if hashlib.sha256(payload.encode()).hexdigest() != manifest["entries_sha256"]:
        raise ValueError("V9 manifest checksum differs")
    if manifest["protocol"] != "v9-0-dates-only-1":
        raise ValueError("wrong V9 manifest protocol")
    if root is None:
        return
    rows_by_card: dict[str, list[dict]] = {}
    for row in entries:
        rows_by_card.setdefault(row["unit_id"], []).append(row)
    for case in load_universe(root):
        aligned = pd.DataFrame(case.histories).dropna()
        dates = pd.DatetimeIndex(pd.to_datetime(aligned.index))
        period = _observation_period_business_days(aligned)
        maximum = max(case.horizons)
        old = [
            _interval(dates, int(dates.get_loc(pd.Timestamp(cutoff))), maximum, period)
            for count in PREVIOUS_CUTOFF_COUNTS for cutoff in cutoff_dates(case, count)
        ]
        new = []
        for row in rows_by_card.get(case.unit_id, []):
            position = int(dates.get_loc(pd.Timestamp(row["cutoff"])))
            interval = _interval(dates, position, maximum, period)
            if _overlaps(interval, old) or _overlaps(interval, new):
                raise ValueError("V9 evaluation interval overlaps prior or new interval")
            if str(dates[interval[1]].date()) != row["end"]:
                raise ValueError("V9 interval end differs from manifest")
            new.append(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.root)
    verify(result, args.root)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    counts = {split: sum(row["split"] == split for row in result["entries"])
              for split in ("fit", "select", "later", "purged")}
    print(json.dumps({"checksum": result["entries_sha256"], "counts": counts,
                      "dates": len({row["cutoff"] for row in result["entries"]})}, indent=2))


if __name__ == "__main__":
    main()

"""## Executive summary (read this first)

Evaluate the already specified selector on disjoint outer pseudo-events. Each outer
prediction repeats selection using only earlier data. The held-out response is used
only after prediction. Results remain outside the public repository and never tune code.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import tomllib
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qfbench2_track_forecasting.cli import _read_panels, _series
from qfbench2_track_forecasting.v6.catalog import load_catalog
from qfbench2_track_forecasting.v6.engine import apply_v6
from qfbench2_track_forecasting.v6.responses import extract, frame_at
from qfbench2_track_forecasting.v6.selector import statistics
from qfbench2_track_forecasting.v6.walkforward import baseline_at, loss_ratio


def run(item: tuple[str, str, int, int, int]) -> list[dict]:
    path, catalog, seed, draws, count = item
    unit = Path(path).parent
    card = tomllib.loads(Path(path).read_text())
    t = card["targets"]
    family = card["metadata"]["category"]
    asof = card["provenance"]["data_cutoff"]
    assets = t["asset_ids"]
    h = t["horizons"]
    target = t["target_type"]
    freq = t["target_frequency"]
    value_unit = t.get("value_unit", "")
    panels = _read_panels(unit)
    hist = {a: _series(panels, a, asof) for a in assets}
    frame = frame_at(hist, assets, asof)
    records = load_catalog(Path(catalog), asof)
    cases = []
    for event in reversed(records):
        if family == "T2-F1" and not event.fingerprint.delta:
            continue
        r = extract(frame, event, h, target, freq, asof)
        if r is None or any(not (r.end < q.start or r.start > q.end) for q in cases):
            continue
        cases.append(r)
        if len(cases) >= count:
            break
    rows = []
    for case in reversed(cases):
        cutoff = case.event.published_at
        past = frame.loc[frame.index <= pd.Timestamp(cutoff)]
        n = max(draws, 1000 if family == "T2-F4" else draws)
        available = load_catalog(Path(catalog), cutoff)
        base = baseline_at(
            past, available, cutoff, assets, h, target, freq, family, n, seed, value_unit
        )
        with tempfile.TemporaryDirectory(prefix="v6-outer-") as tmp:
            folder = Path(tmp)
            docs = []
            for i, event in enumerate(available[-12:]):
                filename = f"{i}.txt"
                (folder / filename).write_text(event.text)
                docs.append(
                    {
                        "doc_id": f"{event.doc_type}-{i}",
                        "timestamp": event.published_at,
                        "source": "Federal Reserve",
                        "doc_type": event.doc_type,
                        "file": filename,
                    }
                )
            (folder / "corpus_index.json").write_text(json.dumps({"documents": docs}))
            output, meta = apply_v6(
                base,
                {a: past[a] for a in assets},
                assets,
                h,
                target,
                freq,
                family,
                cutoff,
                seed,
                folder,
                value_unit,
                Path(catalog),
            )
        # Only after forecast: access the disjoint pseudo-future.
        outcome = case.path + (past.iloc[-1].to_numpy()[:, None] if target == "level" else 0.0)
        ratio = loss_ratio(output, base, outcome)
        # Equivalent asset/date/horizon cases are clustered by identity in report aggregation.
        identity = json.dumps([assets, h, target, cutoff])
        rows.append(
            {
                "unit": unit.name,
                "family": family,
                "cutoff": cutoff,
                "identity": identity,
                "active": meta["applied"],
                "ratio": ratio,
                "reason": meta["reason"],
            }
        )
    return rows


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--catalog", type=Path, default=Path("data/v6"))
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--seed", type=int, default=17)
    p.add_argument("--draws", type=int, default=500)
    p.add_argument("--cases", type=int, default=2)
    args = p.parse_args()
    paths = sorted((args.root / "units").glob("t2-F*/card.toml"))
    inputs = [
        (str(p.resolve()), str(args.catalog.resolve()), args.seed, args.draws, args.cases)
        for p in paths
    ]
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for part in pool.map(run, inputs):
            rows.extend(part)
            print("outer cases", len(rows), flush=True)
    unique = {}
    for row in rows:
        unique.setdefault((row["family"], row["identity"]), row)
    values = list(unique.values())
    families = {}
    for family in ("T2-F1", "T2-F2", "T2-F3", "T2-F4"):
        group = [r for r in values if r["family"] == family]
        families[family] = {
            **statistics([r["ratio"] for r in group]),
            "active": sum(r["active"] for r in group),
        }
    active = [r for r in values if r["active"]]
    summary = statistics([r["ratio"] for r in values])
    # Architecture gate is predeclared. Inactivity is not evidence of an improvement.
    release = (
        len(active) >= 10
        and summary.get("geometric_ratio", 1) <= 0.98
        and all(
            f.get("geometric_ratio", 1) <= 1.01 and f.get("q90", 1) <= 1.1
            for f in families.values()
        )
    )
    report = {
        "release_candidate": release,
        "unique_cases": len(values),
        "active_cases": len(active),
        "summary": summary,
        "families": families,
        "rows": values,
        "seed": args.seed,
        "draws": args.draws,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "outer.json").write_text(json.dumps(report, indent=2) + "\n")
    with (args.out / "V6_REPORT.md").open("a") as out:
        out.write(
            "\nOuter walk-forward results (not official scores):\n\n```json\n"
            + json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=2)
            + "\n```\n"
        )
    print("RELEASE_CANDIDATE =", release, flush=True)


if __name__ == "__main__":
    main()

"""## Executive summary (read this first)

Run every practice card, verify exact fallback and F3 marginal preservation, and write
an audit report outside the repository. No private outcomes or official scores are read.
The release flag requires independent outer replay evidence, not activation alone.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import tomllib
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qfbench2_track_forecasting.cli import _read_panels, _series
from qfbench2_track_forecasting.numeric_v3 import forecast_numeric_v3
from qfbench2_track_forecasting.text_first_v5 import apply_text_first_v5
from qfbench2_track_forecasting.v6.catalog import load_catalog
from qfbench2_track_forecasting.v6.engine import apply_v6


def run_card(item: tuple[str, str, int, int]) -> dict:
    card_path, catalog, seed, draws = item
    path = Path(card_path)
    card = tomllib.loads(path.read_text())
    t = card["targets"]
    family = card["metadata"]["category"]
    asof = card["provenance"]["data_cutoff"]
    assets = t["asset_ids"]
    horizons = t["horizons"]
    n = max(draws, 1000 if family == "T2-F4" else draws)
    panel = _read_panels(path.parent)
    hist = {a: _series(panel, a, asof) for a in assets}
    numeric = forecast_numeric_v3(
        hist, assets, horizons, t["target_type"], t["target_frequency"], n, seed, family
    ).samples
    base, _ = apply_text_first_v5(
        numeric,
        hist,
        assets,
        horizons,
        t["target_type"],
        t["target_frequency"],
        family,
        asof,
        seed,
        path.parent / "text",
        t.get("value_unit", ""),
        interpreter_version="v5.1",
    )
    start = time.monotonic()
    result, meta = apply_v6(
        base,
        hist,
        assets,
        horizons,
        t["target_type"],
        t["target_frequency"],
        family,
        asof,
        seed,
        path.parent / "text",
        t.get("value_unit", ""),
        Path(catalog),
    )
    assert np.isfinite(result).all()
    assert meta["applied"] == (not np.array_equal(result, base))
    if not meta["applied"]:
        assert result is base
    if family == "T2-F3":
        np.testing.assert_array_equal(np.sort(result, axis=0), np.sort(base, axis=0))
    if meta["applied"]:
        assert meta["max_response_date"] <= asof
    return {
        "unit": path.parent.name,
        "family": family,
        "asof": asof,
        "seed": seed,
        "draws": n,
        "seconds": round(time.monotonic() - start, 3),
        "metadata": meta,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--catalog", type=Path, default=Path("data/v6"))
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--seed", type=int, default=17)
    p.add_argument("--draws", type=int, default=500)
    args = p.parse_args()
    records = load_catalog(args.catalog, "9999-12-31")
    cards = sorted((args.root / "units").glob("t2-F*/card.toml"))
    args.out.mkdir(parents=True, exist_ok=True)
    items = [(str(p.resolve()), str(args.catalog.resolve()), args.seed, args.draws) for p in cards]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        rows = []
        for row in pool.map(run_card, items):
            rows.append(row)
            print(row["unit"], row["metadata"]["reason"], row["seconds"], flush=True)
    report = {
        "catalog_records": len(records),
        "cards": len(rows),
        "active": sum(r["metadata"]["applied"] for r in rows),
        "release_candidate": False,
        "release_reason": "outer walk-forward gate must be evaluated separately",
        "rows": rows,
    }
    (args.out / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = [
        "# V6 report",
        "",
        f"Catalog records: {len(records)}. Cards: {len(rows)}.",
        f'Actual-asof activation: {report["active"]}/{len(rows)}.',
        "No official score is estimated from these checks.",
        "",
        "| Family | Active | Total |",
        "|---|---:|---:|",
    ]
    for f in ("T2-F1", "T2-F2", "T2-F3", "T2-F4"):
        part = [r for r in rows if r["family"] == f]
        lines.append(f'| {f} | {sum(r["metadata"]["applied"] for r in part)} | {len(part)} |')
    lines += [
        "",
        "Exact fallback and F3 marginal preservation: PASS.",
        "Independent outer validation: pending.",
        "RELEASE_CANDIDATE = NO until the outer gate and Docker gates pass.",
    ]
    (args.out / "V6_REPORT.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()

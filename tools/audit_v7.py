"""## Executive summary (read this first)

Audit all public as-of cards and replay earlier F2 event cutoffs. Outcomes are
opened only after the corresponding forecast is made. Multiple cards with the
same event quarter are summarized as a cluster, not independent discoveries.
This diagnostic never estimates the official leaderboard score.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import tomllib
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qfbench2_track_forecasting.cli import _read_panels, _series
from qfbench2_track_forecasting.numeric_v3 import forecast_numeric_v3
from qfbench2_track_forecasting.text_first_v5 import apply_text_first_v5
from qfbench2_track_forecasting.v6.responses import extract, frame_at
from qfbench2_track_forecasting.v6.walkforward import loss_ratio
from qfbench2_track_forecasting.v7.catalog import load_catalog
from qfbench2_track_forecasting.v7.engine import apply_v7


def _pseudo_corpus(root: Path, event) -> None:
    (root / "event.txt").write_text(event.text)
    (root / "corpus_index.json").write_text(
        json.dumps(
            {
                "documents": [
                    {
                        "doc_id": event.episode_id,
                        "timestamp": event.published_at,
                        "source": {
                            "US": "Federal Reserve"
                            if event.event_type == "POLICY_DECISION"
                            else "BLS",
                            "EU": "ECB",
                        }.get(event.region, event.region),
                        "doc_type": event.doc_type,
                        "file": "event.txt",
                    }
                ]
            }
        )
    )


def run_card(item: tuple[str, str, int, int, int]) -> dict:
    card_file, catalog_path, seed, draws, outer_cases = item
    card_path = Path(card_file)
    card = tomllib.loads(card_path.read_text())
    t = card["targets"]
    family = card["metadata"]["category"]
    asof = card["provenance"]["data_cutoff"]
    assets, horizons = t["asset_ids"], t["horizons"]
    n = max(draws, 1000 if family == "T2-F4" else draws)
    histories = {a: _series(_read_panels(card_path.parent), a, asof) for a in assets}
    numeric = forecast_numeric_v3(
        histories, assets, horizons, t["target_type"], t["target_frequency"], n, seed, family
    ).samples
    base, _ = apply_text_first_v5(
        numeric,
        histories if family in {"T2-F1", "T2-F4"} else {},
        assets,
        horizons,
        t["target_type"],
        t["target_frequency"],
        family,
        asof,
        seed,
        card_path.parent / "text",
        t.get("value_unit", ""),
        interpreter_version="v5.1",
    )
    candidate, meta = apply_v7(
        base,
        histories,
        assets,
        horizons,
        t["target_type"],
        t["target_frequency"],
        family,
        asof,
        seed,
        card_path.parent / "text",
        Path(catalog_path),
    )
    assert meta["applied"] == (not np.array_equal(candidate, base))
    if not meta["applied"]:
        assert candidate is base
    if family != "T2-F2":
        assert candidate is base
    if meta["applied"]:
        assert meta["max_response_date"] <= asof
    result = {
        "unit": card_path.parent.name,
        "family": family,
        "asof": asof,
        "active": meta["applied"],
        "eligible": meta.get("eligible", False),
        "reason": meta["reason"],
        "metadata": meta,
        "outer": [],
    }
    if family != "T2-F2" or outer_cases == 0:
        return result

    frame = frame_at(histories, assets, asof)
    events, _ = load_catalog(Path(catalog_path), asof)
    seen = []
    for event in reversed(events):
        case = extract(frame, event, horizons, t["target_type"], t["target_frequency"], asof)
        if case is None or any(not (case.end < c.start or case.start > c.end) for c in seen):
            continue
        seen.append(case)
        if len(seen) >= outer_cases:
            break
    for case in reversed(seen):
        cutoff = case.event.published_at
        past = frame.loc[frame.index <= pd.Timestamp(cutoff)]
        history = {a: past[a] for a in assets}
        if len(past) < 180:
            continue
        baseline = forecast_numeric_v3(
            history, assets, horizons, t["target_type"], t["target_frequency"], draws, seed, family
        ).samples
        with tempfile.TemporaryDirectory(prefix="v7-outer-") as tmp:
            folder = Path(tmp)
            _pseudo_corpus(folder, case.event)
            prediction, ledger = apply_v7(
                baseline,
                history,
                assets,
                horizons,
                t["target_type"],
                t["target_frequency"],
                family,
                cutoff,
                seed,
                folder,
                Path(catalog_path),
            )
        # This access comes strictly after prediction is produced.
        outcome = case.path + (
            past.iloc[-1].to_numpy()[:, None] if t["target_type"] == "level" else 0.0
        )
        result["outer"].append(
            {
                "event": case.event.episode_id,
                "cutoff": cutoff,
                "quarter": cutoff[:4] + "Q" + str((int(cutoff[5:7]) - 1) // 3 + 1),
                "active": ledger["applied"],
                "eligible": ledger.get("eligible", False),
                "ratio": loss_ratio(prediction, baseline, outcome),
                "reason": ledger["reason"],
            }
        )
    return result


def summarize(rows: list[dict]) -> dict:
    active = sum(r["active"] for r in rows)
    eligible = sum(r["eligible"] for r in rows)
    ratios = np.array([r["ratio"] for r in rows], dtype=float)
    return {
        "count": len(rows),
        "active": active,
        "eligible": eligible,
        "activation": active / max(1, len(rows)),
        "coverage": eligible / max(1, len(rows)),
        "geometric_ratio": float(np.exp(np.log(ratios).mean())) if len(ratios) else 1.0,
        "q90": float(np.quantile(ratios, 0.9)) if len(ratios) else 1.0,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--catalog", type=Path, default=Path("data/v7"))
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--draws", type=int, default=500)
    p.add_argument("--seed", type=int, default=17)
    p.add_argument("--outer-cases", type=int, default=4)
    args = p.parse_args()
    paths = sorted((args.root / "units").glob("t2-F*/card.toml"))
    payload = [
        (str(path), str(args.catalog.resolve()), args.seed, args.draws, args.outer_cases)
        for path in paths
    ]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(run_card, payload))
    outer = [case for row in rows for case in row["outer"]]
    # Disjoint dates within a unit; group later by event-quarter so duplicated cards
    # cannot create dozens of independent wins from one macro episode.
    quarters = {}
    for case in outer:
        quarters.setdefault(case["quarter"], []).append(case)
    clusters = [
        {
            "quarter": quarter,
            "ratio": float(np.exp(np.mean(np.log([x["ratio"] for x in group])))),
            "active": any(x["active"] for x in group),
            "eligible": any(x["eligible"] for x in group),
        }
        for quarter, group in quarters.items()
    ]
    scored = summarize(clusters)
    changed = summarize(outer)
    f2_public = [r for r in rows if r["family"] == "T2-F2"]
    release = (
        changed["active"] >= 10
        and changed["coverage"] >= 0.25
        and changed["activation"] >= 0.10
        and scored["geometric_ratio"] <= 0.98
        and scored["q90"] <= 1.10
    )
    report = {
        "catalog": str(args.catalog),
        "public_cards": len(rows),
        "public_f2": len(f2_public),
        "public_f2_active": sum(r["active"] for r in f2_public),
        "outer": changed,
        "quarter_clusters": scored,
        "release_candidate": release,
        "rows": rows,
        "clusters": clusters,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in {"rows", "clusters"}}, indent=2))


if __name__ == "__main__":
    main()

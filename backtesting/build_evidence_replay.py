"""## Executive summary (read this first)

Build a local Phase-6 evidence replay from public historical cutoffs.  The builder calls the same
strict Phase-4 interpreter used by the submission, but only when a cutoff has both later panel data
and at least one frozen document already published.  It writes validated evidence, never forecast
outcomes.  The resulting JSONL is a calibration input and must not be mistaken for a score report.

The organizer-compatible model endpoint must be configured explicitly.  If it is unavailable or
rejects every case, the command fails instead of manufacturing evidence or silently approving the
Phase-5 integration.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import tomllib

from qfbench2_track_forecasting.numeric_v3 import forecast_numeric_v3
from qfbench2_track_forecasting.text_evidence import (
    INTERPRETER_SCHEMA_VERSION,
    interpret_text_evidence,
    read_frozen_corpus,
)

from .universe_backtest import _seed, cutoff_dates, future_observations, load_universe


def build_evidence_replay(
    root: pathlib.Path,
    output: pathlib.Path,
    cutoff_count: int,
    n_draws: int,
    *,
    seed_salt: str = "phase6-evidence-v1",
    families: set[str] | None = None,
) -> tuple[int, int]:
    """Materialize validated evidence and return ``(written, skipped)`` case counts."""
    if not os.environ.get("MODEL_ENDPOINT", "").strip():
        raise RuntimeError("MODEL_ENDPOINT is unset; refusing to manufacture an evidence replay")
    if output.exists():
        raise ValueError(f"refusing to overwrite existing evidence replay: {output}")
    records: list[dict[str, object]] = []
    skipped = 0
    for case in load_universe(root):
        if families is not None and case.family not in families:
            continue
        unit = root / "units" / case.unit_id
        card = tomllib.loads((unit / "card.toml").read_text(encoding="utf-8"))
        target = card["targets"]
        for cutoff in cutoff_dates(case, cutoff_count):
            corpus = read_frozen_corpus(unit / "text", cutoff)
            if not corpus.documents:
                skipped += 1
                continue
            # Prove future coverage before paying for a model call.
            future_observations(case, cutoff)
            histories = {
                asset: series[series.index.astype(str).str.slice(0, 10) <= cutoff]
                for asset, series in case.histories.items()
            }
            seed = _seed(case.unit_id, cutoff, seed_salt)
            numeric = forecast_numeric_v3(
                histories,
                case.assets,
                case.horizons,
                case.target_type,
                case.target_frequency,
                n_draws,
                seed,
                case.family,
            )
            stats = numeric.metadata
            panel_context = {
                "value_unit": str(target.get("value_unit", "unspecified")),
                "panels": {
                    panel_id: {
                        "series": panel.get("series", []),
                        "asset_ids": panel.get("asset_ids", []),
                        "frequency": panel.get("frequency", ""),
                    }
                    for panel_id, panel in card.get("panels", {}).items()
                    if isinstance(panel, dict)
                },
            }
            numeric_context = {
                "fragility": float(stats["regime"]["fragility"]),
                "recent_weight": float(stats["regime"]["recent_weight"]),
                "uncertainty_scale": float(stats["regime"]["uncertainty_scale"]),
                "daily_drift": {key: float(value) for key, value in stats["daily_drift"].items()},
                "daily_sd": {key: float(value) for key, value in stats["daily_sd"].items()},
                "anchor": {key: float(value) for key, value in stats["anchor"].items()},
            }
            reasoning = interpret_text_evidence(
                text_dir=unit / "text",
                unit_id=case.unit_id,
                family=case.family,
                asof=cutoff,
                assets=case.assets,
                horizons=case.horizons,
                target_type=case.target_type,
                target_frequency=case.target_frequency,
                panel_context=panel_context,
                numeric_context=numeric_context,
            )
            if not reasoning.applied or reasoning.evidence is None:
                skipped += 1
                continue
            records.append(
                {
                    "unit_id": case.unit_id,
                    "cutoff": cutoff,
                    "model_name": reasoning.model_name,
                    "interpreter_schema_version": INTERPRETER_SCHEMA_VERSION,
                    "evidence": reasoning.evidence,
                }
            )
    if not records:
        raise RuntimeError(
            "no evidence replay cases were produced; configure the organizer MODEL_ENDPOINT and "
            "check that selected cutoffs have frozen documents"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n",
        encoding="utf-8",
    )
    return len(records), skipped


def main() -> int:
    parser = argparse.ArgumentParser(description="Build cutoff-safe Phase-6 evidence replay")
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path("."))
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--cutoffs", type=int, default=12)
    parser.add_argument("--n-draws", type=int, default=300)
    parser.add_argument("--seed-salt", default="phase6-evidence-v1")
    parser.add_argument("--family", action="append", choices=("T2-F1", "T2-F2", "T2-F3", "T2-F4"))
    args = parser.parse_args()
    try:
        written, skipped = build_evidence_replay(
            args.root,
            args.output,
            args.cutoffs,
            args.n_draws,
            seed_salt=args.seed_salt,
            families=set(args.family) if args.family else None,
        )
    except (RuntimeError, ValueError) as exc:
        parser.error(str(exc))
    print(f"validated replay cases written: {written}")
    print(f"cases skipped before calibration: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

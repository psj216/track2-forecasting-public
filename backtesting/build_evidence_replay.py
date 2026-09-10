"""## Executive summary (read this first)

Build a local Phase-6 evidence replay from public historical cutoffs.  The builder calls the same
strict Phase-4 interpreter used by the submission, but only when a cutoff has both later panel data
and at least one frozen document already published.  It writes validated evidence, never forecast
outcomes.  The resulting JSONL is a calibration input and must not be mistaken for a score report.

A development-only OpenAI-compatible endpoint must be configured through ``CALIBRATION_MODEL_*``.
The official ``MODEL_ENDPOINT`` variables are never read here.  If the proxy is unavailable or
rejects a selected case, the strict command fails instead of manufacturing evidence or silently
approving the Phase-5 integration.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import tempfile
import tomllib

from qfbench2_track_forecasting.numeric_v3 import forecast_numeric_v3
from qfbench2_track_forecasting.text_evidence import (
    INTERPRETER_PROMPT_VERSION,
    INTERPRETER_SCHEMA_VERSION,
    interpret_text_evidence,
    read_frozen_corpus,
)

from .calibration_model import CalibrationModelClient
from .universe_backtest import (
    UniverseCase,
    calibration_seed,
    cutoff_dates,
    future_observations,
    load_universe,
)

REPLAY_FORMAT_VERSION = "2.0.0"
CALIBRATION_KIND = "public_nemotron_proxy"


def _selected_cutoffs(
    case: UniverseCase, root: pathlib.Path, cutoff_count: int, one_case_per_unit: bool
) -> list[str]:
    candidates = cutoff_dates(case, cutoff_count)
    if not one_case_per_unit:
        return candidates
    safe = [
        cutoff
        for cutoff in candidates
        if read_frozen_corpus(root / "units" / case.unit_id / "text", cutoff).documents
    ]
    return safe[-1:]


def build_evidence_replay(
    root: pathlib.Path,
    output: pathlib.Path,
    cutoff_count: int,
    n_draws: int,
    *,
    seed_salt: str = "phase6-evidence-v1",
    families: set[str] | None = None,
    model_client: CalibrationModelClient | None = None,
    strict_model_failures: bool = False,
    one_case_per_unit: bool = False,
) -> tuple[int, int]:
    """Materialize validated evidence and return ``(written, skipped)`` case counts."""
    client = model_client or CalibrationModelClient.from_environment()
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
        for cutoff in _selected_cutoffs(case, root, cutoff_count, one_case_per_unit):
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
            seed = calibration_seed(case.unit_id, cutoff, case.family, n_draws, seed_salt)
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
                model_caller=client.call,
                model_name_hint=client.model_name,
            )
            if not reasoning.applied or reasoning.evidence is None:
                if strict_model_failures:
                    raise RuntimeError(
                        f"proxy evidence failed for {case.unit_id}|{cutoff}: "
                        f"{reasoning.skipped_reason}"
                    )
                skipped += 1
                continue
            if reasoning.model_name != client.model_name:
                raise RuntimeError(
                    f"proxy returned model name {reasoning.model_name!r}, expected "
                    f"{client.model_name!r}; refusing a mixed or redirected replay"
                )
            records.append(
                {
                    "calibration_kind": CALIBRATION_KIND,
                    "unit_id": case.unit_id,
                    "cutoff": cutoff,
                    "model_name": reasoning.model_name,
                    "interpreter_prompt_version": INTERPRETER_PROMPT_VERSION,
                    "interpreter_schema_version": INTERPRETER_SCHEMA_VERSION,
                    "replay_format_version": REPLAY_FORMAT_VERSION,
                    "evidence": reasoning.evidence,
                }
            )
    if not records:
        raise RuntimeError(
            "no evidence replay cases were produced; configure CALIBRATION_MODEL_* and check "
            "that selected cutoffs have frozen documents"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n"
    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=output.parent, prefix=".replay-", delete=False
        ) as temporary:
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_name = temporary.name
        os.link(temporary_name, output)
    except FileExistsError as exc:
        raise ValueError(f"refusing to overwrite existing evidence replay: {output}") from exc
    finally:
        if temporary_name:
            pathlib.Path(temporary_name).unlink(missing_ok=True)
    return len(records), skipped


def main() -> int:
    parser = argparse.ArgumentParser(description="Build cutoff-safe public-model evidence replay")
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path("."))
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--cutoffs", type=int, default=5)
    parser.add_argument("--n-draws", type=int, default=300)
    parser.add_argument("--seed-salt", default="phase6-evidence-v1")
    parser.add_argument("--family", action="append", choices=("T2-F4",), default=["T2-F4"])
    args = parser.parse_args()
    try:
        written, skipped = build_evidence_replay(
            args.root,
            args.output,
            args.cutoffs,
            args.n_draws,
            seed_salt=args.seed_salt,
            families=set(args.family) if args.family else None,
            strict_model_failures=True,
            one_case_per_unit=True,
        )
    except (RuntimeError, ValueError) as exc:
        parser.error(str(exc))
    print(f"validated replay cases written: {written}")
    print(f"cases skipped before calibration: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

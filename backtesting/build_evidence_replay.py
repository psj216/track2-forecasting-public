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
    EvidenceModelCaller,
    INTERPRETER_PROMPT_VERSION,
    INTERPRETER_SCHEMA_VERSION,
    ReasoningResult,
    interpret_text_evidence,
    read_frozen_corpus,
    validate_evidence_response,
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
_MAX_SCHEMA_REPAIR_ATTEMPTS = 3

_CHECKPOINT_VERSION = "1.0.0"

_EVIDENCE_TOP_LEVEL_KEYS = (
    "market_state",
    "evidence",
    "views",
    "skeptic",
    "scenarios",
)

_REPLAY_RECORD_KEYS = {
    "calibration_kind",
    "unit_id",
    "cutoff",
    "model_name",
    "interpreter_prompt_version",
    "interpreter_schema_version",
    "replay_format_version",
    "evidence",
}


def _normalize_calibration_raw(raw: object) -> object:
    """Drop only surplus top-level keys when every required key already exists.

    Missing required keys, malformed nested fields, duplicate scenarios, invented citations,
    and every other semantic/schema error remain untouched for the strict validator.
    """
    if not isinstance(raw, dict):
        return raw

    required = set(_EVIDENCE_TOP_LEVEL_KEYS)
    if not required.issubset(raw):
        return raw

    return {key: raw[key] for key in _EVIDENCE_TOP_LEVEL_KEYS}


def _checkpoint_config(
    *,
    client: CalibrationModelClient,
    cutoff_count: int,
    n_draws: int,
    seed_salt: str,
    families: set[str] | None,
    one_case_per_unit: bool,
) -> dict[str, object]:
    return {
        "model_name": client.model_name,
        "interpreter_prompt_version": INTERPRETER_PROMPT_VERSION,
        "interpreter_schema_version": INTERPRETER_SCHEMA_VERSION,
        "replay_format_version": REPLAY_FORMAT_VERSION,
        "cutoff_count": cutoff_count,
        "n_draws": n_draws,
        "seed_salt": seed_salt,
        "families": sorted(families) if families is not None else None,
        "one_case_per_unit": one_case_per_unit,
    }


def _load_checkpoint(
    path: pathlib.Path,
    expected_config: dict[str, object],
) -> dict[tuple[str, str], dict[str, object]]:
    if not path.exists():
        return {}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read calibration checkpoint: {exc}") from exc

    expected_top = {"checkpoint_version", "config", "records"}
    if not isinstance(payload, dict) or set(payload) != expected_top:
        raise ValueError("calibration checkpoint has an invalid shape")

    if payload["checkpoint_version"] != _CHECKPOINT_VERSION:
        raise ValueError("calibration checkpoint version is stale")

    if payload["config"] != expected_config:
        raise ValueError(
            "calibration checkpoint configuration does not match this run; "
            "do not reuse it with different model/prompt/draw settings"
        )

    raw_records = payload["records"]
    if not isinstance(raw_records, list):
        raise ValueError("calibration checkpoint records must be a list")

    result: dict[tuple[str, str], dict[str, object]] = {}

    for index, record in enumerate(raw_records):
        if not isinstance(record, dict) or set(record) != _REPLAY_RECORD_KEYS:
            raise ValueError(f"checkpoint record {index} has an invalid shape")

        if record["calibration_kind"] != CALIBRATION_KIND:
            raise ValueError(f"checkpoint record {index} has the wrong calibration kind")
        if record["model_name"] != expected_config["model_name"]:
            raise ValueError(f"checkpoint record {index} has a different model")
        if record["interpreter_prompt_version"] != INTERPRETER_PROMPT_VERSION:
            raise ValueError(f"checkpoint record {index} has a stale prompt version")
        if record["interpreter_schema_version"] != INTERPRETER_SCHEMA_VERSION:
            raise ValueError(f"checkpoint record {index} has a stale schema version")
        if record["replay_format_version"] != REPLAY_FORMAT_VERSION:
            raise ValueError(f"checkpoint record {index} has a stale replay version")

        unit_id = str(record["unit_id"])
        cutoff = str(record["cutoff"])
        key = (unit_id, cutoff)

        if key in result:
            raise ValueError(f"duplicate checkpoint case {unit_id}|{cutoff}")

        result[key] = record

    return result


def _write_checkpoint(
    path: pathlib.Path,
    config: dict[str, object],
    records: list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(
        {
            "checkpoint_version": _CHECKPOINT_VERSION,
            "config": config,
            "records": records,
        },
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )

    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".checkpoint-",
            delete=False,
        ) as temporary:
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_name = temporary.name

        os.replace(temporary_name, path)
        temporary_name = ""
    finally:
        if temporary_name:
            pathlib.Path(temporary_name).unlink(missing_ok=True)


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

    checkpoint_path = output.with_name(output.name + ".partial.json")
    checkpoint_config = _checkpoint_config(
        client=client,
        cutoff_count=cutoff_count,
        n_draws=n_draws,
        seed_salt=seed_salt,
        families=families,
        one_case_per_unit=one_case_per_unit,
    )
    cached_records = _load_checkpoint(checkpoint_path, checkpoint_config)

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

            case_key = (case.unit_id, cutoff)
            cached_record = cached_records.get(case_key)

            if cached_record is not None:
                try:
                    validate_evidence_response(
                        cached_record["evidence"],
                        assets=case.assets,
                        document_ids={doc.doc_id for doc in corpus.documents},
                    )
                except ValueError as exc:
                    raise ValueError(
                        f"cached evidence failed revalidation for "
                        f"{case.unit_id}|{cutoff}: {exc}"
                    ) from exc

                records.append(cached_record)
                print(f"[replay] RESUME {case.unit_id}|{cutoff}")
                continue

            print(f"[replay] REQUEST {case.unit_id}|{cutoff}")

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
            def run_interpreter(model_caller: EvidenceModelCaller) -> ReasoningResult:
                return interpret_text_evidence(
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
                    model_caller=model_caller,
                    model_name_hint=client.model_name,
                )

            last_raw: object | None = None

            def captured_call(prompt: str) -> tuple[object | None, str, str]:
                nonlocal last_raw
                raw, failure, model = client.call(prompt)
                normalized = _normalize_calibration_raw(raw)
                last_raw = normalized
                return normalized, failure, model

            reasoning = run_interpreter(captured_call)

            for repair_attempt in range(1, _MAX_SCHEMA_REPAIR_ATTEMPTS + 1):
                if reasoning.applied:
                    break
                if not reasoning.skipped_reason.startswith("evidence schema rejected:"):
                    break
                if last_raw is None:
                    break

                schema_error = reasoning.skipped_reason.removeprefix(
                    "evidence schema rejected:"
                ).strip()

                previous_json = json.dumps(
                    last_raw,
                    ensure_ascii=False,
                    sort_keys=True,
                )

                def repair_call(
                    prompt: str,
                    *,
                    attempt: int = repair_attempt,
                    error: str = schema_error,
                    previous: str = previous_json,
                ) -> tuple[object | None, str, str]:
                    repair_instruction = f"""

CALIBRATION SCHEMA REPAIR ATTEMPT {attempt}

The previous JSON response failed validation for exactly this reason:
{error}

PREVIOUS INVALID JSON:
{previous}

Repair the PREVIOUS INVALID JSON rather than redoing the market analysis.

Rules:
- Preserve every already-grounded claim and numeric score whenever possible.
- Do not introduce new documents, facts, assets, or future knowledge.
- Return the complete corrected JSON object, not a patch.
- evidence must contain 2 to 8 genuinely distinct grounded items.
- evidence ids must be unique.
- every evidence item must cite supplied doc_ids only.
- scenarios must contain at least 3 UNIQUE names.
- scenario names must come ONLY from the allowed scenario labels in the original request.
- NEVER repeat a scenario name.
- every evidence_id reference must point to an existing evidence item.
- Do not change valid fields merely for variety.
- Return JSON only.

Before sending the response, explicitly check scenario names for duplicates.
"""
                    return captured_call(prompt + repair_instruction)

                reasoning = run_interpreter(repair_call)
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
            record = {
                "calibration_kind": CALIBRATION_KIND,
                "unit_id": case.unit_id,
                "cutoff": cutoff,
                "model_name": reasoning.model_name,
                "interpreter_prompt_version": INTERPRETER_PROMPT_VERSION,
                "interpreter_schema_version": INTERPRETER_SCHEMA_VERSION,
                "replay_format_version": REPLAY_FORMAT_VERSION,
                "evidence": reasoning.evidence,
            }
            records.append(record)

            _write_checkpoint(
                checkpoint_path,
                checkpoint_config,
                records,
            )
            print(
                f"[replay] CHECKPOINT {len(records)} validated cases "
                f"(latest {case.unit_id}|{cutoff})"
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
    checkpoint_path.unlink(missing_ok=True)
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

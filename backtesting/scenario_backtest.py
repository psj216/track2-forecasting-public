"""## Executive summary (read this first)

Calibrate Phase-5 scenario integration with leakage-safe evidence replays.  Each replay record is
bound to one public unit and one historical cutoff.  The record's citations are revalidated against
documents that existed by that cutoff, Numeric v3 and every candidate share the same base draws,
and official public metric primitives compare forecasts with later panel observations.

Candidate selection uses older records.  Approval uses newer holdout records.  A family remains
disabled unless it clears every holdout guard.  This module never generates model evidence, stores
private outcomes, copies official scoring formulas, or treats its diagnostic ratio as the official
competition score.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from qfbench2_track_forecasting.numeric_v3 import forecast_numeric_v3
from qfbench2_track_forecasting.scenario_integration import (
    FAMILY_CONFIGS,
    IntegrationConfig,
    integrate_scenario_worlds,
)
from qfbench2_track_forecasting.text_evidence import (
    INTERPRETER_PROMPT_VERSION,
    INTERPRETER_SCHEMA_VERSION,
    ReasoningResult,
    read_frozen_corpus,
    scenario_probability_ledger,
    validate_evidence_response,
)

from .build_evidence_replay import CALIBRATION_KIND, REPLAY_FORMAT_VERSION
from .universe_backtest import (
    UniverseCase,
    _components,
    calibration_seed,
    future_observations,
    load_universe,
    summarize_paired,
)

_BASELINE = "Numeric v3"
_MAX_REPLAY_BYTES = 20_000_000
_MIN_TRAIN_CASES = 4
_MIN_HOLDOUT_CASES = 4


@dataclass(frozen=True)
class ReplayRecord:
    """One validated evidence response tied to a historical public cutoff."""

    unit_id: str
    cutoff: str
    reasoning: ReasoningResult


@dataclass(frozen=True)
class CalibrationDecision:
    """A family-level holdout decision suitable for an explicit deployment review."""

    family: str
    approved: bool
    candidate: str
    train_cases: int
    train_geometric_mean_ratio: float | None
    holdout_cases: int
    holdout_geometric_mean_ratio: float | None
    holdout_median_ratio: float | None
    holdout_win_rate: float | None
    holdout_worst_decile_ratio: float | None
    component_geometric_ratios: dict[str, float]
    reasons: list[str]


def _scaled_config(base: IntegrationConfig, scale: float) -> IntegrationConfig:
    """Scale one Phase-5 route without changing its qualitative family contract."""
    return IntegrationConfig(
        name=f"{base.name} x{scale:.2f}",
        mean_shift_sd=base.mean_shift_sd * scale,
        volatility_scale=base.volatility_scale * scale,
        tail_fraction=base.tail_fraction * scale,
        tail_scale_sd=base.tail_scale_sd * scale,
        rank_strength=base.rank_strength * scale,
        max_change_sd=base.max_change_sd * scale,
    )


def candidate_configs(family: str) -> tuple[IntegrationConfig, ...]:
    """Return a small predeclared grid; no holdout-driven parameter search is allowed."""
    base = FAMILY_CONFIGS[family]
    scales: tuple[float, ...]
    if family == "T2-F1":
        scales = (0.50, 1.00)
    elif family == "T2-F3":
        scales = (0.33, 0.67, 1.00, 1.33)
    else:
        scales = (0.50, 0.75, 1.00)
    return tuple(_scaled_config(base, scale) for scale in scales)


def _as_float(value: Any) -> float:
    """Narrow a pandas scalar at the boundary of the typed calibration logic."""
    return float(value)


def load_replay(
    path: pathlib.Path, root: pathlib.Path, expected_model_name: str | None = None
) -> list[ReplayRecord]:
    """Load JSONL model responses and fail closed on stale, duplicate, or uncited evidence."""
    if not path.is_file():
        raise ValueError(f"evidence replay does not exist: {path}")
    if path.stat().st_size > _MAX_REPLAY_BYTES:
        raise ValueError("evidence replay exceeds the safe input limit")
    universe = {case.unit_id: case for case in load_universe(root)}
    records: list[ReplayRecord] = []
    seen: set[tuple[str, str]] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"replay line {line_number} is not valid JSON") from exc
        expected = {
            "calibration_kind",
            "unit_id",
            "cutoff",
            "model_name",
            "interpreter_prompt_version",
            "interpreter_schema_version",
            "replay_format_version",
            "evidence",
        }
        if not isinstance(raw, dict) or set(raw) != expected:
            raise ValueError(f"replay line {line_number} must contain exactly {sorted(expected)}")
        unit_id = str(raw["unit_id"])
        cutoff = str(raw["cutoff"])
        try:
            cutoff = date.fromisoformat(cutoff).isoformat()
        except ValueError as exc:
            raise ValueError(f"replay line {line_number} has an invalid cutoff") from exc
        if unit_id not in universe:
            raise ValueError(f"replay line {line_number} names unknown unit {unit_id!r}")
        if not isinstance(raw["model_name"], str) or not raw["model_name"].strip():
            raise ValueError(f"replay line {line_number} has an empty model name")
        if raw["calibration_kind"] != CALIBRATION_KIND:
            raise ValueError(f"replay line {line_number} is not a {CALIBRATION_KIND!r} calibration")
        if raw["interpreter_prompt_version"] != INTERPRETER_PROMPT_VERSION:
            raise ValueError(
                f"replay line {line_number} uses interpreter prompt "
                f"{raw['interpreter_prompt_version']!r}, expected {INTERPRETER_PROMPT_VERSION!r}"
            )
        if raw["interpreter_schema_version"] != INTERPRETER_SCHEMA_VERSION:
            raise ValueError(
                f"replay line {line_number} uses interpreter schema "
                f"{raw['interpreter_schema_version']!r}, expected {INTERPRETER_SCHEMA_VERSION!r}"
            )
        if raw["replay_format_version"] != REPLAY_FORMAT_VERSION:
            raise ValueError(
                f"replay line {line_number} uses replay format "
                f"{raw['replay_format_version']!r}, expected {REPLAY_FORMAT_VERSION!r}"
            )
        key = (unit_id, cutoff)
        if key in seen:
            raise ValueError(f"duplicate replay case {unit_id}|{cutoff}")
        seen.add(key)
        case = universe[unit_id]
        corpus = read_frozen_corpus(root / "units" / unit_id / "text", cutoff)
        document_ids = {document.doc_id for document in corpus.documents}
        if not document_ids:
            raise ValueError(f"replay case {unit_id}|{cutoff} has no cutoff-safe documents")
        evidence = validate_evidence_response(
            raw["evidence"], assets=case.assets, document_ids=document_ids
        )
        # This also proves that the requested outcome exists after the cutoff.
        future_observations(case, cutoff)
        reasoning = ReasoningResult(
            applied=True,
            skipped_reason="",
            evidence=evidence,
            scenario_probabilities=scenario_probability_ledger(evidence, case.family),
            corpus=corpus,
            model_name=str(raw["model_name"])[:200],
        )
        records.append(ReplayRecord(unit_id, cutoff, reasoning))
    if not records:
        raise ValueError("evidence replay contains no cases")
    model_names = {record.reasoning.model_name for record in records}
    if len(model_names) != 1:
        raise ValueError("an evidence replay must use exactly one model name")
    actual_model_name = next(iter(model_names))
    if expected_model_name is not None and actual_model_name != expected_model_name:
        raise ValueError(
            f"evidence replay model {actual_model_name!r} does not match expected model "
            f"{expected_model_name!r}"
        )
    return sorted(records, key=lambda record: (record.cutoff, record.unit_id))


def _histories_at(case: UniverseCase, cutoff: str) -> dict[str, pd.Series]:
    return {
        asset: series[series.index.astype(str).str.slice(0, 10) <= cutoff]
        for asset, series in case.histories.items()
    }


def run_scenario_backtest(
    root: pathlib.Path,
    records: list[ReplayRecord],
    n_draws: int,
    *,
    seed_salt: str = "phase6-v1",
    configs_by_family: dict[str, tuple[IntegrationConfig, ...]] | None = None,
) -> pd.DataFrame:
    """Evaluate Numeric v3 and predeclared integration candidates on identical base draws."""
    universe = {case.unit_id: case for case in load_universe(root)}
    rows: list[dict[str, Any]] = []
    for record in records:
        case = universe[record.unit_id]
        histories = _histories_at(case, record.cutoff)
        observed = future_observations(case, record.cutoff)
        seed = calibration_seed(case.unit_id, record.cutoff, case.family, n_draws, seed_salt)
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
        common = {
            "unit_id": case.unit_id,
            "family": case.family,
            "cutoff": record.cutoff,
            "model_name": record.reasoning.model_name,
        }
        base_samples = numeric.samples.copy()
        rows.append(
            {
                **common,
                "candidate": _BASELINE,
                **_components(base_samples.reshape(n_draws, -1), observed),
            }
        )
        candidates = (
            configs_by_family.get(case.family, ())
            if configs_by_family is not None
            else candidate_configs(case.family)
        )
        for config in candidates:
            integrated = integrate_scenario_worlds(
                base_samples.copy(),
                record.reasoning,
                case.assets,
                case.horizons,
                case.family,
                seed,
                config_override=config,
            )
            rows.append(
                {
                    **common,
                    "candidate": config.name,
                    **_components(integrated.samples.reshape(n_draws, -1), observed),
                }
            )
    return pd.DataFrame(rows)


def _split_case_keys(frame: pd.DataFrame) -> tuple[set[tuple[str, str]], set[tuple[str, str]]]:
    keys = sorted(
        {(str(row.unit_id), str(row.cutoff)) for row in frame.itertuples()},
        key=lambda key: (key[1], key[0]),
    )
    dates = sorted({key[1] for key in keys})
    candidates: list[tuple[float, set[tuple[str, str]], set[tuple[str, str]]]] = []
    for date_index in range(1, len(dates)):
        train_dates = set(dates[:date_index])
        train = {key for key in keys if key[1] in train_dates}
        holdout = set(keys) - train
        if len(train) < _MIN_TRAIN_CASES or len(holdout) < _MIN_HOLDOUT_CASES:
            continue
        distance_from_target = abs(len(train) / len(keys) - 0.60)
        candidates.append((distance_from_target, train, holdout))
    if not candidates:
        return set(), set()
    _, train, holdout = min(candidates, key=lambda item: item[0])
    return train, holdout


def _select(frame: pd.DataFrame, keys: set[tuple[str, str]]) -> pd.DataFrame:
    mask = [
        (str(row.unit_id), str(row.cutoff)) in keys
        for row in frame[["unit_id", "cutoff"]].itertuples(index=False)
    ]
    return frame.loc[mask].copy()


def _component_geometric_ratios(frame: pd.DataFrame, candidate: str) -> dict[str, float]:
    keys = ["unit_id", "family", "cutoff"]
    baseline = frame[frame["candidate"] == _BASELINE].set_index(keys)
    selected = frame[frame["candidate"] == candidate].set_index(keys)
    ratios: dict[str, float] = {}
    for component in ("marginal", "joint", "tail"):
        denominator = baseline[component]
        valid = denominator > 1e-12
        if not valid.any():
            continue
        values = (selected.loc[valid, component] / denominator.loc[valid]).clip(lower=1e-12)
        ratios[component] = float(np.exp(np.log(values).mean()))
    return ratios


def calibrate(detail: pd.DataFrame) -> tuple[pd.DataFrame, list[CalibrationDecision]]:
    """Select on older cases and approve only on newer cases with family-specific guards."""
    if detail.empty:
        raise ValueError("scenario backtest produced no rows")
    decisions: list[CalibrationDecision] = []
    summaries: list[pd.DataFrame] = []
    for family, family_frame in detail.groupby("family", sort=True):
        model_names = set(family_frame["model_name"].astype(str))
        if len(model_names) != 1:
            decisions.append(
                CalibrationDecision(
                    family=str(family),
                    approved=False,
                    candidate="",
                    train_cases=0,
                    train_geometric_mean_ratio=None,
                    holdout_cases=0,
                    holdout_geometric_mean_ratio=None,
                    holdout_median_ratio=None,
                    holdout_win_rate=None,
                    holdout_worst_decile_ratio=None,
                    component_geometric_ratios={},
                    reasons=["a family replay must use exactly one model version"],
                )
            )
            continue
        train_keys, holdout_keys = _split_case_keys(family_frame)
        if not train_keys or not holdout_keys:
            decisions.append(
                CalibrationDecision(
                    family=str(family),
                    approved=False,
                    candidate="",
                    train_cases=len(train_keys),
                    train_geometric_mean_ratio=None,
                    holdout_cases=len(holdout_keys),
                    holdout_geometric_mean_ratio=None,
                    holdout_median_ratio=None,
                    holdout_win_rate=None,
                    holdout_worst_decile_ratio=None,
                    component_geometric_ratios={},
                    reasons=["at least four training and four holdout cases are required"],
                )
            )
            continue
        train = _select(family_frame, train_keys)
        holdout = _select(family_frame, holdout_keys)
        train_summary = summarize_paired(train, _BASELINE)
        candidates = train_summary.drop(index=_BASELINE, errors="ignore")
        winner = str(candidates["geometric_mean_ratio"].idxmin())
        train_ratio = _as_float(train_summary.loc[winner, "geometric_mean_ratio"])
        holdout_summary = summarize_paired(holdout, _BASELINE)
        row = holdout_summary.loc[winner]
        component_ratios = _component_geometric_ratios(holdout, winner)
        reasons: list[str] = []
        if family != "T2-F4":
            reasons.append("only F4 has enough independent public proxy cases for approval")
        if _as_float(row["geometric_mean_ratio"]) >= 1.0:
            reasons.append("holdout geometric mean did not beat Numeric v3")
        if _as_float(row["median_ratio"]) > 1.02:
            reasons.append("holdout median exceeded the 1.02 guard")
        if _as_float(row["win_rate"]) < 0.50:
            reasons.append("holdout win rate was below 50%")
        if _as_float(row["worst_decile_ratio"]) > 1.10:
            reasons.append("holdout worst decile exceeded the 1.10 guard")
        if component_ratios.get("marginal", 1.0) > 1.03:
            reasons.append("marginal component worsened by more than 3%")
        if component_ratios.get("tail", 1.0) > 1.05:
            reasons.append("tail component worsened by more than 5%")
        if family == "T2-F3":
            if abs(component_ratios.get("marginal", 1.0) - 1.0) > 1e-10:
                reasons.append("F3 changed the protected marginal component")
            if abs(component_ratios.get("tail", 1.0) - 1.0) > 1e-10:
                reasons.append("F3 changed the protected tail component")
        decision = CalibrationDecision(
            family=str(family),
            approved=not reasons,
            candidate=winner,
            train_cases=len(train_keys),
            train_geometric_mean_ratio=train_ratio,
            holdout_cases=len(holdout_keys),
            holdout_geometric_mean_ratio=_as_float(row["geometric_mean_ratio"]),
            holdout_median_ratio=_as_float(row["median_ratio"]),
            holdout_win_rate=_as_float(row["win_rate"]),
            holdout_worst_decile_ratio=_as_float(row["worst_decile_ratio"]),
            component_geometric_ratios=component_ratios,
            reasons=reasons,
        )
        decisions.append(decision)
        train_labelled = train_summary.copy()
        train_labelled.insert(0, "family", family)
        train_labelled.insert(1, "split", "candidate_selection")
        train_labelled.insert(2, "selected_on_train", train_labelled.index == winner)
        labelled = holdout_summary.copy()
        labelled.insert(0, "family", family)
        labelled.insert(1, "split", "untouched_holdout")
        labelled.insert(2, "selected_on_train", labelled.index == winner)
        summaries.extend((train_labelled, labelled))
    combined = pd.concat(summaries) if summaries else pd.DataFrame()
    return combined, decisions


def write_results(
    output_dir: pathlib.Path,
    detail: pd.DataFrame,
    summary: pd.DataFrame,
    decisions: list[CalibrationDecision],
) -> None:
    """Write diagnostics only; deployment still requires an explicit reviewed code change."""
    output_dir.mkdir(parents=True, exist_ok=True)
    detail.to_parquet(output_dir / "scenario_backtest_detail.parquet", index=False)
    summary.to_csv(output_dir / "scenario_candidate_summary.csv")
    if not summary.empty:
        summary[summary["split"] == "untouched_holdout"].to_csv(
            output_dir / "scenario_holdout_summary.csv"
        )
    payload = {
        "status": "public_nemotron_proxy_diagnostic_not_official_score",
        "calibration_kind": CALIBRATION_KIND,
        "interpreter_prompt_version": INTERPRETER_PROMPT_VERSION,
        "interpreter_schema_version": INTERPRETER_SCHEMA_VERSION,
        "replay_format_version": REPLAY_FORMAT_VERSION,
        "model_name": (str(detail["model_name"].iloc[0]) if not detail.empty else ""),
        "deployment_changed": False,
        "decisions": [asdict(decision) for decision in decisions],
    }
    (output_dir / "calibration_decisions.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase-5 scenario integration calibration")
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path("."))
    parser.add_argument("--replay", type=pathlib.Path, required=True)
    parser.add_argument("--output-dir", type=pathlib.Path, required=True)
    parser.add_argument("--n-draws", type=int, default=1000)
    parser.add_argument("--seed-salt", default="phase6-v1")
    parser.add_argument(
        "--expected-model-name",
        default=os.environ.get("CALIBRATION_MODEL_NAME", "").strip(),
        help="must match every replay record; defaults to CALIBRATION_MODEL_NAME",
    )
    args = parser.parse_args()
    if not args.expected_model_name:
        parser.error("--expected-model-name or CALIBRATION_MODEL_NAME is required")
    records = load_replay(args.replay, args.root, args.expected_model_name)
    detail = run_scenario_backtest(args.root, records, args.n_draws, seed_salt=args.seed_salt)
    summary, decisions = calibrate(detail)
    write_results(args.output_dir, detail, summary, decisions)
    for decision in decisions:
        state = "APPROVE" if decision.approved else "REJECT"
        print(f"{decision.family}: {state} {decision.candidate or '(no candidate)'}")
        for reason in decision.reasons:
            print(f"  - {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

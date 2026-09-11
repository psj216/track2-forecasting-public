"""Track-2 Numeric v3 plus Phase-5 scenario-integration submission CLI.

Implements the `forecast` verb from the shared submission contract:

    forecast --panels /input/panels/ --text /input/text/ --asof YYYY-MM-DD \
             --out /output/forecast.parquet

and writes the three deliverables the contract requires next to `--out`:

    forecast.parquet         the scored artifact — joint draws [draw, asset, horizon, value]
    forecast_meta.json       the sidecar g1_schema validates
    forecast_rationale.md    required, NEVER scored — the derivation, for human review

The numeric implementation separates level and log-return targets, respects the panel observation
frequency, detects regime fragility, and samples joint paths from recent, full-history and
state-matched historical blocks. F3 cards add a calibrated latent-factor transmission layer that
changes joint draw pairing without changing marginal distributions. The text layer reads the
frozen corpus and extracts grounded competing views and scenario evidence. Phase 5 converts that
validated evidence into bounded family-specific scenario worlds in deterministic Python.

It runs offline as an explicitly labelled Numeric v3 fallback. In evaluated reasoning runs, its
only network call is the organizer-compatible model endpoint configured by the environment.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from typing import Any

import numpy as np
import pandas as pd

from .limits import ParseLimits
from .numeric_v3 import forecast_numeric_v3
from .scenario_integration import (
    APPROVED_F4_CONFIG,
    IntegrationResult,
    integrate_scenario_worlds,
)
from .text_evidence import (
    CorpusResult,
    ReasoningResult,
    interpret_text_evidence,
    scenario_probability_ledger,
)

DEFAULT_DRAWS = 500
_RATIONALE_NAME = "forecast_rationale.md"
_FORECAST_MODES = {"numeric", "f4-only", "full"}


def _forecast_mode() -> str:
    """Return the baked Development experiment mode or reject an ambiguous image."""
    mode = os.environ.get("FORECAST_MODE", "full").strip().lower()
    if mode not in _FORECAST_MODES:
        raise SystemExit(f"FORECAST_MODE must be one of {sorted(_FORECAST_MODES)}, got {mode!r}")
    return mode


def _numeric_reasoning(family: str, reason: str) -> ReasoningResult:
    """Create an explicit text-ablated ledger without reading text or calling the endpoint."""
    return ReasoningResult(
        applied=False,
        skipped_reason=reason,
        evidence=None,
        scenario_probabilities=scenario_probability_ledger(None, family),
        corpus=CorpusResult((), 0, 0, 0, 0, 0),
        model_name="",
    )


def _read_panels(panels_dir: pathlib.Path) -> dict[str, pd.DataFrame]:
    """Every parquet under --panels, keyed by filename stem.

    Accepts the contract layout (`/input/panels/*.parquet`) and also tolerates a unit that keeps
    its panels one level up, which is how the shipped exemplar was laid out before this CLI
    existed. Tolerating it here means a card authored either way still runs.
    """
    found = sorted(panels_dir.glob("*.parquet"))
    if not found and panels_dir.parent.is_dir():
        found = sorted(panels_dir.parent.glob("*.parquet"))
    if not found:
        raise SystemExit(f"no .parquet found under {panels_dir} (or its parent)")
    return {p.stem: pd.read_parquet(p) for p in found}


#: Both spellings occur in the shipped cards — the exemplar unit uses `asset_id`, the pilot and
#: prospective batches use `asset`. A reference implementation has to read either, or it works on
#: some cards and not others for a reason that has nothing to do with forecasting.
_ASSET_COLS = ("asset", "asset_id")


def _asset_col(df: pd.DataFrame) -> str | None:
    return next((c for c in _ASSET_COLS if c in df.columns), None)


def _series(panels: dict[str, pd.DataFrame], asset: str, asof: str) -> pd.Series:
    """The history of one asset up to and including the as-of, from whichever panel holds it."""
    for df in panels.values():
        col = _asset_col(df)
        if col is None:
            continue
        sub = df[df[col].astype(str) == asset]
        if sub.empty:
            continue
        sub = sub.copy()
        # Dates arrive as either strings or datetimes depending on how the panel was written.
        sub["date"] = sub["date"].astype(str).str.slice(0, 10)
        sub = sub[sub["date"] <= asof].sort_values("date")
        if not sub.empty:
            return sub.set_index("date")["value"].astype(float)
    seen = sorted(
        {
            str(v)
            for df in panels.values()
            if (c := _asset_col(df)) is not None
            for v in df[c].unique()
        }
    )
    raise SystemExit(
        f"asset {asset!r} not present in any panel at or before {asof}. "
        f"Panels carry: {', '.join(seen) if seen else '(no asset column found)'}"
    )


def _draw(
    panels: dict[str, pd.DataFrame],
    assets: list[str],
    horizons: list[int],
    asof: str,
    n_draws: int,
    seed: int,
    target_type: str = "level",
    target_frequency: str = "daily",
    family: str = "T2-F1",
) -> tuple[np.ndarray, dict[str, Any]]:
    """Target-aware joint block bootstrap with regime diagnostics and coherent horizons."""
    hist = {a: _series(panels, a, asof) for a in assets}
    try:
        result = forecast_numeric_v3(
            hist,
            assets,
            horizons,
            target_type,
            target_frequency,
            n_draws,
            seed,
            family,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    return result.samples, result.metadata


def _rationale(
    unit_id: str,
    asof: str,
    assets: list[str],
    horizons: list[int],
    n_draws: int,
    stats: dict[str, Any],
    text_dir: pathlib.Path,
    reasoning: ReasoningResult,
    integration: IntegrationResult,
) -> str:
    # Document accounting comes from the cutoff-safe corpus reader, not a directory glob.
    del text_dir
    transmission = stats.get("transmission")
    if transmission:
        transmission_note = (
            "F3 routing applied dynamic latent-factor transmission at strength "
            f"{transmission['strength']:.2f}. The first latent factor explains "
            f"{transmission['first_factor_variance_share']:.1%} of the target correlation "
            "structure. Marginal draw values were rank-preserved exactly; only their joint "
            "pairing changed."
        )
    else:
        transmission_note = (
            "The family router did not apply cross-asset transmission. The V2.1 joint paths "
            "were retained exactly."
        )
    ladder = "\n".join(
        f"| {a} | {stats['anchor'][a]:.4f} | {stats['daily_sd'][a]:.4f} | "
        f"{stats['daily_sd'][a] * np.sqrt(h):.4f} | {h} |"
        for a in assets
        for h in horizons
    )
    if reasoning.applied and reasoning.evidence:
        state = reasoning.evidence["market_state"]
        scenario_rows = "\n".join(
            f"| {name} | {probability:.3f} |"
            for name, probability in sorted(
                reasoning.scenario_probabilities.items(), key=lambda item: item[1], reverse=True
            )
        )
        view_rows = "\n".join(
            f"| {name} | {str(view['thesis']).replace('|', '/').replace(chr(10), ' ')} | "
            f"{view['confidence']:.2f} |"
            for name, view in reasoning.evidence["views"].items()
        )
        document_count = len(reasoning.corpus.documents)
        skeptic_challenge = (
            str(reasoning.evidence["skeptic"]["challenge"]).replace("|", "/").replace(chr(10), " ")
        )
        integration_meta = integration.metadata
        if integration_meta["applied"]:
            integration_note = (
                f"Phase 5 applied **{integration_meta['config']}**. "
                f"Marginals preserved exactly: "
                f"**{integration_meta.get('marginals_preserved_exactly', False)}**. "
                f"Shock draws: **{integration_meta.get('shock_draw_count', 0)}**."
            )
        else:
            integration_note = (
                "The evidence remained shadow-only and Numeric v3 was retained exactly: "
                f"**{integration_meta['reason']}**."
            )
        text_section = f"""The evidence interpreter read **{document_count}** dated document(s).
It classified the market state as **{state['label']}** with evidence confidence
**{state['confidence']:.2f}**. The model supplied evidence scores, not forecast probabilities.
Python converted those scores into this probability ledger:

| scenario | Python probability |
|---|---:|
{scenario_rows}

| competing view | thesis | evidence confidence |
|---|---|---:|
{view_rows}

Skeptic challenge: {skeptic_challenge}

{integration_note}"""
    else:
        text_section = f"""No text interpretation was applied: **{reasoning.skipped_reason}**.
The cutoff-safe reader found {len(reasoning.corpus.documents)} usable document(s) from
{reasoning.corpus.indexed_count} indexed entries. Numeric v3 was retained exactly."""

    return f"""# Forecast rationale — {unit_id}

As of **{asof}**, joint distribution over {", ".join(assets)} at horizon(s)
{", ".join(str(h) for h in horizons)} business days. {n_draws} draws.

## Target and anchor

Target type: **{stats["target_type"]}**. Level forecasts start from the last observed level.
Return forecasts start from zero and accumulate daily returns. The engine used
{stats["n_history_rows"]} overlapping rows dated no later than the as-of.

## Adjustments

The centre uses a strongly shrunk blend of 20, 60, 120 and long-window daily drift. It is capped
relative to forecast uncertainty so a short trend cannot dominate a long horizon.

## Scale and shape

Five-observation historical blocks are sampled from recent, full-history and state-matched pools.
A requested business-day horizon is mapped to the panel's observation frequency before sampling;
this panel represents approximately {stats['observation_period_business_days']} business day(s)
per observation. A
matched block had a similar prior 20/120-day volatility ratio and momentum, using no future
information. {stats['sampling']['state_matched_block_count']} historical blocks qualified.
Current fragility is
**{stats['regime']['fragility']:.3f}**; recent-history weight is
**{stats['regime']['recent_weight']:.3f}** and uncertainty scale is
**{stats['regime']['uncertainty_scale']:.3f}**.

The draws are **joint**: each sampled block contains every asset. Each draw is also one path
through time, and every requested horizon is read from that same path.

{transmission_note}

## Adjustment ledger

| asset | model anchor | effective daily sd | sd at horizon | horizon (BD) |
|---|---|---|---|---|
{ladder}

Daily drift: {stats['daily_drift']}.

## What the text corpus contributed

{text_section}

## What would change this forecast

New numeric observations that change momentum, volatility, correlation or fragility, or a dated
document that contradicts the cited evidence. Post-as-of information is never eligible.
"""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="forecast",
        description="QFBench 2.0 Track-2 Numeric v3 submission.",
    )
    p.add_argument("--panels", type=pathlib.Path, required=True)
    p.add_argument("--text", type=pathlib.Path, required=True)
    p.add_argument("--asof", required=True)
    p.add_argument(
        "--out",
        type=pathlib.Path,
        required=True,
        help="path to forecast.parquet; the sidecars are written beside it",
    )
    p.add_argument(
        "--card",
        type=pathlib.Path,
        default=None,
        help="card.toml; defaults to <panels>/../card.toml. Supplies assets/horizons.",
    )
    p.add_argument("--n-draws", type=int, default=None)
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args(argv)

    # --panels names the unit root (contract) but a card may still keep a panels/ subdir, so look
    # in the panels dir first and only then one level up. Deriving it as parent/ unconditionally
    # resolves to "/" when --panels is /input/, which is how this was wrong the first time.
    card_path = a.card
    if card_path is None:
        for cand in (a.panels / "card.toml", a.panels.parent / "card.toml"):
            if cand.exists():
                card_path = cand
                break
    if card_path is None or not card_path.exists():
        raise SystemExit(
            f"card.toml not found in {a.panels} or {a.panels.parent}; pass --card explicitly"
        )
    import tomllib

    card = tomllib.loads(card_path.read_text())
    tgt = card["targets"]
    assets = list(tgt["asset_ids"])
    horizons = [int(h) for h in tgt["horizons"]]
    unit_id = card["task"]["id"]
    family = str(card["metadata"]["category"])
    # The card's `n_draws_min` is AUTHORITATIVE and was previously advisory: the reference
    # producer read it, the scorer never did, and the scorer instead compared the submission
    # against the participant's own declared `n_draws`. It is now a floor on both sides — this
    # producer honours it, and `limits.min_draws` enforces the contract floor in the scorer, in
    # code no missing module can skip.
    card_floor = int(card.get("scoring", {}).get("params", {}).get("n_draws_min", 0) or 0)
    floor = max(card_floor, DEFAULT_DRAWS, ParseLimits().min_draws)
    n_draws = max(a.n_draws or floor, floor)
    if n_draws > ParseLimits().max_draws:
        raise SystemExit(
            f"--n-draws {n_draws} exceeds the contract ceiling {ParseLimits().max_draws}; the "
            "scorer refuses a submission above it"
        )

    panels = _read_panels(a.panels)
    target_type = str(tgt.get("target_type", "level"))
    target_frequency = str(tgt.get("target_frequency", "daily"))
    samples, stats = _draw(
        panels,
        assets,
        horizons,
        a.asof,
        n_draws,
        a.seed,
        target_type=target_type,
        target_frequency=target_frequency,
        family=family,
    )

    panel_context = {
        "value_unit": str(tgt.get("value_unit", "unspecified")),
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
    forecast_mode = _forecast_mode()
    reasoning_enabled = forecast_mode == "full" or (
        forecast_mode == "f4-only" and family == "T2-F4"
    )
    if reasoning_enabled:
        reasoning = interpret_text_evidence(
            text_dir=a.text,
            unit_id=unit_id,
            family=family,
            asof=a.asof,
            assets=assets,
            horizons=horizons,
            target_type=target_type,
            target_frequency=target_frequency,
            panel_context=panel_context,
            numeric_context=numeric_context,
        )
    else:
        reasoning = _numeric_reasoning(
            family, f"FORECAST_MODE={forecast_mode} disables reasoning for {family}"
        )
    integration_setting = os.environ.get("TEXT_INTEGRATION", "on").strip().lower()
    if integration_setting not in {"1", "true", "on", "0", "false", "off"}:
        raise SystemExit("TEXT_INTEGRATION must be one of on/off, true/false, or 1/0")
    integration_enabled = integration_setting in {"1", "true", "on"}

    # Public Nemotron F4 calibration approved the frozen half-strength route.
    # Numeric mode and F1-F3 remain unchanged.
    approved_config = (
        APPROVED_F4_CONFIG
        if reasoning_enabled and family == "T2-F4"
        else None
    )

    try:
        integration = integrate_scenario_worlds(
            samples,
            reasoning,
            assets,
            horizons,
            family,
            a.seed,
            enabled=integration_enabled,
            config_override=approved_config,
        )
    except ValueError as exc:
        integration = IntegrationResult(
            samples=samples.copy(),
            metadata={
                "enabled": integration_enabled,
                "family": family,
                "applied": False,
                "numeric_fallback_exact": True,
                "reason": f"integration rejected: {exc}",
            },
        )
    samples = integration.samples

    out_dir = a.out.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {"draw": d, "asset": asset, "horizon": h, "value": float(samples[d, ai, hi])}
            for d in range(n_draws)
            for ai, asset in enumerate(assets)
            for hi, h in enumerate(horizons)
        ]
    ).to_parquet(a.out, index=False)

    (out_dir / "forecast_meta.json").write_text(
        json.dumps(
            {
                "unit_id": unit_id,
                "asof": a.asof,
                "representation": "samples",
                "asset_ids": assets,
                "horizons": horizons,
                "n_draws": n_draws,
                "target": target_type,
                "forecast_mode": forecast_mode,
                "reasoning_applied": reasoning.applied,
                "reasoning_skipped_reason": reasoning.skipped_reason,
                "forecast_adjustment_applied": integration.metadata["applied"],
                "rationale": {
                    "file": _RATIONALE_NAME,
                    "method": (
                        f"Numeric v3 + {integration.metadata['config']}"
                        if integration.metadata["applied"]
                        else "Numeric v3 + explicit text-integration fallback"
                    ),
                    "text_evidence": reasoning.metadata(
                        mode="integrated" if integration.metadata["applied"] else "shadow",
                        forecast_adjustment_applied=bool(integration.metadata["applied"]),
                    ),
                    "scenario_integration": integration.metadata,
                },
            },
            indent=2,
        )
        + "\n"
    )

    (out_dir / _RATIONALE_NAME).write_text(
        _rationale(
            unit_id,
            a.asof,
            assets,
            horizons,
            n_draws,
            stats,
            a.text,
            reasoning,
            integration,
        )
    )

    print(f"wrote {a.out.name}, forecast_meta.json and {_RATIONALE_NAME} to {out_dir}")
    print(f"  {len(assets)} asset(s) x {len(horizons)} horizon(s), {n_draws} draws")
    print(f"  forecast mode: {forecast_mode}")
    print(
        f"  text evidence: applied={reasoning.applied}, "
        f"documents={len(reasoning.corpus.documents)}"
        + (f", skipped={reasoning.skipped_reason}" if not reasoning.applied else "")
    )
    print(
        f"  scenario integration: applied={integration.metadata['applied']}"
        + (
            f", fallback={integration.metadata['reason']}"
            if not integration.metadata["applied"]
            else ""
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

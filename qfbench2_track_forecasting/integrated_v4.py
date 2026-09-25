"""## Executive summary (read this first)

Apply small, state-gated F1/F2/F4 changes to frozen Numeric V3 draws. F3 is
exactly unchanged. F2 needs dated, explicit target direction in actual text;
weak or absent evidence leaves the numeric anchor unchanged. F4 stress worlds
are real historical joint paths from before the forecast cutoff.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from .historical_heads import apply_historical_head
from .numeric_v1 import _diff_without_gaps, _observation_period_business_days
from .regime_router import RegimeDecision
from .text_evidence import read_frozen_corpus


@dataclass(frozen=True)
class IntegratedConfig:
    """Freeze all numeric strengths before later validation folds are scored."""

    name: str
    f1_strength: float
    f4_calm_strength: float
    f4_stress_strength: float
    f4_stress_sleeve: float
    f2_sleeve: float


CONFIGS = (
    IntegratedConfig("integrated-conservative", 0.10, 0.08, 0.08, 0.04, 0.05),
    IntegratedConfig("integrated-moderate", 0.18, 0.12, 0.12, 0.07, 0.08),
    IntegratedConfig("integrated-strong", 0.25, 0.18, 0.18, 0.10, 0.10),
)


def _history_steps(
    histories: dict[str, pd.Series], assets: list[str], target_type: str, asof: str
) -> pd.DataFrame:
    cutoff = pd.Timestamp(asof)
    prepared = {}
    for asset in assets:
        series = histories[asset].sort_index().astype(float)
        series = series.loc[pd.to_datetime(series.index) <= cutoff]
        prepared[asset] = (
            series if target_type in {"log_return", "return"} else _diff_without_gaps(series)
        )
    return pd.DataFrame(prepared).replace([np.inf, -np.inf], np.nan).dropna().tail(2520)


def _vol_state(steps: pd.DataFrame) -> tuple[float, float, float]:
    if len(steps) < 150:
        return 1.0, 0.0, 0.0
    short = steps.tail(20).std().clip(lower=1e-8)
    long = steps.tail(252).std().clip(lower=1e-8)
    ratio = float(np.median((short / long).clip(0.1, 10).to_numpy()))
    momentum = float(np.median((steps.tail(20).sum() / (long * np.sqrt(20))).to_numpy()))
    previous = steps.iloc[-40:-20].std().clip(lower=1e-8)
    persistence = float(np.median((previous / long).clip(0.1, 10).to_numpy()))
    return ratio, momentum, persistence


def _scale(samples: NDArray[np.float64], factors: NDArray[np.float64]) -> NDArray[np.float64]:
    center = np.median(samples, axis=0)
    return np.asarray(center + (samples - center) * factors[None, None, :], dtype=np.float64)


def _explicit_direction(
    text_dir: Path | None, asof: str, asset: str
) -> tuple[int, tuple[str, ...], str]:
    """Require a recent document to say the literal asset and rise/fall in one sentence."""
    if text_dir is None:
        return 0, (), "continuation"
    try:
        corpus = read_frozen_corpus(text_dir, asof)
    except (OSError, ValueError, TypeError):
        return 0, (), "continuation"
    directions: list[tuple[int, str, str]] = []
    for doc in corpus.documents:
        age = (pd.Timestamp(asof) - pd.Timestamp(doc.timestamp)).days
        if age > 45:
            continue
        for sentence in re.split(r"[.!?\n]", doc.text):
            if not re.search(rf"(?<!\w){re.escape(asset)}(?!\w)", sentence, re.IGNORECASE):
                continue
            up = bool(re.search(r"\b(rise|rises|rose|higher|increase|increases)\b", sentence, re.I))
            down = bool(
                re.search(r"\b(fall|falls|fell|lower|decrease|decreases)\b", sentence, re.I)
            )
            if up != down:
                regimes = [
                    label
                    for label, terms in (
                        ("policy_shift", r"\b(policy|rate|hike|cut|qe|tighten|eas)\w*\b"),
                        ("inflation_shift", r"\b(inflation|cpi|price)\w*\b"),
                        ("growth_shift", r"\b(growth|recession|output)\w*\b"),
                        ("liquidity_stress", r"\b(liquidity|funding|credit)\w*\b"),
                    )
                    if re.search(terms, sentence, re.I)
                ]
                if len(regimes) == 1:
                    directions.append((1 if up else -1, doc.doc_id, regimes[0]))
    if (
        not directions
        or len({direction for direction, _, _ in directions}) != 1
        or len({regime for _, _, regime in directions}) != 1
    ):
        return 0, (), "continuation"
    return (
        directions[0][0],
        tuple(sorted({doc_id for _, doc_id, _ in directions})),
        directions[0][2],
    )


def _stress_worlds(
    samples: NDArray[np.float64],
    steps: pd.DataFrame,
    histories: dict[str, pd.Series],
    assets: list[str],
    horizons: list[int],
    target_type: str,
    frequency: str,
    sleeve: float,
    seed: int,
) -> tuple[NDArray[np.float64], int]:
    if target_type not in {"level", "log_return"}:
        return samples.copy(), 0
    period = 1 if frequency == "daily" else _observation_period_business_days(steps)
    observed_horizons = np.maximum(1, np.ceil(np.asarray(horizons) / period).astype(int))
    maximum = int(observed_horizons.max())
    values = steps.to_numpy(dtype=float)
    if len(values) < maximum + 100:
        return samples.copy(), 0
    accumulated = np.vstack((np.zeros((1, len(assets))), np.cumsum(values, axis=0)))
    starts = np.arange(len(values) - maximum + 1)
    calendar = pd.DatetimeIndex(steps.index).to_numpy(dtype="datetime64[D]")
    gaps = np.r_[False, np.busday_count(calendar[:-1], calendar[1:]) > max(5, 2 * period)]
    gap_count = np.r_[0, np.cumsum(gaps.astype(int))]
    starts = starts[(gap_count[starts + maximum] - gap_count[starts + 1]) == 0]
    if len(starts) < 100:
        return samples.copy(), 0
    long_moves = accumulated[starts + maximum] - accumulated[starts]
    magnitude = np.max(
        np.abs(long_moves / np.maximum(steps.std().to_numpy() * np.sqrt(maximum), 1e-8)), axis=1
    )
    eligible = starts[magnitude >= np.quantile(magnitude, 0.90)]
    separated = 0
    previous = -maximum
    for start in eligible:
        if start - previous >= maximum:
            separated += 1
            previous = int(start)
    if len(eligible) < 10 or separated < 3:
        return samples.copy(), 0
    count = min(len(samples), int(np.floor(len(samples) * sleeve)))
    if count == 0:
        return samples.copy(), 0
    rng = np.random.default_rng(seed ^ 0xF440)
    chosen = rng.choice(len(samples), count, replace=False)
    starts = rng.choice(eligible, count, replace=True)
    paths = accumulated[starts[:, None] + observed_horizons[None, :]] - accumulated[starts, None]
    paths = paths.transpose(0, 2, 1)
    if target_type == "level":
        anchors = np.array(
            [
                histories[a].loc[pd.to_datetime(histories[a].index) <= steps.index[-1]].iloc[-1]
                for a in assets
            ],
            dtype=float,
        )
        paths += anchors[None, :, None]
    result = samples.copy()
    result[chosen] = paths
    return result, count


def apply_integrated_v4(
    samples: NDArray[np.float64],
    histories: dict[str, pd.Series],
    assets: list[str],
    horizons: list[int],
    target_type: str,
    target_frequency: str,
    family: str,
    asof: str,
    seed: int,
    config: IntegratedConfig,
    text_dir: Path | None = None,
) -> tuple[NDArray[np.float64], dict[str, Any]]:
    """Gate every intervention; return exact V3 whenever conditions are ambiguous."""
    meta: dict[str, Any] = {"config": config.name, "applied": False, "reason": "gate_closed"}
    if family == "T2-F3" or family not in {"T2-F1", "T2-F2", "T2-F4"}:
        return samples.copy(), meta
    if samples.ndim != 3 or samples.shape[1:] != (len(assets), len(horizons)):
        raise ValueError("invalid draw grid")
    if not np.isfinite(samples).all():
        raise ValueError("non-finite draws")
    steps = _history_steps(histories, assets, target_type, asof)
    ratio, momentum, persistence = _vol_state(steps)
    meta.update(vol_ratio=ratio, momentum=momentum, persistence=persistence)
    if len(steps) < 150:
        return samples.copy(), meta
    if family == "T2-F1":
        if target_type != "level":
            return samples.copy(), meta
        horizons_array = np.asarray(horizons, dtype=float)
        horizon_weight = np.clip(np.sqrt(horizons_array / 63.0), 0.5, 1.5)
        calm = float(np.clip((0.85 - ratio) / 0.40, 0, 1))
        calm *= float(np.clip((1.2 - abs(momentum)) / 1.2, 0, 1))
        stress = float(np.clip(min((ratio - 1.5) / 1.2, (persistence - 1.15) / 0.8), 0, 1))
        if calm >= 0.30:
            confidence, direction, reason = calm, -1, "calm_f1_width"
        elif stress >= 0.30:
            confidence, direction, reason = stress, 1, "stress_f1_width"
        else:
            return samples.copy(), meta
        factors = np.clip(
            1 + direction * config.f1_strength * confidence * horizon_weight, 0.85, 1.15
        )
        output = _scale(samples, factors)
        meta.update(applied=True, reason=reason, confidence=confidence, factors=factors.tolist())
        return output, meta
    if family == "T2-F2":
        if len(assets) != 1 or text_dir is None:
            return samples.copy(), meta
        direction, evidence, regime = _explicit_direction(text_dir, asof, assets[0])
        signal = momentum * direction
        if not evidence or signal < 0.35:
            return samples.copy(), meta
        confidence = float(np.clip((signal - 0.35) / 1.5, 0, 1))
        if confidence < 0.30:
            return samples.copy(), meta
        decision = RegimeDecision(
            regime,
            direction,
            0.65 + 0.35 * confidence,
            "none",
            "medium",
            evidence,
            assets[0],
        )
        output, head = apply_historical_head(
            samples,
            histories,
            assets,
            horizons,
            target_type,
            target_frequency,
            family,
            asof,
            seed,
            decision,
            evidence_valid=True,
            direction_asset=assets[0],
        )
        meta.update(
            applied=bool(head["applied"]),
            reason=head["reason"],
            confidence=confidence,
            evidence_count=len(evidence),
        )
        return output, meta
    if ratio < 0.75 and persistence < 1.0 and abs(momentum) < 1.0:
        confidence = float(np.clip((0.75 - ratio) / 0.50, 0, 1))
        if confidence >= 0.30:
            factor = max(0.88, 1 - config.f4_calm_strength * confidence)
            output = _scale(samples, np.full(len(horizons), factor))
            meta.update(applied=True, reason="calm_f4_width", confidence=confidence, factor=factor)
            return output, meta
    if ratio > 1.4 and persistence > 1.2:
        confidence = float(np.clip(min((ratio - 1.4) / 1.2, (persistence - 1.2) / 0.8), 0, 1))
        if confidence >= 0.30:
            factor = min(1.20, 1 + config.f4_stress_strength * confidence)
            expanded = _scale(samples, np.full(len(horizons), factor))
            output, count = _stress_worlds(
                expanded,
                steps,
                histories,
                assets,
                horizons,
                target_type,
                target_frequency,
                config.f4_stress_sleeve * confidence,
                seed,
            )
            meta.update(
                applied=True,
                reason="stress_f4_worlds",
                confidence=confidence,
                factor=factor,
                replacement_draws=count,
            )
            return output, meta
    return samples.copy(), meta

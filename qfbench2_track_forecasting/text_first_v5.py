"""## Executive summary (read this first)

Read only cutoff-safe documents, infer an economic event, and route a small
fraction of frozen Numeric V3 draws to real, pre-asof directional paths.
Ambiguous evidence, unsuitable assets, or insufficient historical episodes
return the exact original draws. F2 and F3 never enter this module.
"""

# Long regex literals are kept intact for review of each semantic event clause.
# ruff: noqa: E501

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from .integrated_v4 import _history_steps
from .numeric_v1 import _observation_period_business_days
from .text_evidence import read_frozen_corpus


@dataclass(frozen=True)
class Event:
    kind: str
    strength: float
    doc_ids: tuple[str, ...]
    excerpt: str


# Expressions describe events, not named validation cards or subsequent outcomes.
_EVENTS: tuple[tuple[str, str, int], ...] = (
    (
        "liquidity_stress",
        r"\b(funding (?:market )?(?:stress|strain|pressures?)|liquidity (?:shortage|strain|pressures?)|credit crunch|bank (?:failures?|runs?|distress)|systemic (?:risk|stress)|market dislocation|forced liquidation|financial conditions (?:deteriorat|tighten))\w*\b",
        3,
    ),
    (
        "growth_down",
        r"\b(economy (?:is |has )?(?:entering|in) recession|growth (?:is |has )?(?:slow(?:ed|ing)|weaken(?:ed|ing)|decelerat)|economic activity (?:is |has )?(?:declin|contract)|job losses (?:are |have )?(?:ris|increas)|unemployment (?:is |has )?(?:ris|increas)|coronavirus outbreak (?:has |is )?(?:harm|disrupt)|covid.19 (?:has |is )?(?:harm|disrupt))\w*\b",
        2,
    ),
    (
        "policy_tightening",
        r"\b(raise(?:d|s)? (?:the )?(?:policy |interest )?rate|rate hikes?|tighten(?:ing)? monetary policy|taper(?:ing)? (?:asset )?purchases|begin(?:ning)? balance.sheet runoff|withdraw(?:al of)? accommodation|higher for longer)\b",
        2,
    ),
    (
        "policy_easing",
        r"\b(cut(?:ting)? (?:the )?(?:policy |interest )?rate|lower(?:ed|ing)? (?:the )?(?:policy |interest )?rate|quantitative easing|expand(?:ing)? (?:asset )?purchases|additional accommodation|ease monetary policy)\b",
        2,
    ),
    (
        "inflation_up",
        r"\b(inflation (?:accelerat\w*|ris(?:es|ing|en)|remain(?:s|ed)? (?:too |persistently )?(?:high|elevated)|persist\w*)|price pressures? (?:increas\w*|ris(?:es|ing|en)|persist\w*)|inflation (?:above|exceed\w*))\b",
        2,
    ),
    (
        "inflation_down",
        r"\b(inflation (?:decelerat|declin|fall|eas|cool)|disinflation|price pressures? (?:eas|subsid)|downside inflation risk)\w*\b",
        2,
    ),
    (
        "trade_geopolitical",
        r"\b(trade (?:war|tensions?|barriers?|escalation)|tariff (?:increase|hike|threat)|geopolitical (?:risk|tension)|brexit (?:risk|uncertainty)|sovereign debt (?:crisis|stress)|debt.ceiling (?:impasse|standoff)|downgrade (?:risk|watch))\b",
        2,
    ),
    (
        "oil_supply_shock",
        r"\b(oil (?:supply (?:shock|disruption|cut)|price (?:collapse|surge))|crude (?:supply disruption|price collapse)|opec (?:production )?cut)\b",
        2,
    ),
    (
        "positioning_crowding",
        r"\b(crowded (?:trade|position)|positioning (?:extreme|unwind)|carry (?:trade )?unwind|short.volatility (?:trade|position)|forced (?:liquidation|selling)|margin calls?)\b",
        2,
    ),
    (
        "growth_up",
        r"\b(growth (?:accelerat|rebound)|economic activity (?:strengthen|rebound)|labor market (?:strengthen|improv))\w*\b",
        1,
    ),
)

_OPPOSITE = {
    "policy_tightening": "policy_easing",
    "inflation_up": "inflation_down",
    "growth_down": "growth_up",
}
_RISK = {"growth_down", "liquidity_stress", "trade_geopolitical", "positioning_crowding"}


def _event(text_dir: Path, asof: str) -> tuple[Event | None, dict[str, Any]]:
    try:
        corpus = read_frozen_corpus(text_dir, asof)
    except (OSError, ValueError, TypeError):
        return None, {"reason": "corpus_unavailable"}
    candidates: list[tuple[float, str, str, str]] = []
    for doc in corpus.documents:
        age = max(0, (pd.Timestamp(asof) - pd.Timestamp(doc.timestamp)).days)
        if age > 100:
            continue
        recency = max(0.45, 1 - age / 150)
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", doc.text):
            if not 25 <= len(sentence) <= 700:
                continue
            for kind, pattern, specificity in _EVENTS:
                m = re.search(pattern, sentence, flags=re.I)
                if not m:
                    continue
                prefix = sentence[max(0, m.start() - 32) : m.start()]
                if re.search(
                    r"\b(no|not|without|unlikely|avoid(?:ed)?|prevent(?:ed)?)\s+(?:\w+\s+){0,3}$",
                    prefix,
                    re.I,
                ):
                    continue
                if re.search(
                    r"\b(?:when the crisis hit|probability,? though minor|(?:minor|small) (?:probability|chance)|risks? (?:remain|are) (?:low|limited)|ten\s+words|bibliography|references|forthcoming|has its origins|years ago|the 2008 crisis|great recession|(?:banking|sovereign )?debt crisis (?:has|had|morphed|re.emergence)|recession which has touched|trade war .* (?:receded|less likely)|swap lines? (?:are|is) a (?:critical|important) tool)\b",
                    sentence,
                    re.I,
                ):
                    continue
                # A retrospective or a hypothetical example is not a current signal.
                if re.search(
                    r"\b(historic(?:al|ally)?|previous|past|last (?:crisis|recession)|since (?:the |last )?(?:global )?financial crisis|(?:back |in )(?:19\d\d|20\d\d)|at that time|(?:risk )?scenario where|if (?:there|the economy)|did not|not concerned)\b",
                    sentence,
                    re.I,
                ):
                    continue
                if kind == "liquidity_stress" and re.search(
                    r"\b(?:framework|lesson|approach|monitoring|stress test|regulation)\b",
                    sentence,
                    re.I,
                ):
                    continue
                if kind == "growth_down" and re.search(
                    r"\b(?:most adversely affected|have improved|continues to improve|potential|hypothetical)\b",
                    sentence,
                    re.I,
                ):
                    continue
                if kind == "liquidity_stress" and re.search(
                    r"\b(?:systemic risk board|financial cycles|market intelligence|contingency funding)\b",
                    sentence,
                    re.I,
                ):
                    continue
                if kind == "inflation_up" and re.search(
                    r"\b(?:while .* decelerat|although .* fall|in contrast, .* fall)\b",
                    sentence,
                    re.I,
                ):
                    continue
                # The title and opening paragraph usually carry the document's subject.
                salience = 1.20 if doc.text.find(sentence) < 750 else 1.0
                candidates.append(
                    (specificity * recency * salience, kind, doc.doc_id, sentence.strip()[:220])
                )
    if not candidates:
        return None, {"reason": "no_specific_event", "documents": len(corpus.documents)}
    scores: dict[str, float] = {}
    for score, kind, _, _ in candidates:
        scores[kind] = scores.get(kind, 0.0) + score
    leader = max(scores, key=scores.get)
    opposite = _OPPOSITE.get(leader) or next((k for k, v in _OPPOSITE.items() if v == leader), None)
    if opposite and scores.get(opposite, 0) >= scores[leader] * 0.55:
        return None, {"reason": "contradictory_event", "top_event": leader}
    top = max((row for row in candidates if row[1] == leader), key=lambda row: row[0])
    if top[0] < 1.35:
        return None, {"reason": "weak_event", "top_event": leader}
    docs = tuple(sorted({doc for _, kind, doc, _ in candidates if kind == leader}))
    return Event(leader, min(1.0, top[0] / 3.0), docs, top[3]), {
        "reason": "event_identified",
        "event": leader,
        "documents": len(corpus.documents),
    }


def _asset_direction(event: Event, asset: str, value_unit: str) -> int:
    """Map economic exposure to the card's quoted convention, abstaining when unclear."""
    kind = event.kind
    if asset.startswith("UST_"):
        return {
            "policy_tightening": 1,
            "policy_easing": -1,
            "inflation_up": 1,
            "inflation_down": -1,
            "growth_down": -1,
            "growth_up": 1,
            "liquidity_stress": -1,
        }.get(kind, 0)
    if asset == "MKT":
        return -1 if kind in _RISK else (1 if kind in {"growth_up", "policy_easing"} else 0)
    if asset == "CPI_ALL":
        return {"inflation_up": 1, "inflation_down": -1, "oil_supply_shock": 1}.get(kind, 0)
    if asset == "UNRATE":
        return 1 if kind == "growth_down" else (-1 if kind == "growth_up" else 0)
    if asset == "NFP":
        return -1 if kind == "growth_down" else (1 if kind == "growth_up" else 0)
    if asset == "MOM" and kind == "positioning_crowding":
        return -1
    if asset in {"EUR", "GBP", "AUD", "CAD", "NOK", "JPY", "CHF", "DKK"}:
        if kind not in _RISK:
            return 0
        # Risk-off is assumed to benefit safe havens JPY/CHF and weaken cyclical currencies.
        base = 1 if asset in {"JPY", "CHF"} else -1
        if asset == "DKK":
            return 0
        unit = value_unit.lower()
        if unit.startswith("usd_per_"):
            return base
        if unit.endswith("_per_usd"):
            return -base
    return 0


def apply_text_first_v5(
    samples: NDArray[np.float64],
    histories: dict[str, pd.Series],
    assets: list[str],
    horizons: list[int],
    target_type: str,
    target_frequency: str,
    family: str,
    asof: str,
    seed: int,
    text_dir: Path,
    value_unit: str,
) -> tuple[NDArray[np.float64], dict[str, Any]]:
    """Replace a bounded, stratified subset with pre-cutoff complete historical paths."""
    meta: dict[str, Any] = {
        "config": "text-first-v5",
        "applied": False,
        "numeric_fallback_exact": True,
        "reason": "family_frozen",
    }
    if family not in {"T2-F1", "T2-F4"}:
        return samples, meta
    if target_type not in {"level", "log_return"} or samples.ndim != 3:
        meta["reason"] = "unsupported_target"
        return samples, meta
    event, diagnostic = _event(text_dir, asof)
    meta.update(diagnostic)
    if event is None:
        return samples, meta
    directions = [_asset_direction(event, asset, value_unit) for asset in assets]
    if not any(directions):
        meta["reason"] = "no_safe_exposure"
        return samples, meta
    steps = _history_steps(histories, assets, target_type, asof)
    if len(steps) < 180:
        meta["reason"] = "insufficient_history"
        return samples, meta
    period = 1 if target_frequency == "daily" else _observation_period_business_days(steps)
    observed = np.maximum(1, np.ceil(np.asarray(horizons) / period).astype(int))
    maximum = int(observed.max())
    values = steps.to_numpy(dtype=float)
    if maximum > len(values) // 3:
        meta["reason"] = "insufficient_horizon_history"
        return samples, meta
    accumulated = np.vstack((np.zeros((1, len(assets))), np.cumsum(values, axis=0)))
    starts = np.arange(len(values) - maximum + 1)
    calendar = pd.DatetimeIndex(steps.index).to_numpy(dtype="datetime64[D]")
    gaps = np.r_[False, np.busday_count(calendar[:-1], calendar[1:]) > max(5, 2 * period)]
    gap_count = np.r_[0, np.cumsum(gaps.astype(int))]
    starts = starts[(gap_count[starts + maximum] - gap_count[starts + 1]) == 0]
    direction = np.asarray(directions, dtype=float)
    sd = np.maximum(steps.std().to_numpy(dtype=float), 1e-8)
    displacement = accumulated[starts + maximum] - accumulated[starts]
    metric = np.sum(displacement * direction / sd, axis=1) / max(1, np.count_nonzero(direction))
    eligible = starts[metric >= np.quantile(metric, 0.83 if family == "T2-F1" else 0.90)]
    separated = 0
    last = -maximum
    for start in eligible:
        if start - last >= maximum:
            separated += 1
            last = int(start)
    if len(eligible) < 10 or separated < 3:
        meta["reason"] = "too_few_independent_worlds"
        return samples, meta
    sleeve = (0.08 if family == "T2-F1" else 0.16) * event.strength
    count = min(len(samples), int(len(samples) * sleeve))
    if count < 10:
        meta["reason"] = "too_few_draws"
        return samples, meta
    rng = np.random.default_rng(seed ^ 0x5A17F14)
    indices = rng.choice(len(samples), count, replace=False)
    chosen = rng.choice(eligible, count, replace=True)
    paths = (
        accumulated[chosen[:, None] + observed[None, :]] - accumulated[chosen, None]
    ).transpose(0, 2, 1)
    if target_type == "level":
        anchor = np.array(
            [
                histories[a].loc[pd.to_datetime(histories[a].index) <= pd.Timestamp(asof)].iloc[-1]
                for a in assets
            ],
            dtype=float,
        )
        paths += anchor[None, :, None]
    if not np.isfinite(paths).all():
        meta["reason"] = "nonfinite_worlds"
        return samples, meta
    output = samples.copy()
    output[indices] = paths
    meta.update(
        applied=True,
        numeric_fallback_exact=False,
        reason="historical_scenario_mixture",
        event=event.kind,
        confidence=event.strength,
        evidence_ids=list(event.doc_ids),
        evidence_excerpt=event.excerpt,
        directions=dict(zip(assets, directions, strict=True)),
        sleeve_draws=count,
        sleeve_fraction=count / len(samples),
        eligible_windows=len(eligible),
        independent_episodes=separated,
        last_world_date=str(steps.index[-1])[:10],
    )
    return output, meta

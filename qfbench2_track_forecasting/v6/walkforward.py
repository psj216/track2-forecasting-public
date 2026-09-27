"""## Executive summary (read this first)

Replay event cutoffs using only mature preceding events and the current unit's panel.
Score official public primitives against later panel observations, then use a purged
older-selection/newer-validation split. Ratios are diagnostics, not leaderboard scores.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from qfbench2_common.scoring.crps import crps_marginal, variogram_score

from ..numeric_v3 import forecast_numeric_v3
from ..tail import tail_pinball
from ..text_first_v5 import apply_text_first_v5
from .catalog import EventRecord
from .fingerprint import Fingerprint
from .heads import Candidate, apply_head, candidates
from .responses import Response, extract, volatility
from .retrieval import retrieve, similarity
from .selector import choose


def components(samples: NDArray[np.float64], outcome: NDArray[np.float64]) -> NDArray[np.float64]:
    s = samples.reshape(len(samples), -1)
    y = outcome.reshape(-1)
    return np.array(
        [
            crps_marginal(s, y),
            variogram_score(s, y) if y.size > 1 else 0.0,
            tail_pinball(s, y, (0.01, 0.05, 0.95, 0.99)),
        ]
    )


def loss_ratio(
    candidate: NDArray[np.float64], baseline: NDArray[np.float64], outcome: NDArray[np.float64]
) -> float:
    b = components(baseline, outcome)
    c = components(candidate, outcome)
    weights = np.array([0.5, 0.3, 0.2])
    weights[b <= 1e-12] = 0
    if not weights.sum():
        return 1.0
    return float(np.sum(weights * c / np.maximum(b, 1e-12)) / weights.sum())


def materialize(
    base: NDArray[np.float64],
    pool: list[Response],
    weights: NDArray[np.float64],
    ess: float,
    frame: pd.DataFrame,
    family: str,
    target: str,
    config: Candidate,
    confidence: float,
    seed: int,
) -> NDArray[np.float64]:
    paths = np.stack([r.path for r in pool])
    if config.vol_scaled:
        recent = volatility(frame, target)
        ratios = np.clip(recent[None, :] / np.stack([r.volatility for r in pool]), 0.5, 2.0)
        paths = paths * ratios[:, :, None]
    quality = float(np.sum(weights * np.array([r.event.fingerprint.confidence for r in pool])))
    trust = float(np.clip(confidence * quality * min(1.0, ess / 8.0), 0, 1))
    return apply_head(
        base,
        paths,
        weights,
        frame.iloc[-1].to_numpy(dtype=float),
        family,
        target,
        config,
        trust,
        seed,
    )


def baseline_at(
    frame: pd.DataFrame,
    records: list[EventRecord],
    asof: str,
    assets: list[str],
    horizons: list[int],
    target: str,
    frequency: str,
    family: str,
    draws: int,
    seed: int,
    value_unit: str,
) -> NDArray[np.float64]:
    history = {a: frame[a] for a in assets}
    base = forecast_numeric_v3(
        history, assets, horizons, target, frequency, draws, seed, family
    ).samples
    if family not in {"T2-F1", "T2-F4"}:
        return base
    # Replay the identical V5.1 interpreter on the historical texts then available.
    available = [r for r in records if r.published_at <= asof][-12:]
    with tempfile.TemporaryDirectory(prefix="v6-replay-") as tmp:
        root = Path(tmp)
        entries = []
        for i, r in enumerate(available):
            name = f"{i}.txt"
            (root / name).write_text(r.text)
            entries.append(
                {
                    "doc_id": f"{r.doc_type}-{r.published_at}-{i}",
                    "timestamp": r.published_at,
                    "source": "Federal Reserve",
                    "doc_type": r.doc_type,
                    "file": name,
                }
            )
        (root / "corpus_index.json").write_text(json.dumps({"documents": entries}))
        return apply_text_first_v5(
            base,
            history,
            assets,
            horizons,
            target,
            frequency,
            family,
            asof,
            seed,
            root,
            value_unit,
            interpreter_version="v5.1",
        )[0]


def calibrate(
    frame: pd.DataFrame,
    records: list[EventRecord],
    query: Fingerprint,
    assets: list[str],
    horizons: list[int],
    target: str,
    frequency: str,
    family: str,
    asof: str,
    seed: int,
    value_unit: str,
    draws: int = 500,
) -> tuple[Candidate | None, dict[str, Any]]:
    responses = [
        r
        for e in records
        if (r := extract(frame, e, horizons, target, frequency, asof)) is not None
    ]
    # Most recent disjoint pseudo-events; sample membership uses text/time, never outcomes.
    eligible = sorted(
        [r for r in responses if similarity(query, r.event.fingerprint, family) >= 0.5],
        key=lambda r: r.start,
        reverse=True,
    )
    cases: list[Response] = []
    seen = set()
    for r in eligible:
        if r.event.episode_id in seen or any(
            not (r.end < c.start or r.start > c.end) for c in cases
        ):
            continue
        cases.append(r)
        seen.add(r.event.episode_id)
        if len(cases) >= 20:
            break
    cases.sort(key=lambda r: r.start)
    grid = candidates(family)
    details = []
    for case in cases:
        cutoff = case.event.published_at
        past_frame = frame.loc[frame.index <= pd.Timestamp(cutoff)]
        pool, weights, ess = retrieve(
            case.event.fingerprint, [r for r in responses if r.end < pd.Timestamp(cutoff)], family
        )
        if ess < 4:
            continue
        baseline = baseline_at(
            past_frame,
            records,
            cutoff,
            assets,
            horizons,
            target,
            frequency,
            family,
            draws,
            seed,
            value_unit,
        )
        outcome = case.path + (
            past_frame.iloc[-1].to_numpy()[:, None] if target == "level" else 0.0
        )
        ratios = {}
        for config in grid:
            adjusted = materialize(
                baseline,
                pool,
                weights,
                ess,
                past_frame,
                family,
                target,
                config,
                case.event.fingerprint.confidence,
                seed,
            )
            ratios[config.name] = loss_ratio(adjusted, baseline, outcome)
        details.append((case, ratios))
    if len(details) < 10:
        return None, {"reason": "insufficient_walkforward_events", "pseudo_events": len(details)}
    split = len(details) // 2
    # The chronological cases were already purged so their response windows cannot overlap.
    training = {c.name: [d[1][c.name] for d in details[:split]] for c in grid}
    validation = {c.name: [d[1][c.name] for d in details[split:]] for c in grid}
    name, meta = choose(training, validation)
    meta.update(
        pseudo_events=len(details),
        selection_end=str(details[split - 1][0].end.date()),
        validation_start=details[split][0].event.published_at,
        validation_end=str(details[-1][0].end.date()),
        normalization="paired official primitive ratios; private scales unavailable",
    )
    return next((c for c in grid if c.name == name), None), meta

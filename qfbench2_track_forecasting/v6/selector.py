"""## Executive summary (read this first)

Choose a candidate on older events and approve it only on later disjoint events.
Report sample size and downside diagnostics; never silently turn a failed gate green.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def statistics(ratios: list[float]) -> dict[str, Any]:
    values = np.asarray(ratios, dtype=float)
    if len(values) == 0 or not np.isfinite(values).all():
        return {"n": 0}
    ordered = np.sort(values)
    trim = max(0, int(len(values) * 0.1))
    trimmed = ordered[trim : len(values) - trim] if trim else ordered
    return {
        "n": len(values),
        "median": float(np.median(values)),
        "trimmed_mean": float(trimmed.mean()),
        "q90": float(np.quantile(values, 0.9)),
        "win_rate": float(np.mean(values < 1)),
        "geometric_ratio": float(np.exp(np.log(np.maximum(values, 1e-12)).mean())),
    }


def choose(
    training: dict[str, list[float]], validation: dict[str, list[float]]
) -> tuple[str | None, dict[str, Any]]:
    eligible = {k: statistics(v) for k, v in training.items() if len(v) >= 5}
    if not eligible:
        return None, {"reason": "insufficient_selection_events"}
    name = min(eligible, key=lambda k: (eligible[k]["trimmed_mean"], eligible[k]["q90"]))
    fit = eligible[name]
    test = statistics(validation.get(name, []))
    passed = (
        test.get("n", 0) >= 5
        and fit["median"] < 1
        and test["median"] < 0.97
        and test["trimmed_mean"] < 0.98
        and test["q90"] <= 1.10
        and test["win_rate"] >= 0.6
    )
    return (name if passed else None), {
        "reason": "past_only_gate_passed" if passed else "past_only_gate_failed",
        "selected": name,
        "selection": fit,
        "validation": test,
    }

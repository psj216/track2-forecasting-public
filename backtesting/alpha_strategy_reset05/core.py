"""Executive summary: deterministic evidence checks and a frozen strategic rubric.

This module reads stored aggregate evidence. It never fits or scores forecasts.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PARENT = "3c2bbfe7ff54ff9f95debf58f5bafa92d5d2ad70"
PARENT_PRE = "ae0bdf3faf2b2ca32205f43cd417e32ab2119d4f"
MAIN = "e1b5cf3b3a87966e902332ef3cc5c0ed2dbffee8"
BRANCH = "track2/alpha-strategy-reset-05"
OFFICIAL = 0.9541
DIMENSIONS = {
    "THEORETICAL_HEADROOM": .20, "EMPIRICAL_SIGNAL": .25,
    "REPLICATION_STABILITY": .15, "NEW_INFORMATION_NOVELTY": .10,
    "VALIDATION_FEASIBILITY": .10, "TIME_TO_RESULT": .10,
    "IMPLEMENTATION_RISK": .05, "SUBMISSION_RELEVANCE": .05,
}
CANDIDATES = {
    "LOCATION_INFORMATION_CONTINUE": "LOCATION-NEW-INFORMATION-06",
    "MARGINAL_SCALE_REOPEN": "MARGINAL-SCALE-RESET-06",
    "TAIL_REOPEN": "TAIL-STRUCTURE-RESET-06",
    "JOINT_DEPENDENCE_REOPEN": "JOINT-DEPENDENCE-RESET-06",
    "TEXT_ROUTING_VALIDATION": "TEXT-ROUTING-VALIDATION-06",
    "SCORE_GEOMETRY_REASSESSMENT": "SCORE-GEOMETRY-AUDIT-06",
    "CARD_CONDITIONAL_ERROR_STRUCTURE": "CARD-CONDITIONAL-ERROR-06",
    "NEW_HIGH_FREQUENCY_INFORMATION": "HIGH-FREQUENCY-MARKET-INFO-06",
    "SUBMISSION_HARDENING": "SUBMISSION-HARDENING-06",
}
UNIVERSES = {"OFFICIAL", "CARD_PROXY", "CANONICAL_MARGINAL_PROXY",
             "SOURCE_SPECIFIC_PROXY", "DIAGNOSTIC_ONLY"}
QUALITIES = {"A", "B", "C", "D"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text())


def weighted(scores: dict) -> float:
    if set(scores) != set(DIMENSIONS):
        raise ValueError("All eight frozen dimensions are required")
    if any(not isinstance(v, int) or not 0 <= v <= 5 for v in scores.values()):
        raise ValueError("Scores must be integers from zero to five")
    return round(20 * sum(DIMENSIONS[k] * scores[k] for k in DIMENSIONS), 6)


def decide(rows: list[dict]) -> dict:
    """Apply the PRE stopping rule, with no post-ranking changes."""
    research = [r for r in rows if r["axis"] != "SUBMISSION_HARDENING"]
    feasible = [r for r in research if r["genuinely_novel"] and
                r["validation"] not in {"NOT_AVAILABLE", "EXPOSED_ONLY"} and
                r["operationally_feasible"] and not r["eliminated"]]
    best = max(feasible, key=lambda r: (r["priority"], -list(CANDIDATES).index(r["axis"])),
               default=None)
    if best and best["priority"] >= 70:
        stopping, axis = "RESEARCH_CONTINUE", best["axis"]
    elif best and 55 <= best["priority"] < 70 and best["low_submission_downside"]:
        stopping, axis = "ONE_LAST_SHOT", best["axis"]
    else:
        stopping, axis = "HARDEN_NOW", "SUBMISSION_HARDENING"
    return {"stopping_rule": stopping, "selected_axis": axis,
            "NEXT": CANDIDATES[axis], "best_research_score": max(r["priority"] for r in research),
            "eligible_research_count": len(feasible), "next_study_executed": False}


def verify_protection(root: Path, manifest: dict) -> None:
    for name, digest in manifest.items():
        if sha(root / name) != digest:
            raise ValueError(f"Protected parent file changed: {name}")

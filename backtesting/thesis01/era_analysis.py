"""## Executive summary (read this first)

Report era-specific sparse-grid behavior. Pre-2013 episodes provide development
diagnostics only; their scores are never called independent OOS evidence.
"""

from .diagnostics import aggregate


def episode(year: int) -> str:
    if year < 2007:
        return "pre-GFC"
    if year <= 2010:
        return "GFC/aftermath"
    if year <= 2019:
        return "post-GFC low-rate"
    if year <= 2021:
        return "COVID"
    return "inflation/hiking"


def summarize(rows: list[dict], beta: dict) -> dict:
    from collections import defaultdict

    groups = defaultdict(list)
    for r in rows:
        groups[r["episode"]].append(r)
    return {era: {**aggregate(part), "beta_signs": beta} for era, part in sorted(groups.items())}

"""## Executive summary (read this first)

Extract dated economic statements and same-issuer document changes. No asset direction,
card title, event date memorization, outcome, or neural model enters these features.
"""

# Long deterministic semantic patterns remain intact for review.
# ruff: noqa: E501
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..text_evidence import TextDocument, read_frozen_corpus
from ..text_interpreter_v51 import _sentences, classify_currentness

PATTERNS = {
    "policy": (
        r"(?:rais(?:e|ed|ing)|increas(?:e|ed|ing)).{0,100}(?:federal funds|policy|interest|target range)",
        r"(?:lower(?:ed|ing)?|reduc(?:e|ed|ing)|cut(?:ting)?).{0,100}(?:federal funds|policy|interest|target range)",
    ),
    "guidance": (
        r"(?:further (?:policy )?(?:firming|tightening)|additional (?:policy )?firming|withdraw.*accommodation|higher for longer|begin.*normalization|taper)",
        r"(?:patient|considerable period|extended period|additional accommodation|asset purchases|act as appropriate|further easing)",
    ),
    "inflation": (
        r"inflation.{0,65}(?:elevated|high|risen|ris(?:ing|ks)|increas|above|accelerat)|price pressures.{0,35}(?:increas|ris|persist)",
        r"inflation.{0,65}(?:declin|eas|cool|low|below|subsid)|disinflation",
    ),
    "growth": (
        r"(?:growth|economic activity|employment|labor market).{0,55}(?:strong|strengthen|expand|improv|rebound)",
        r"(?:growth|economic activity|employment|labor market).{0,55}(?:slow|weak|contract|declin|deteriorat)|recession",
    ),
    "liquidity": (
        r"(?:funding|liquidity|credit|financial market).{0,45}(?:stress|strain|disrupt|tighten)|bank failures?|credit crunch",
        r"(?:funding|liquidity).{0,35}(?:eased|improved|receded)",
    ),
    "risk": (
        r"trade tensions?|tariffs?|geopolitical|fragmentation|financial instability",
        r"(?:trade tensions?|geopolitical risk).{0,35}(?:receded|eased)",
    ),
    "oil": (
        r"oil.{0,35}(?:supply|price).{0,30}(?:cut|surge|disrupt)|energy prices.{0,25}(?:increas|ris)",
        r"oil prices.{0,25}(?:fall|declin|collaps)",
    ),
    "positioning": (
        r"carry.{0,20}unwind|forced (?:selling|liquidation)|margin calls?|crowded (?:trade|position)",
        r"(?!)",
    ),
}
ISSUERS = {
    "FED": ("federal reserve", "fomc"),
    "ECB": ("ecb", "european central bank"),
    "BOJ": ("bank of japan",),
    "BOE": ("bank of england",),
    "BOC": ("bank of canada",),
    "RBA": ("reserve bank of australia",),
    "SNB": ("swiss national bank",),
}
REGIONS = {
    "FED": "US",
    "ECB": "EU",
    "BOJ": "JP",
    "BOE": "GB",
    "BOC": "CA",
    "RBA": "AU",
    "SNB": "CH",
}


@dataclass(frozen=True)
class Fingerprint:
    major: str
    issuer: str
    region: str
    currentness: str
    confidence: float
    axes: dict[str, float]
    delta: dict[str, float] = field(default_factory=dict)
    tokens: tuple[str, ...] = ()
    evidence: str = ""
    doc_ids: tuple[str, ...] = ()

    def payload(self) -> dict[str, Any]:
        return asdict(self)


def interpret(text: str, published_at: str, source: str, doc_id: str = "") -> Fingerprint | None:
    issuer = next((k for k, v in ISSUERS.items() if any(x in source.lower() for x in v)), "UNKNOWN")
    hits: dict[str, list[float]] = {k: [] for k in PATTERNS}
    evidence: list[tuple[float, str, str]] = []
    for sentence in _sentences(text):
        if len(sentence) > 1000 or len(sentence) < 20 or sentence.endswith("?"):
            continue
        for axis, patterns in PATTERNS.items():
            for sign, pattern in zip((1, -1), patterns, strict=True):
                m = re.search(pattern, sentence, re.I)
                if not m:
                    continue
                prefix = sentence[max(0, m.start() - 30) : m.start()]
                if re.search(r"\b(?:not|no|without|unlikely)\s+(?:\w+\s+){0,2}$", prefix, re.I):
                    continue
                state = classify_currentness(sentence, m.group(), published_at)
                if state == "UNRESOLVED" and re.search(
                    r"\b(?:decided|expects?|anticipates?|judged|agreed)\b", sentence, re.I
                ):
                    state = (
                        "FORWARD"
                        if re.search(r"expects?|anticipates?", sentence, re.I)
                        else "CURRENT"
                    )
                if state not in {"CURRENT", "FORWARD"}:
                    continue
                weight = 1.0 if state == "CURRENT" else 0.6
                hits[axis].append(sign * weight)
                evidence.append((weight, sentence[:300], state))
    axes = {k: max(-1.0, min(1.0, sum(v) / max(1, len(v)))) for k, v in hits.items() if v}
    axes = {k: v for k, v in axes.items() if abs(v) >= 0.2}
    if not axes:
        return None
    major = max(
        axes,
        key=lambda k: abs(axes[k]) * (1.2 if k in {"liquidity", "policy", "positioning"} else 1.0),
    )
    best = max(evidence)
    tokens = tuple(
        sorted(set(re.findall(r"[a-z]{4,}", " ".join(s for _, s, _ in evidence).lower())))
    )[:100]
    return Fingerprint(
        major,
        issuer,
        REGIONS.get(issuer, "GLOBAL"),
        best[2],
        min(0.95, 0.45 + 0.1 * len(axes)),
        axes,
        tokens=tokens,
        evidence=best[1],
        doc_ids=(doc_id,) if doc_id else (),
    )


def with_delta(current: Fingerprint, prior: Fingerprint | None) -> Fingerprint:
    if prior is None or prior.issuer != current.issuer:
        return current
    delta = {k: current.axes.get(k, 0.0) - prior.axes.get(k, 0.0) for k in PATTERNS}
    return Fingerprint(
        **{**current.payload(), "delta": {k: v for k, v in delta.items() if abs(v) >= 0.2}}
    )


def current_fingerprint(text_dir: Path, asof: str, family: str) -> Fingerprint | None:
    import pandas as pd

    docs = sorted(
        read_frozen_corpus(text_dir, asof).documents, key=lambda d: (d.timestamp, d.doc_id)
    )
    records: list[tuple[TextDocument, Fingerprint]] = []
    for doc in docs:
        fp = interpret(doc.text, doc.timestamp, doc.source, doc.doc_id)
        if fp:
            previous = next(
                (
                    p
                    for d, p in reversed(records)
                    if d.timestamp < doc.timestamp
                    and d.doc_type == doc.doc_type
                    and p.issuer == fp.issuer
                ),
                None,
            )
            fp = with_delta(fp, previous)
            records.append((doc, fp))
    eligible = [
        (d, f)
        for d, f in records
        if (pd.Timestamp(asof) - pd.Timestamp(d.timestamp)).days <= 60
        and (family != "T2-F1" or f.delta)
    ]
    return eligible[-1][1] if eligible else None

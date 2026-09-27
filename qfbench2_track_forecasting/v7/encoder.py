"""## Executive summary (read this first)

Map frozen, dated card documents to event features without predicting asset values.
An unknown release surprise stays unknown: published data alone supplies no consensus.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..text_evidence import read_frozen_corpus
from ..v6.fingerprint import Fingerprint, interpret


@dataclass(frozen=True)
class Query:
    fingerprint: Fingerprint
    event_type: str
    published_at: str
    doc_id: str
    surprise: str = "unknown"


def event_type_for(doc_type: str, source: str, text: str) -> str:
    hint = (doc_type + " " + source).lower()
    head = text[:1300].lower()
    is_bls_release = "bls" in hint or "bureau of labor statistics" in hint
    if is_bls_release and ("consumer price index" in head or "cpi" in doc_type.lower()):
        return "CPI_RELEASE"
    if is_bls_release and (
        "employment situation" in head or "empsit" in hint or "nonfarm payroll" in head
    ):
        return "EMPLOYMENT_RELEASE"
    if "fomc_statement" in hint or "monetary policy decisions" in head:
        return "POLICY_DECISION"
    if "fomc_minutes" in hint:
        return "POLICY_MINUTES"
    return "MACRO_CONTEXT"


def fingerprint_for(
    text: str, published_at: str, source: str, doc_id: str, event_type: str
) -> Fingerprint | None:
    # Syndicated central-bank speeches retain speaker/institution attribution in
    # their masthead even if the archive's publisher is BIS.
    masthead = text[:700]
    if "BIS" in source and re.search(
        r"Jerome H\.? Powell.{0,200}(?:Chair|Federal Reserve)", masthead, re.I | re.S
    ):
        source = "Federal Reserve"
    fp = interpret(text[:7000], published_at, source, doc_id)
    if event_type in {"CPI_RELEASE", "EMPLOYMENT_RELEASE"}:
        major = "inflation" if event_type == "CPI_RELEASE" else "growth"
        # A first-paragraph published change is observable, unlike a consensus surprise.
        opening = re.sub(r"\s+", " ", text[:2000])
        key = (
            r"(?:consumer price index|all items index|"
            r"nonfarm payroll employment|total nonfarm payroll employment)"
        )
        match = re.search(
            key + r".{0,120}?\b(increased|rose|gained|decreased|declined|fell)\b", opening, re.I
        )
        sign = 1 if match and match[1].lower() in {"increased", "rose", "gained"} else -1
        if match:
            return Fingerprint(
                major,
                "BLS",
                "US",
                "CURRENT",
                0.55,
                {major: float(sign)},
                tokens=("official_release",),
                evidence=opening[max(0, match.start() - 30) : match.end() + 80],
                doc_ids=(doc_id,),
            )
        return None
    if fp is None:
        return None
    return fp


def current_queries(text_dir: Path, asof: str, max_age_days: int = 21) -> list[Query]:
    docs = read_frozen_corpus(text_dir, asof).documents
    if not docs:
        return []
    latest_document = max(date.fromisoformat(doc.timestamp[:10]) for doc in docs)
    result = []
    for doc in docs:
        age = (date.fromisoformat(asof[:10]) - date.fromisoformat(doc.timestamp[:10])).days
        lag = (latest_document - date.fromisoformat(doc.timestamp[:10])).days
        if not 0 <= age <= max_age_days or lag > 7:
            continue
        kind = event_type_for(doc.doc_type, doc.source, doc.text)
        fp = fingerprint_for(doc.text, doc.timestamp[:10], doc.source, doc.doc_id, kind)
        if fp and fp.currentness in {"CURRENT", "FORWARD"}:
            result.append(Query(fp, kind, doc.timestamp[:10], doc.doc_id))
    return sorted(result, key=lambda q: (q.published_at, q.fingerprint.confidence), reverse=True)

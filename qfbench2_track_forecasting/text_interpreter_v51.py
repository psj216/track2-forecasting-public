"""## Executive summary (read this first)

F1 compares dated documents of the same kind for changes in forward policy
language. F4 classifies the sentence's temporal status before allowing any
shock event. Both interpreters abstain on conflicting or unsupported evidence.
"""

# Keep long semantic patterns on single lines for manual clause auditing.
# ruff: noqa: E501

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .text_evidence import TextDocument, read_frozen_corpus
from .text_first_v5 import Event


@dataclass(frozen=True)
class Evidence:
    event: Event
    currentness: str
    prior_excerpt: str
    interpretation: str


def _sentences(text: str) -> list[str]:
    # Published statements often hard-wrap a single sentence at column 70.
    body = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    return [" ".join(s.split()) for s in re.split(r"(?<=[.!?])\s+|\n+", body) if s.strip()]


def _doc_group(doc: TextDocument) -> str:
    if doc.doc_type == "fomc_statement":
        return "fomc_statement"
    if doc.doc_type == "macro_release":
        return re.sub(r"-?\d.*", "", doc.doc_id.lower()) or "macro_release"
    if doc.doc_type == "cb_speech":
        chunks = doc.doc_id.lower().split("_")
        return "_".join(chunks[:2]) if len(chunks) >= 2 else ""
    return ""


_POLICY_PHRASES: tuple[tuple[str, str, float], ...] = (
    (
        "extended_accommodation",
        r"\b(?:for a considerable period|for a considerable time|can be patient in beginning|keep(?:ing)? (?:the )?rate(?:s)? (?:low|below))\b",
        -1.0,
    ),
    (
        "near_term_tightening",
        r"\b(?:raise.{0,75}at its next meeting|begin to raise|extent and timing of additional adjustments)\b",
        1.0,
    ),
    (
        "balance_sheet_tightening",
        r"\b(?:begin implementing a balance sheet normalization|decided to conclude its asset purchase program|decreas(?:e|ing) reinvestment)\b",
        1.0,
    ),
    (
        "new_balance_of_risks",
        r"\brisks to achieving its employment and inflation goals (?:are moving|have moved) (?:into|toward) better balance\b",
        -0.45,
    ),
    (
        "policy_easing_guidance",
        r"\b(?:act as appropriate to sustain|provide additional accommodation|further easing|lower (?:the )?target range)\b",
        -0.8,
    ),
    (
        "inflation_pressure",
        r"\b(?:inflation pressures? (?:have increased|are rising)|inflation remains (?:too )?(?:high|elevated)|upside risks? to inflation)\b",
        0.5,
    ),
    (
        "disinflation",
        r"\b(?:disinflationary progress|inflation (?:has |is )?(?:declin|eas|cool)|inflation pressures? (?:have eased|are easing))\b",
        -0.5,
    ),
)


def _action(text: str) -> int:
    for s in _sentences(text):
        if "committee decided" not in s.lower() or "rate" not in s.lower():
            continue
        if re.search(r"\b(?:raise|increase|hike)\b.{0,90}\brate|\braise.{0,90}target", s, re.I):
            return 1
        if re.search(r"\b(?:lower|reduce|cut)\b.{0,90}\brate|\blower.{0,90}target", s, re.I):
            return -1
        if re.search(r"\b(?:keep|maintain|hold)\b.{0,90}\b(?:rate|target)", s, re.I):
            return 0
    return 0


def _phrase_hits(doc: TextDocument) -> dict[str, tuple[float, str]]:
    body = doc.text
    # FOMC minutes contain quotations, votes, and appendix discussion. Only
    # the issued statement itself is comparable across adjacent releases.
    if doc.doc_type == "fomc_statement":
        body = re.split(
            r"\bVoting (?:for|against) the (?:monetary policy )?action\b", body, flags=re.I
        )[0]
    found: dict[str, tuple[float, str]] = {}
    for sentence in _sentences(body):
        if len(sentence) > 650:
            continue
        for name, pattern, sign in _POLICY_PHRASES:
            if name not in found and re.search(pattern, sentence, re.I):
                found[name] = (sign, sentence[:250])
    return found


def f1_document_delta(
    text_dir: Path, asof: str, assets: list[str]
) -> tuple[Evidence | None, dict[str, Any]]:
    """Compare adjacent same-issuer releases, never a generic event bag."""
    try:
        corpus = read_frozen_corpus(text_dir, asof)
    except (OSError, ValueError, TypeError):
        return None, {"reason": "corpus_unavailable"}
    docs = sorted(corpus.documents, key=lambda d: (d.timestamp, d.doc_id), reverse=True)
    target = assets[0] if len(assets) == 1 or all(a.startswith("UST_") for a in assets) else ""
    if not (
        target.startswith("UST_")
        or target in {"MKT", "CPI_ALL", "UNRATE", "AUD", "CAD", "EUR", "JPY", "CHF", "DKK"}
    ):
        return None, {"reason": "no_comparable_exposure"}
    pairs: list[tuple[TextDocument, TextDocument]] = []
    for latest in docs:
        group = _doc_group(latest)
        if not group or latest.doc_type not in {"fomc_statement", "cb_speech", "macro_release"}:
            continue
        if (
            latest.doc_type == "fomc_statement"
            and not target.startswith("UST_")
            and target != "MKT"
        ):
            continue
        if latest.doc_type == "cb_speech" and target.startswith("UST_"):
            continue
        if latest.doc_type == "macro_release" and target != "CPI_ALL":
            continue
        # A foreign central bank speech should not route another currency.
        issuer = {
            "AUD": ("lowe", "reserve bank of australia"),
            "CAD": ("poloz", "wilkins", "bank of canada"),
            "EUR": ("draghi", "lagarde", "ecb"),
            "JPY": ("kuroda", "ueda", "bank of japan"),
            "CHF": ("jordan", "swiss national bank"),
            "DKK": ("danmarks nationalbank",),
        }.get(target)
        if (
            latest.doc_type == "cb_speech"
            and issuer
            and not any(x in (latest.doc_id + latest.text[:400]).lower() for x in issuer)
        ):
            continue
        previous = next(
            (
                d
                for d in docs
                if d.timestamp < latest.timestamp
                and _doc_group(d) == group
                and (pd.Timestamp(latest.timestamp) - pd.Timestamp(d.timestamp)).days <= 100
            ),
            None,
        )
        if previous:
            pairs.append((latest, previous))
    if not pairs:
        return None, {"reason": "no_same_series_pair", "documents": len(docs)}
    latest, previous = max(
        pairs, key=lambda pair: (pair[0].timestamp, pair[0].doc_type == "fomc_statement")
    )
    fresh, old = _phrase_hits(latest), _phrase_hits(previous)
    changes: list[tuple[float, str, str, str]] = []
    for name, (sign, excerpt) in fresh.items():
        if name not in old:
            changes.append((sign, name, excerpt, ""))
    for name, (sign, excerpt) in old.items():
        if name not in fresh:
            changes.append((-sign, name + "_removed", "", excerpt))
    if latest.doc_type == "fomc_statement":
        shift = _action(latest.text) - _action(previous.text)
        if shift:
            sentence = next(
                (
                    s
                    for s in _sentences(latest.text)
                    if "committee decided" in s.lower() and "rate" in s.lower()
                ),
                "",
            )
            prior = next(
                (
                    s
                    for s in _sentences(previous.text)
                    if "committee decided" in s.lower() and "rate" in s.lower()
                ),
                "",
            )
            changes.append((0.45 * shift, "policy_action_changed", sentence[:250], prior[:250]))
    if not changes:
        return None, {
            "reason": "no_meaningful_delta",
            "document_pair": [previous.doc_id, latest.doc_id],
        }
    net = sum(c[0] for c in changes)
    if abs(net) < 0.40:
        return None, {"reason": "mixed_delta", "document_pair": [previous.doc_id, latest.doc_id]}
    sign = 1 if net > 0 else -1
    candidates = [c for c in changes if c[0] * sign > 0]
    best = max(candidates, key=lambda c: abs(c[0]))
    current_excerpt = best[2]
    if not current_excerpt:
        current_excerpt = next(
            (
                s[:250]
                for s in _sentences(latest.text)
                if re.search(
                    r"\b(?:raise|lower|increase|maintain)\b.{0,70}\btarget range\b", s, re.I
                )
                and re.search(r"\b(?:committee|bank)\b", s, re.I)
            ),
            "",
        )
    direction = "policy_tightening" if sign > 0 else "policy_easing"
    if target == "CPI_ALL":
        direction = "inflation_up" if sign > 0 else "inflation_down"
    evidence = Evidence(
        event=Event(
            direction,
            min(0.90, 0.45 + 0.15 * abs(net)),
            (previous.doc_id, latest.doc_id),
            current_excerpt,
        ),
        currentness="DOCUMENT_DELTA",
        prior_excerpt=best[3],
        interpretation=best[1],
    )
    return evidence, {
        "reason": "document_delta",
        "document_pair": [previous.doc_id, latest.doc_id],
        "change_names": [c[1] for c in changes],
        "tone_shift": round(net, 3),
    }


_SHOCKS: tuple[tuple[str, str], ...] = (
    (
        "liquidity_stress",
        r"\b(?:funding (?:markets? )?(?:stress|strain|pressures?)|liquidity (?:shortage|strain|pressures?)|bank (?:failures?|runs?|distress)|systemic (?:stress|risk)|credit crunch|market dislocation|financial conditions (?:tighten|deteriorat))\w*\b",
    ),
    (
        "growth_down",
        r"\b(?:economic activity (?:has |is )?(?:contract|declin|disrupt)|growth (?:has |is )?(?:weak|slow|decelerat)|unemployment (?:has |is )?(?:ris|increas)|(?:coronavirus|covid.19)(?: outbreak)?.{0,100}(?:harm|disrupt|global growth|uncertainty|impact on equity markets|impact on .*commodity prices))\w*\b",
    ),
    (
        "policy_tightening",
        r"\b(?:raising (?:interest |policy )?rates?|rate hikes?|taper(?:ing)? (?:asset )?purchases|reduce (?:asset )?purchases|tightening (?:monetary )?policy)\b",
    ),
    (
        "policy_easing",
        r"\b(?:cutting (?:interest |policy )?rates?|lowering (?:interest |policy )?rates?|expanding (?:asset )?purchases|quantitative easing)\b",
    ),
    (
        "inflation_up",
        r"\b(?:inflation (?:remains? (?:too )?(?:high|elevated)|is (?:rising|accelerating))|price pressures? (?:are |have )?(?:rising|increased))\b",
    ),
    (
        "inflation_down",
        r"\b(?:inflation (?:is |has )?(?:falling|easing|decelerating)|disinflationary progress|price pressures? (?:are |have )?(?:easing|subsided))\b",
    ),
    (
        "trade_geopolitical",
        r"\b(?:trade (?:war|tensions?|escalation)|brexit (?:risk|uncertainty)|debt.ceiling (?:impasse|standoff)|sovereign debt (?:crisis|stress))\b",
    ),
    (
        "positioning_crowding",
        r"\b(?:crowded (?:trade|position)|carry (?:trade )?unwind|forced (?:liquidation|selling)|margin calls?)\b",
    ),
)


def classify_currentness(sentence: str, matched_phrase: str, asof: str) -> str:
    """Read temporal scope of the matched clause before reading its event."""
    s = " ".join(sentence.split()).lower()
    match = s.find(matched_phrase.lower())
    if match < 0:
        return "UNRESOLVED"
    prior = s[max(0, match - 170) : match]
    following = s[match : match + 180]
    prior = re.split(r"[;:]|\b(?:but|however|whereas)\b", prior)[-1]
    following = re.split(r"[;:]|\b(?:but|however|whereas)\b", following)[0]
    clause = prior + following
    # A year well before the as-of dates a retrospective example. The latest
    # document timestamp alone cannot turn that example into current evidence.
    years = [int(y) for y in re.findall(r"\b(?:19|20)\d{2}\b", clause)]
    if any(y < int(asof[:4]) - 1 for y in years):
        return "RETROSPECTIVE"
    if re.search(
        r"\b(?:in the past|over the past year|historically|previous crisis|last recession|back then|at that time|years ago|during the|since the (?:global )?financial crisis|when the crisis hit|re.emergence of the|morphed into)\b",
        clause,
    ):
        return "RETROSPECTIVE"
    if re.search(
        r"\b(?:if .{0,80}\b(?:were|would|could)|hypothetical|scenario where|for example|what if|do you think|would have|could have)\b",
        clause,
    ):
        return "HYPOTHETICAL"
    if re.search(
        r"\b(?:has eased|have eased|is easing|have receded|has receded|appears to have receded|has improved|are improving|has subsided|is no longer|less likely|not concerned|without (?:any |further )?stress)\b",
        clause,
    ):
        return "RESOLVED"
    if re.search(
        r"\b(?:potential effect|potential impact|may intensify|could intensify|risk of|threat of)\b",
        clause,
    ):
        return "FORWARD"
    if re.search(r"\b(?:may|might|could|likely to|risk of|warns? (?:that|of)|threat of)\b", clause):
        return "FORWARD"
    if re.search(
        r"\b(?:is|are|has|have|remains?|continue[sd]?|recent|currently|now|deteriorated|weakened|disrupted|increased|elevated)\b",
        clause,
    ):
        return "CURRENT"
    return "UNRESOLVED"


def f4_current_event(
    text_dir: Path, asof: str, assets: list[str] | None = None
) -> tuple[Evidence | None, dict[str, Any]]:
    """Only a current or forward event in a recent public document can route worlds."""
    try:
        corpus = read_frozen_corpus(text_dir, asof)
    except (OSError, ValueError, TypeError):
        return None, {"reason": "corpus_unavailable"}
    hits: list[tuple[float, str, str, str, str]] = []
    rejected: dict[str, int] = {}
    for doc in corpus.documents:
        age = (pd.Timestamp(asof) - pd.Timestamp(doc.timestamp)).days
        if age > 50:
            continue
        for sentence in _sentences(doc.text):
            if not 24 <= len(sentence) <= 550:
                continue
            # Citations and questions refer to topics rather than assertions.
            if sentence.lstrip().startswith(("- ", "## ")) or sentence.endswith("?"):
                continue
            if not re.match(r"^[A-Z0-9('“]", sentence.strip()):
                continue
            for kind, pattern in _SHOCKS:
                match = re.search(pattern, sentence, re.I)
                if not match:
                    continue
                state = classify_currentness(sentence, match.group(0), asof)
                if kind == "inflation_up" and re.search(
                    r"\b(?:points to a decelerat\w*|although .* inflation .* (?:cool|fall)|while .* inflation .* (?:decelerat|flatten)|(?:GDP|economy) (?:has )?recover\w*)",
                    sentence,
                    re.I,
                ):
                    state = "RESOLVED"
                if kind == "growth_down" and re.search(
                    r"\b(?:recovered? to its pre.pandemic|still allowed .* recover|followed by a rebound)\b",
                    sentence,
                    re.I,
                ):
                    state = "RESOLVED"
                if state not in {"CURRENT", "FORWARD"}:
                    rejected[state] = rejected.get(state, 0) + 1
                    continue
                # A generic historical reference in a long speech is not
                # rescued by an unrelated present-tense verb elsewhere.
                if re.search(
                    r"\b(?:recession of|banking crisis|global financial crisis|stress testing|historical experience|lessons from|financial stability framework)\b",
                    sentence,
                    re.I,
                ):
                    rejected["RETROSPECTIVE"] = rejected.get("RETROSPECTIVE", 0) + 1
                    continue
                if assets and all(a.startswith("UST_") for a in assets):
                    foreign = re.search(
                        r"\b(?:euro area|ECB|advanced foreign|Japan|United Kingdom|UK economy|Bank of England|Canada|Swiss|European economies)\b",
                        sentence,
                        re.I,
                    )
                    domestic = re.search(
                        r"\b(?:United States|U\.S\.|US economy|global|worldwide|systemic)\b",
                        sentence,
                        re.I,
                    )
                    if foreign and not domestic:
                        rejected["UNRELATED_MARKET"] = rejected.get("UNRELATED_MARKET", 0) + 1
                        continue
                if (
                    assets
                    and assets[0] in {"JPY", "CHF", "AUD", "CAD", "EUR", "GBP", "NOK"}
                    and kind == "growth_down"
                ):
                    local = {
                        "JPY": r"\b(?:Japan|Japanese|yen|global|worldwide)\b",
                        "CHF": r"\b(?:Swiss|Switzerland|franc|global|worldwide)\b",
                        "AUD": r"\b(?:Australia|Australian|global|worldwide)\b",
                        "CAD": r"\b(?:Canada|Canadian|global|worldwide)\b",
                        "EUR": r"\b(?:euro area|European|ECB|global|worldwide)\b",
                        "GBP": r"\b(?:Britain|British|United Kingdom|UK|global|worldwide)\b",
                        "NOK": r"\b(?:Norway|Norwegian|oil|global|worldwide)\b",
                    }[assets[0]]
                    if not re.search(local, sentence, re.I):
                        rejected["UNRELATED_MARKET"] = rejected.get("UNRELATED_MARKET", 0) + 1
                        continue
                weight = (1.0 if state == "CURRENT" else 0.45) * (1 - age / 100)
                weight *= {
                    "liquidity_stress": 1.12,
                    "growth_down": 1.08,
                    "inflation_up": 0.85,
                    "policy_tightening": 0.85,
                }.get(kind, 1.0)
                if doc.doc_type in {"fomc_statement", "macro_release", "corporate_8k"}:
                    weight *= 1.10
                hits.append((weight, kind, state, doc.doc_id, sentence[:250]))
    if not hits:
        return None, {"reason": "no_current_event", "rejected_states": rejected}
    # Select the strongest *recent assertion*, not the most frequently cited
    # theme across a large corpus of speeches.
    hits.sort(reverse=True)
    best = hits[0]
    if best[0] < 0.38:
        return None, {"reason": "weak_current_event", "rejected_states": rejected}
    if any(
        h[1] != best[1]
        and h[0] >= best[0] * 0.95
        and (
            (h[1], best[1])
            in {
                ("policy_easing", "policy_tightening"),
                ("inflation_up", "inflation_down"),
                ("inflation_down", "inflation_up"),
            }
        )
        for h in hits[1:]
    ):
        return None, {"reason": "contradictory_current_events", "rejected_states": rejected}
    confidence = min(0.90, best[0] * (0.85 if best[2] == "CURRENT" else 0.55))
    evidence = Evidence(
        Event(best[1], confidence, (best[3],), best[4]), best[2], "", "current_event"
    )
    return evidence, {
        "reason": "current_event",
        "rejected_states": rejected,
        "candidate_count": len(hits),
    }

"""## Executive summary (read this first)

Keep traded-market values separate and enforce a t-minus-one close.
"""
from .event_alignment import known_cutoff
from .source_schema import CLASS_B,separate_classes

def market_implied_at(records,origin):
    separate_classes(records,CLASS_B)
    return [r for r in records if r["publication_date"]<=str(known_cutoff(origin).date())]

"""## Executive summary (read this first)
Aggregate all thirteen single-cell cards without selecting favorable outcomes.
"""
from .diagnostics import summarize
def evaluate(records,model):return summarize([c for c in records if c['single']],model)

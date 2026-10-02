"""## Executive summary (read this first)
Keep all four fixed family aggregates with equal-card geometric summaries.
"""
from .diagnostics import summarize
def evaluate(records,model):return {f:summarize([c for c in records if c['family']==f],model)for f in ['T2-F1','T2-F2','T2-F3','T2-F4']}

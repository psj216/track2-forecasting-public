"""## Executive summary (read this first)
Aggregate all eleven multi-cell cards and explicitly classify F1 location/path damage.
"""
from .diagnostics import summarize
def evaluate(records,model):return summarize([c for c in records if not c['single']],model)
def f1_safety(records,model):
 m=summarize([c for c in records if c['family']=='T2-F1'],model)
 # Material joint damage is predeclared as at least one percent.
 if m['marginal_ratio']<1 and m['joint_ratio']>1.01 and m['geometric_composite_ratio']>=1:return 'CONTEXT_LOCATION_SIGNAL_BUT_PATH_REQUIRED'
 return 'POSITIVE'if m['geometric_composite_ratio']<1 else'NO_IMPROVEMENT'

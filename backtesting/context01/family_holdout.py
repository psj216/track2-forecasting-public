"""## Executive summary (read this first)
Run the fixed four-family diagnostic through the same whole-card crossfit implementation.
"""
from .card_block_crossfit import run
def run_family(root,private,card_private,pre,index):return run(root,private,card_private,pre,'family',index)

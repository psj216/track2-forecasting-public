"""## Executive summary (read this first)

Generate matched numeric/text draws with the same seed and existing V5.1 paths.
"""

from .build_baseline_ledger import card_draws


def run(unit, card):
    return {"numeric": card_draws(unit, card, text=False), "text": card_draws(unit, card)}

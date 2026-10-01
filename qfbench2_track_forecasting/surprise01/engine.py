"""## Executive summary (read this first)

Apply three independent precommitted heads to the same frozen V5.1 draws.
Inference reads only passed pre-origin events and frozen response coefficients.
"""

from .location_head import shift, apply as location
from .scale_head import multiplier, apply as scale


def update(draws, surprise, beta, gamma, sigma, horizon):
    delta = shift(beta, surprise, sigma, horizon)
    factor = multiplier(gamma, surprise)
    return {"location": location(draws, delta),
            "scale": scale(draws, factor),
            "combined": location(scale(draws, factor), delta)}, delta, factor

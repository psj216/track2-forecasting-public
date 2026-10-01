"""## Executive summary (read this first)

Levels use daily differences. Daily return values already are increments.
The scale at a date uses at most 252 earlier observations and at least 200.
"""

from qfbench2_track_forecasting.thesis01.innovations import innovations
from qfbench2_track_forecasting.thesis01.scaling import scaled

__all__ = ["innovations", "scaled"]

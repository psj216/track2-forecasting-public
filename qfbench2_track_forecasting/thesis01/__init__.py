"""## Executive summary (read this first)

THESIS-01 measures historical cross-market tension and shifts V5.1 locations only.
It does not import the V12 or V13 forecasting engines.
"""

from .engine import Thesis01Engine

__all__ = ["Thesis01Engine"]

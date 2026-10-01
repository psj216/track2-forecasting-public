"""## Executive summary (read this first)

Event-level bootstrap repeats exactly under the fixed seed.
"""

from backtesting.surprise01.event_block_bootstrap import interval


def test_same_seed():
    rows = [{"release_date": str(i), "v51": 1, "location": 1+i/100} for i in range(5)]
    assert interval(rows, "location", 100) == interval(rows, "location", 100)

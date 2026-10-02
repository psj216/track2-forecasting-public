"""## Executive summary (read this first)

A shared release must stay whole across assets, horizons and nearby origins.
"""
from backtesting.expectation01.bootstrap_event import event_blocks

def test_transitive_event_blocks():
    dates=["2001-01-02","2001-01-09","2001-01-16","2001-02-20"]
    events={dates[0]:["A"],dates[1]:["A","B"],dates[2]:["B"],dates[3]:["C"]}
    blocks=event_blocks(dates,events,{"A":"2001-01-01","B":"2001-01-08","C":"2001-02-19"})
    assert blocks[dates[0]]==blocks[dates[1]]==blocks[dates[2]]
    assert blocks[dates[3]]!=blocks[dates[0]]

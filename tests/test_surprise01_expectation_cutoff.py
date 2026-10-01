"""## Executive summary (read this first)

Previous first-release expectations exclude the current and future release.
"""

from qfbench2_track_forecasting.surprise01.event_schema import ReleaseEvent
from qfbench2_track_forecasting.surprise01.expectation import previous_first_release


def test_expectation_cutoff():
    events = [ReleaseEvent(str(n), "CPI", "2020-01", day, None, value, None,
                           "BLS", "https://www.bls.gov/archive", "2026-10-01")
              for n, (day, value) in enumerate([("2020-02-13", .1), ("2020-03-13", 999)])]
    assert previous_first_release(events, "CPI", "2020-03-13") == .1

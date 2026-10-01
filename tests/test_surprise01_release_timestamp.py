"""## Executive summary (read this first)

Release timestamps require a timezone and the actual publication date.
"""

import pytest
from qfbench2_track_forecasting.surprise01.event_schema import ReleaseEvent


def test_timestamp_validated():
    event = ReleaseEvent("a", "CPI", "2020-01", "2020-02-13", "2020-02-13T08:30:00",
                         .1, None, "BLS", "https://www.bls.gov/archive", "2026-10-01")
    with pytest.raises(ValueError):
        event.validate()

"""## Executive summary (read this first)

Only explicit first-release archives qualify; revision values cannot replace actuals.
"""

import pytest
from qfbench2_track_forecasting.surprise01.event_schema import ReleaseEvent


def test_first_release_status():
    event = ReleaseEvent("x", "CPI", "2020-01", "2020-02-13", None, .1, None,
                         "BLS", "https://www.bls.gov/archive", "2026-10-01")
    assert event.validate().actual_first_release == .1
    with pytest.raises(ValueError):
        ReleaseEvent(**{**event.as_dict(), "vintage_status": "LATEST_REVISED"}).validate()

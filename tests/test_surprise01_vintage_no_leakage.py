"""## Executive summary (read this first)

Future releases cannot be loaded into an earlier cutoff snapshot.
"""

from qfbench2_track_forecasting.surprise01.event_schema import ReleaseEvent
from qfbench2_track_forecasting.surprise01.vintage_loader import load_records


def test_release_filter():
    first = ReleaseEvent("a", "CPI", "2020-01", "2020-02-13", None, .1, None,
                         "BLS", "https://www.bls.gov/archive", "2026-10-01").as_dict()
    later = {**first, "release_date": "2020-03-13", "actual_first_release": 999}
    assert len(load_records([first, later], "2020-02-14")) == 1

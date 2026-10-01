"""## Executive summary (read this first)

Changing a later revision does not alter a historical release signal.
"""

from qfbench2_track_forecasting.surprise01.event_schema import ReleaseEvent
from qfbench2_track_forecasting.surprise01.vintage_loader import load_records


def test_revision_mutation():
    e = ReleaseEvent("a", "CPI", "2020-01", "2020-02-13", None, .2, .1,
                     "BLS", "https://www.bls.gov/archive", "2026-10-01").as_dict()
    before = load_records([{**e, "later_revised_actual": .9}], "2020-02-13")
    after = load_records([{**e, "later_revised_actual": -999}], "2020-02-13")
    assert before == after

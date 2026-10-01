"""## Executive summary (read this first)

Use the immediately preceding first-release actual as a generic expectation.
Later revisions and later events never enter a historical expectation.
"""


def previous_first_release(events, family, release_date):
    past = [e for e in events if e.event_type == family and e.release_date < release_date]
    return max(past, key=lambda e: e.release_date).actual_first_release if past else None

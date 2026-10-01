"""## Executive summary (read this first)

Ignore revision columns entirely. Select only verified releases known by cutoff.
"""

from .event_schema import ReleaseEvent


def load_records(records, cutoff):
    events = []
    for row in records:
        fields = {k: row[k] for k in ReleaseEvent.__dataclass_fields__ if k in row}
        event = ReleaseEvent(**fields).validate()
        if event.release_date <= cutoff:
            events.append(event)
    return sorted(events, key=lambda e: (e.release_date, e.event_type))

"""## Executive summary (read this first)

Every event retains its original first-release value and dated source provenance.
Consensus and model-based release innovations cannot share a signal label.
"""

from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta


@dataclass(frozen=True)
class ReleaseEvent:
    event_id: str
    event_type: str
    reference_period: str
    release_date: str
    release_timestamp: str | None
    actual_first_release: float
    expected_value: float | None
    source: str
    source_url: str
    retrieval_date: str
    vintage_status: str = "FIRST_RELEASE_ARCHIVE"
    revision_status: str = "FIRST_ESTIMATE"
    information_type: str = "RELEASE_INNOVATION"
    unit: str = "percentage_points"

    def validate(self):
        date.fromisoformat(self.release_date)
        if self.vintage_status != "FIRST_RELEASE_ARCHIVE":
            raise ValueError("Only verified first release archives are accepted")
        if self.information_type not in {"RELEASE_INNOVATION", "TRUE_CONSENSUS_SURPRISE"}:
            raise ValueError("Unknown information type")
        if not self.source_url.startswith("https://"):
            raise ValueError("Original source URL required")
        if self.release_timestamp:
            t = datetime.fromisoformat(self.release_timestamp)
            if t.tzinfo is None or t.date().isoformat() != self.release_date:
                raise ValueError("Timestamp needs timezone and matching release date")
        return self

    def as_dict(self):
        return asdict(self)

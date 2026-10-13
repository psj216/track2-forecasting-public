"""## Executive summary (read this first)

Check release-clock boundaries and reject post-origin calendar information.
Validate all recovered input vintage identities, without scoring any outcome.
"""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location("r17_experiment", HERE / "experiment.py")
EXPERIMENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPERIMENT)
EVENTS = json.loads((HERE / "frozen_calendar.json").read_text())["events"]


@pytest.mark.parametrize(
    "origin,expected",
    [
        ("2024-01-29", [0, 1, 1]),
        ("2024-11-04", [0, 0, 1]),
        ("2024-01-31", [0, 0, 0]),
    ],
)
def test_expected_release_clock(origin, expected):
    assert EXPERIMENT.event_counts(origin, [1, 2, 4], EVENTS).tolist() == expected


def test_post_origin_calendar_document_is_ineligible():
    future = [{**e, "available_at": "2070-01-01T00:00:00+00:00"} for e in EVENTS]
    assert EXPERIMENT.event_counts("2024-01-29", [1, 2, 4], future).tolist() == [0, 0, 0]


def test_all_recovered_market_vintages_are_bound_to_past():
    manifest = json.loads((HERE / "input-manifest.json").read_text())["records"]
    assert len(manifest) == 154
    assert len({r["origin"] for r in manifest}) == 154
    for r in manifest:
        assert r["vintage"] < r["origin"]
        stamp = r["vintage"].replace("-", "")
        assert r["headers"] == ["observation_date"] + [
            s + "_" + stamp for s in ["DGS2", "DGS5", "DGS10"]
        ]
        assert r["future_nonmissing_values"] == 0

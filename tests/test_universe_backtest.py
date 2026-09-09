"""## Executive summary (read this first)

These tests pin calendar-aware pseudo-asof evaluation. A monthly panel must evaluate a 21-business-
day horizon near the next month, while a return target must accumulate only observations inside the
future interval.
"""

from __future__ import annotations

import pandas as pd

from backtesting.universe_backtest import UniverseCase, cutoff_dates, future_observations


def _monthly_case(target_type: str = "level") -> UniverseCase:
    dates = pd.date_range("2000-01-01", periods=180, freq="MS").astype(str)
    values = pd.Series(range(180), index=dates, dtype=float)
    return UniverseCase(
        unit_id="test-monthly",
        family="T2-F1",
        target_type=target_type,
        target_frequency="monthly",
        assets=["X"],
        horizons=[21],
        histories={"X": values},
    )


def test_monthly_future_uses_first_observation_after_business_day_horizon() -> None:
    case = _monthly_case()
    observed = future_observations(case, "2012-01-01")

    assert observed.tolist() == [145.0]


def test_monthly_return_sums_only_future_interval() -> None:
    case = _monthly_case(target_type="log_return")
    observed = future_observations(case, "2012-01-01")

    assert observed.tolist() == [145.0]


def test_cutoffs_leave_calendar_room_for_target() -> None:
    case = _monthly_case()
    selected = cutoff_dates(case, count=4)

    assert len(selected) == 4
    assert pd.Timestamp(selected[-1]) + pd.offsets.BDay(21) <= pd.Timestamp("2014-12-01")

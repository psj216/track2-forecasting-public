from __future__ import annotations

import numpy as np
import pytest

from qfbench2_track_forecasting.numeric_tail import calibrate_single_cell_tails


def test_tail_transform_preserves_central_draws_and_is_monotone() -> None:
    samples = np.arange(1000, dtype=float).reshape(1000, 1, 1)
    transformed = calibrate_single_cell_tails(samples, lower=0.85, upper=1.15)
    lo, hi = np.quantile(samples, [0.10, 0.90], axis=0)
    central = (samples >= lo) & (samples <= hi)
    np.testing.assert_array_equal(transformed[central], samples[central])
    assert np.all(np.diff(transformed[:, 0, 0]) >= 0)
    assert transformed[0, 0, 0] > samples[0, 0, 0]
    assert transformed[-1, 0, 0] > samples[-1, 0, 0]


def test_tail_transform_bypasses_multi_cell_distribution() -> None:
    samples = np.arange(40, dtype=float).reshape(10, 2, 2)
    np.testing.assert_array_equal(
        calibrate_single_cell_tails(samples, lower=0.85, upper=1.15),
        samples,
    )


@pytest.mark.parametrize("factor", [0.74, 1.26, float("nan")])
def test_tail_transform_rejects_unbounded_factor(factor: float) -> None:
    samples = np.zeros((100, 1, 1), dtype=float)
    with pytest.raises(ValueError):
        calibrate_single_cell_tails(samples, lower=factor, upper=1.0)

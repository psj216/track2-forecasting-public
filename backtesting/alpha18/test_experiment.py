"""## Executive summary (read this first)
Guard the research adapter against calendar, partial-anchor and parquet-order mistakes.
These tests use synthetic numbers, never official future targets or relaxed production assertions.
"""

import numpy as np
import pandas as pd
import pytest
from experiment import ASSETS, matrix, observation_gap


@pytest.mark.parametrize(
    "last,asof,gap",
    [
        ("2024-01-05", "2024-01-08", 1),
        ("2024-01-04", "2024-01-08", 2),
        ("2024-01-08", "2024-01-08", 0),
    ],
)
def test_calendar(last, asof, gap):
    frame = pd.DataFrame(dict(asset=ASSETS, date=[last] * 3))
    assert observation_gap(frame, asof) == gap


@pytest.mark.parametrize("problem", ["different_anchor", "future", "missing_asset"])
def test_reject_ambiguous_anchor(problem):
    frame = pd.DataFrame(dict(asset=ASSETS, date=["2024-01-04"] * 3))
    if problem == "different_anchor":
        frame.loc[0, "date"] = "2024-01-03"
    elif problem == "future":
        frame["date"] = "2024-01-09"
    else:
        frame = frame.iloc[:2]
    with pytest.raises(ValueError, match="common, nonfuture"):
        observation_gap(frame, "2024-01-08")


def test_tensor_mapping_preserves_joint_draw_ids(tmp_path):
    rows = [
        dict(draw=d, asset=asset, horizon=h, value=float(d * 100 + ai * 10 + hi))
        for d in range(3)
        for ai, asset in enumerate(ASSETS)
        for hi, h in enumerate([3, 4, 5, 6])
    ]
    path = tmp_path / "prediction.parquet"
    pd.DataFrame(rows).sample(frac=1, random_state=7).to_parquet(path, index=False)
    values = matrix(path, [3, 4, 5, 6])
    assert values.shape == (3, 3, 4)
    assert np.array_equal(values[:, 1, 2], np.array([12.0, 112.0, 212.0]))
    assert np.array_equal(values[2, 2, :], np.array([220.0, 221.0, 222.0, 223.0]))

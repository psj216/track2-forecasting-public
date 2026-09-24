"""## Executive summary (read this first)

Synthetic checks require chronological purging across cards, baseline ratio identity,
and rejection when apparent gains harm a family or rely on too few cases.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from backtesting.universe_backtest import UniverseCase, _components
from backtesting.v4_ablation import Opportunity, assign_splits, paired_metrics, summary


def test_global_date_split_purges_overlapping_label_intervals() -> None:
    case = UniverseCase("u-synthetic", "T2-F1", "level", "daily", ["SYN-A"], [21], {})
    items = [
        Opportunity(case, f"2000-{m:02d}-01", f"2000-{min(m+2, 12):02d}-28", str(m))
        for m in range(1, 13)
    ]
    selection, holdout = assign_splits(items)
    assert any(x.split == "purged" for x in items)
    assert all(x.end < selection for x in items if x.split == "fit")
    assert all(selection <= x.cutoff and x.end < holdout for x in items if x.split == "select")
    assert all(x.cutoff >= holdout for x in items if x.split == "holdout")


def test_paired_score_uses_existing_pinball_composite_and_single_cell_weights() -> None:
    values = np.random.default_rng(2).normal(size=(1000, 1, 1))
    y = np.array([2.0])
    components = _components(values.reshape(1000, 1), y)
    result = paired_metrics(values, y, components)
    assert abs(result["ratio"] - 1) < 1e-12
    assert result["joint_ratio"] == 0


def test_repeated_seeds_are_not_counted_as_new_cases() -> None:
    rows = [
        dict(
            identity=str(i),
            cutoff=str(pd.Timestamp("2000-01-01") + pd.Timedelta(days=i)),
            family="T2-F1",
            seed=seed,
            ratio=0.98,
            marginal_ratio=0.98,
            tail_ratio=0.98,
        )
        for i in range(15)
        for seed in ("a", "b", "c")
    ]
    report = summary(rows)
    assert report["cases"] == 15
    assert report["pass"] is False

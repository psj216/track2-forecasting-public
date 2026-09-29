"""Date-native masked labels, with target-end purge and eligibility boundaries."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd

from .joint_features import features

HORIZONS = (5, 21, 63, 126, 189)


@dataclass
class JointDataset:
    dates: list[str]
    assets: list[str]
    x: np.ndarray
    g: np.ndarray
    y: np.ndarray
    mask: np.ndarray
    target_end: np.ndarray  # datetime64[ns] per origin/horizon

    def fit_mask(self, cutoff: str) -> np.ndarray:
        return self.mask & (self.target_end[:, :, None] <= np.datetime64(cutoff))


def make_dataset(panel: pd.DataFrame, assets: list[str], *,
                 fit_cutoff: str = "2008-12-31", stride: int = 5,
                 eligibility: dict[str, str] | None = None,
                 max_origins: int | None = 950) -> JointDataset:
    """One row per joint date. Labels never cross the fit cutoff or first target as-of."""
    eligibility = eligibility or {}
    clean = panel.copy()
    clean["date"] = pd.to_datetime(clean.date)
    clean = clean[clean.asset.isin(assets)].sort_values("date")
    wide = clean.drop_duplicates(["date", "asset"], keep="last").pivot(
        index="date", columns="asset", values="value"
    ).reindex(columns=assets).sort_index()
    dates = wide.index
    # Keep actual business dates from the synchronized panel, not calendar offsets.
    start = max(504, int(dates.searchsorted(pd.Timestamp("2001-01-01"))))
    origins = np.arange(start, max(start, len(dates) - max(HORIZONS)), stride)
    if max_origins is not None:
        origins = origins[:max_origins]
    xx, gg, yy, mm, ee, dd = [], [], [], [], [], []
    for i in origins:
        asof = dates[i]
        prefix = wide.iloc[max(0, i - 504):i + 1].stack(future_stack=True).dropna().rename("value").reset_index()
        prefix.columns = ["date", "asset", "value"]
        x, g, _ = features(prefix, assets, str(asof.date()))
        target = np.zeros((len(HORIZONS), len(assets)))
        mask = np.zeros_like(target, dtype=bool)
        ends = []
        for j, h in enumerate(HORIZONS):
            end = dates[i + h]
            ends.append(end)
            for k, a in enumerate(assets):
                before, after = wide.iloc[i, k], wide.iloc[i + h, k]
                first_target = pd.Timestamp(eligibility.get(a, "2100-01-01"))
                if np.isfinite(before) and np.isfinite(after) and end < first_target:
                    target[j, k] = float(after - before)
                    mask[j, k] = True
        xx.append(x); gg.append(g); yy.append(target); mm.append(mask)
        ee.append(ends); dd.append(str(asof.date()))
    if not xx:
        raise ValueError("No synchronized origins with 504 prior observations and 189 future dates")
    return JointDataset(dd, assets, np.array(xx), np.array(gg), np.array(yy),
                        np.array(mm), np.asarray(ee, dtype="datetime64[ns]"))

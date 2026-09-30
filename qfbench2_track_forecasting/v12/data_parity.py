"""Rebuild the V12 supervised calendar and masks from the public card prefixes.

The date, catalog, and maturity rules follow the verified local V12 Git object
123115f3a7f04450f6a525594f9e39b88aa0037b. Labels stay in native units for
the reconstructed decoder; no original model coefficients are loaded here.
"""

from __future__ import annotations

from pathlib import Path
import tomllib

import numpy as np
import pandas as pd

from qfbench2_track_forecasting.cli import _asset_col, _read_panels

from .joint_dataset import HORIZONS, JointDataset
from .joint_features import features_from_series

TRAIN_END = "2008-12-31"
VALID_START = "2009-10-01"
FACTORS = {"MKT", "MOM", "SMB", "HML", "BAB", "QMJ", "RMW", "CMA"}


def catalog(root: Path) -> tuple[dict[str, pd.Series], dict[str, str], dict[str, str]]:
    """Longest pre-card daily prefix, including context-only assets."""
    roster: dict[str, tuple[pd.Series, str, str]] = {}
    first_target: dict[str, str] = {}
    for card_path in sorted((root / "units").glob("t2-F*/card.toml")):
        card = tomllib.loads(card_path.read_text())
        cutoff = str(card["provenance"]["data_cutoff"])[:10]
        for target in card["targets"]["asset_ids"]:
            first_target[str(target)] = min(first_target.get(str(target), cutoff), cutoff)
        for panel_name, frame in _read_panels(card_path.parent).items():
            col = _asset_col(frame)
            if col is None or "date" not in frame or "value" not in frame:
                continue
            if "monthly" in panel_name:
                continue  # Historical macro vintage/release time is not verified.
            for asset, subset in frame.groupby(col):
                asset = str(asset)
                dates = pd.to_datetime(subset["date"].astype(str).str.slice(0, 10))
                values = pd.to_numeric(subset["value"], errors="coerce")
                raw = pd.Series(values.to_numpy(dtype=float), index=dates).sort_index()
                raw = raw.loc[:pd.Timestamp(cutoff)].dropna()
                kind = "log_return" if asset in FACTORS or "factor" in panel_name else "level"
                if asset not in roster:
                    roster[asset] = (raw, cutoff, kind)
                else:
                    old, first, old_kind = roster[asset]
                    if old_kind == kind:
                        roster[asset] = (raw if len(raw) > len(old) else old,
                                         min(first, cutoff), kind)
    series = {a: r[0] for a, r in sorted(roster.items()) if len(r[0]) >= 100}
    kinds = {a: roster[a][2] for a in series}
    first = {a: first_target.get(a, roster[a][1]) for a in series}
    return series, kinds, first


def _prefix(raw: pd.Series, asof: str) -> pd.Series:
    s = raw.copy().sort_index().loc[:pd.Timestamp(asof)]
    return s[~s.index.duplicated(keep="last")].replace([np.inf, -np.inf], np.nan).dropna()


def _label(raw: pd.Series, kind: str, origin: pd.Timestamp, horizon: int,
           first: str, train: bool) -> tuple[float, pd.Timestamp] | None:
    """Original date and gap acceptance; preserve native value units."""
    if origin not in raw.index:
        return None
    target = origin + pd.offsets.BDay(horizon)
    dates = raw.index
    pos = int(dates.searchsorted(target))
    if pos >= len(dates) or dates[pos] >= pd.Timestamp(first):
        return None
    if train and dates[pos] > pd.Timestamp(TRAIN_END):
        return None
    if np.busday_count(np.datetime64(target.date()), np.datetime64(dates[pos].date())) > 3:
        return None
    start = int(dates.searchsorted(origin)) + 1
    window = dates[start - 1:pos + 1].to_numpy(dtype="datetime64[D]")
    if np.any(np.busday_count(window[:-1], window[1:]) > 5):
        return None
    value = (float(raw.iloc[start:pos + 1].sum()) if kind == "log_return"
             else float(raw.iloc[pos] - raw.loc[origin]))
    return value, dates[pos]


def make_parity_dataset(root: Path) -> JointDataset:
    """Retain valid joint origins across all dates, with per-asset target ends."""
    series, kinds, first = catalog(root)
    prepared = {a: _prefix(raw, str(raw.index.max().date())) for a, raw in series.items()}
    assets = sorted(series)
    grid = pd.bdate_range("2001-01-02", max(s.index.max() for s in series.values()),
                          freq="B")[::5]
    xx, gg, yy, mm, ee, dd = [], [], [], [], [], []
    for origin in grid:
        stamp = str(origin.date())
        if TRAIN_END < stamp < VALID_START:
            continue
        x, g, available = features_from_series(prepared, assets, stamp, kinds)
        target = np.zeros((len(HORIZONS), len(assets)))
        mask = np.zeros_like(target, dtype=bool)
        ends = np.full(target.shape, np.datetime64("NaT"), dtype="datetime64[ns]")
        for a, asset in enumerate(assets):
            if not available[a] or first[asset] <= stamp:
                continue
            for hidx, horizon in enumerate(HORIZONS):
                result = _label(prepared[asset], kinds[asset], origin, horizon,
                                first[asset], stamp <= TRAIN_END)
                if result is not None:
                    target[hidx, a], ends[hidx, a] = result
                    mask[hidx, a] = True
        if mask.sum() < 3 or np.sum(mask.any(axis=0)) < 2:
            continue
        xx.append(x); gg.append(g); yy.append(target); mm.append(mask)
        ee.append(ends); dd.append(stamp)
    if not dd:
        raise ValueError("No cutoff-safe joint origins")
    return JointDataset(dd, assets, np.asarray(xx), np.asarray(gg), np.asarray(yy),
                        np.asarray(mm), np.asarray(ee),
                        kinds=kinds, origin_rule="v12-calendar-parity")

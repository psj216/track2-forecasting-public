"""As-of-only features for one synchronized market origin."""

from __future__ import annotations

import numpy as np
import pandas as pd

LOCAL_WINDOWS = (1, 5, 20, 60, 120, 252)
LOCAL_NAMES = tuple(f"mom_{w}" for w in LOCAL_WINDOWS) + (
    "trend_252", "trend_504", "z_252", "z_504", "vol_20", "vol_120",
    "vol_252", "drawdown", "range_120", "skew_120", "kurt_120",
    "regime_duration", "coverage_252",
)
GLOBAL_NAMES = (
    "breadth_5", "breadth_20", "breadth_120", "mom_dispersion",
    "vol_dispersion", "corr_20", "corr_120", "pca_concentration",
    "fx_breadth", "fx_direction", "rate_2y", "rate_10y", "slope_2s10s",
    "curve_change", "mkt", "mom", "smb", "hml", "bab", "qmj", "coverage",
)


def _safe(v: float) -> float:
    return float(v) if np.isfinite(v) else 0.0


def local_features(values: np.ndarray, target_type: str = "level") -> np.ndarray:
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if not len(x):
        return np.zeros(19)
    is_return = target_type in {"log_return", "return", "simple_return", "pct_change"}
    if target_type != "level" and not is_return:
        raise ValueError(f"Unsupported target representation: {target_type}")
    # Return panels already contain one increment per observation. Their
    # cumulative path, not the difference of two daily increments, is the
    # level analogue used by momentum, trend, z-score and drawdown.
    path = np.cumsum(x) if is_return else x
    last = path[-1]
    diff = x if is_return else np.diff(x)
    scale = max(float(np.std(diff[-120:])) if len(diff) else 0., 1e-6)
    f = []
    for w in LOCAL_WINDOWS:
        k = min(w, len(x) - 1)
        movement = np.sum(diff[-k:]) if is_return else last - path[-k-1]
        f.append(float(movement / (scale * np.sqrt(w))))
    for w in (252, 504):
        z = path[-w:]
        f.append((z[-1] - z[0]) / (scale * np.sqrt(max(len(z) - 1, 1))))
    for w in (252, 504):
        z = path[-w:]
        f.append((last - np.mean(z)) / max(float(np.std(z)), scale))
    for w in (20, 120, 252):
        f.append(float(np.std(diff[-w:])) / scale if len(diff) else 1.)
    f.append((last - np.max(path[-252:])) / scale)
    f.append((np.max(path[-120:]) - np.min(path[-120:])) / scale)
    z = diff[-120:]
    centered = z - np.mean(z) if len(z) else z
    sigma = max(float(np.std(z)) if len(z) else 0., 1e-6)
    f.extend((float(np.mean((centered / sigma) ** 3)) if len(z) else 0.,
              float(np.mean((centered / sigma) ** 4) - 3) if len(z) else 0.))
    sign = np.sign(diff[-1]) if len(diff) else 0
    duration = 0
    for d in diff[::-1]:
        if np.sign(d) != sign or duration >= 120:
            break
        duration += 1
    f.extend((duration / 120, min(len(x), 252) / 252))
    return np.clip(np.nan_to_num(f), -20, 20)


def features(panel: pd.DataFrame, assets: list[str], asof: str,
             target_types: dict[str, str] | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The caller may supply future rows; they cannot affect these features."""
    date = pd.Timestamp(asof)
    past = panel.loc[pd.to_datetime(panel.date) <= date]
    histories = {}
    for a in assets:
        rows = past.loc[past.asset == a].sort_values("date")
        histories[a] = pd.Series(rows.value.to_numpy(dtype=float),
                                 index=pd.to_datetime(rows.date)).groupby(level=0).last()
    return features_from_series(histories, assets, asof, target_types)


def features_from_series(histories: dict[str, pd.Series], assets: list[str], asof: str,
                         target_types: dict[str, str] | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Feature calculation on clipped per-asset prefixes, including return kinds."""
    past_series = {a: histories.get(a, pd.Series(dtype=float)).loc[:pd.Timestamp(asof)].tail(505)
                   for a in assets}
    target_types = target_types or {}
    x = np.stack([local_features(past_series[a].to_numpy(dtype=float),
                                 target_types.get(a, "level")) for a in assets])
    available = np.array([len(past_series[a]) >= 45 for a in assets], dtype=bool)
    valid = x[available]
    g = np.zeros(21)
    if len(valid):
        g[:3] = np.mean(valid[:, [1, 2, 4]] > 0, axis=0)
        g[3] = np.std(valid[:, 2])
        g[4] = np.std(valid[:, 10])
        aligned = pd.DataFrame(past_series)
        movements = aligned.diff()
        for asset in assets:
            if asset in movements and target_types.get(asset, "level") in {
                    "log_return", "return", "simple_return", "pct_change"}:
                movements[asset] = aligned[asset]
        for index, window in ((5, 20), (6, 120)):
            corr = movements.tail(window).corr(min_periods=max(5, window // 3)).to_numpy()
            if corr.size:
                upper = corr[np.triu_indices_from(corr, k=1)]
                upper = upper[np.isfinite(upper)]
                g[index] = float(np.mean(upper)) if len(upper) else 0.
        complete = movements.tail(120).fillna(0).to_numpy(dtype=float)
        if len(complete) > 5 and complete.shape[1] > 1:
            cov = np.cov(complete, rowvar=False)
            eigen = np.maximum(np.linalg.eigvalsh(np.atleast_2d(cov)), 0)
            g[7] = float(eigen[-1] / max(np.sum(eigen), 1e-8))
        fx = [i for i, a in enumerate(assets) if a in {"AUD", "CAD", "JPY", "EUR", "GBP", "CHF"} and available[i]]
        if fx:
            g[8] = np.mean(x[fx, 2] > 0)
            g[9] = np.mean(x[fx, 2])
        for index, name in ((10, "UST_2Y"), (11, "UST_10Y")):
            if len(past_series.get(name, ())):
                g[index] = past_series[name].iloc[-1]
        g[12] = g[11] - g[10]
        if {"UST_2Y", "UST_10Y"} <= set(aligned):
            rates = aligned[["UST_2Y", "UST_10Y"]].dropna().tail(21)
            if len(rates) > 1:
                g[13] = float((rates.iloc[-1, 1] - rates.iloc[-1, 0]) -
                              (rates.iloc[0, 1] - rates.iloc[0, 0]))
        for index, name in enumerate(("MKT", "MOM", "SMB", "HML", "BAB", "QMJ"), 14):
            if name in assets:
                g[index] = x[assets.index(name), 2]
        g[-1] = np.mean(available)
    return x, np.clip(g, -20, 20), available

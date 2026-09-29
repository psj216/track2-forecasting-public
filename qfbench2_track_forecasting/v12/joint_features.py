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


def local_features(values: np.ndarray) -> np.ndarray:
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if not len(x):
        return np.zeros(19)
    last = x[-1]
    diff = np.diff(x)
    scale = max(float(np.std(diff[-120:])) if len(diff) else 0., 1e-6)
    f = []
    for w in LOCAL_WINDOWS:
        f.append((last - x[-min(len(x), w + 1)]) / (scale * np.sqrt(w)))
    for w in (252, 504):
        z = x[-w:]
        f.append((z[-1] - z[0]) / (scale * np.sqrt(max(len(z) - 1, 1))))
    for w in (252, 504):
        z = x[-w:]
        f.append((last - np.mean(z)) / max(float(np.std(z)), scale))
    for w in (20, 120, 252):
        f.append(float(np.std(diff[-w:])) / scale if len(diff) else 1.)
    f.append((last - np.max(x[-252:])) / scale)
    f.append((np.max(x[-120:]) - np.min(x[-120:])) / scale)
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


def features(panel: pd.DataFrame, assets: list[str], asof: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The caller may supply future rows; they cannot affect these features."""
    date = pd.Timestamp(asof)
    past = panel.loc[pd.to_datetime(panel.date) <= date]
    histories = {}
    for a in assets:
        rows = past.loc[past.asset == a].sort_values("date")
        histories[a] = rows.value.to_numpy(dtype=float)
    x = np.stack([local_features(histories[a]) for a in assets])
    available = np.array([len(histories[a]) >= 21 for a in assets], dtype=bool)
    valid = x[available]
    g = np.zeros(21)
    if len(valid):
        g[:3] = np.mean(valid[:, [1, 2, 4]] > 0, axis=0)
        g[3] = np.std(valid[:, 2])
        g[4] = np.std(valid[:, 10])
        g[7] = np.var(valid[:, 2]) / max(float(np.sum(np.var(valid, axis=0))), 1e-8)
        fx = [i for i, a in enumerate(assets) if a in {"AUD", "CAD", "JPY", "EUR", "GBP", "CHF"} and available[i]]
        if fx:
            g[8] = np.mean(x[fx, 2] > 0)
            g[9] = np.mean(x[fx, 2])
        for index, name in ((10, "UST_2Y"), (11, "UST_10Y")):
            if name in histories and len(histories[name]):
                g[index] = histories[name][-1]
        g[12] = g[11] - g[10]
        for index, name in enumerate(("MKT", "MOM", "SMB", "HML", "BAB", "QMJ"), 14):
            if name in assets:
                g[index] = x[assets.index(name), 2]
        g[-1] = np.mean(available)
    return x, np.clip(g, -20, 20), available

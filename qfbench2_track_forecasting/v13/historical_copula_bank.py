"""Private outcome-derived bank. Its reference ranks are recomputed per as-of."""

from __future__ import annotations

from pathlib import Path
import numpy as np

from .state_retrieval import nearest


class HistoricalBank:
    def __init__(self, path: str | Path):
        with np.load(path, allow_pickle=False) as bank:
            self.dates = bank["dates"]
            self.end = bank["target_end"]
            self.values = bank["values"]
            self.mask = bank["mask"]
            self.state = bank["state"]
            self.assets = list(bank["assets"].astype(str))
            self.horizons = list(map(int, bank["horizons"]))

    def rank_worlds(self, current: np.ndarray, asof: str, assets: list[str],
                    horizons: list[int], draws: int, seed: int) -> np.ndarray | None:
        cutoff = np.datetime64(asof)
        a_idx = [self.assets.index(a) for a in assets]
        # Runtime cards may ask e.g. 127BD while the bank stores 126BD.
        h_idx = [min(range(len(self.horizons)),
                     key=lambda i: (abs(self.horizons[i] - h), i)) for h in horizons]
        matured = self.end < cutoff
        full = (self.dates < cutoff) & np.all(
            self.mask[:, h_idx][:, :, a_idx] & matured[:, h_idx, None], axis=(1, 2)
        )
        neighbours = nearest(current, self.state, full, 32)
        if not len(neighbours):
            return None
        rng = np.random.default_rng(seed)
        chosen = rng.choice(neighbours, draws, replace=True)
        out = np.empty((draws, len(h_idx), len(a_idx)))
        for j, h in enumerate(h_idx):
            for k, a in enumerate(a_idx):
                # Crucial repair: even the percentile denominator is local to cutoff.
                reference = self.values[self.mask[:, h, a] & matured[:, h], h, a]
                if not len(reference):
                    return None
                source = self.values[chosen, h, a]
                ordered = np.sort(reference, kind="stable")
                out[:, j, k] = (np.searchsorted(ordered, source, side="left") +
                                0.5 * (np.searchsorted(ordered, source, side="right") -
                                       np.searchsorted(ordered, source, side="left")) + 0.5) / (len(reference) + 1)
        return np.clip(out, 0, np.nextafter(1., 0.))

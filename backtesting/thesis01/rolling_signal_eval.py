"""## Executive summary (read this first)

Freeze signed slopes from development origins with mature labels by 2012-12-31.
The 2013-2017 validation and 2018-2023 final periods never refit coefficients.
"""

from pathlib import Path

import numpy as np

from qfbench2_track_forecasting.thesis01.location_alpha import fit_beta
from .negative_controls import time_shuffle, peer_permutation


def prepared(private_panel: Path):
    data = np.load(private_panel)
    origins = data["origins"]
    grid = data["grid_rows"]
    dev = origins < np.datetime64("2013-01-01")
    mature = data["target_end"] <= np.datetime64("2012-12-31")
    signals = {"same": data["same"][grid], "lag": data["lag"][grid]}
    signals["time_shuffled"] = time_shuffle(signals["lag"], origins)
    signals["peer_permuted"] = peer_permutation(data["z"], grid)
    betas, counts = {}, {}
    for name, signal in signals.items():
        betas[name], counts[name] = fit_beta(signal, data["normalized"], mature, dev)
    return data, signals, betas, counts

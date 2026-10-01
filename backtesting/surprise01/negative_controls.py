"""## Executive summary (read this first)

Fix event-level sign flips, within-family date permutations, and family mapping.
Sign flips cannot test an absolute-surprise scale head; the other controls can.
"""

import numpy as np
import pandas as pd
from qfbench2_track_forecasting.surprise01 import FAMILIES


def maps(cases, seed=1903):
    rng = np.random.default_rng(seed)
    events = cases[["event_id", "event_type", "surprise"]].drop_duplicates()
    flips = {event: int(rng.choice([-1, 1])) for event in sorted(events["event_id"].unique())}
    dates = {}
    for family, part in events.groupby("event_type", sort=True):
        part = part.sort_values("event_id")
        permuted = rng.permutation(part["surprise"].to_numpy())
        dates.update({(e, family): float(s) for e, s in zip(part["event_id"], permuted)})
    family = dict(zip(FAMILIES, FAMILIES[1:] + FAMILIES[:1]))
    return flips, dates, family

"""## Executive summary (read this first)

Store every historically predictive directed edge and its event count.
The first/second historical subperiod coefficients describe stability only.
"""

import csv
from pathlib import Path

import numpy as np

from qfbench2_track_forecasting.origin01.propagation_model import fit
from qfbench2_track_forecasting.thesis01.asset_semantics import family


def write_edges(training: Path, model: Path, output: Path, kinds: dict):
    d, m = np.load(training), np.load(model)
    assets = d["assets"].tolist()
    first = d["dates"] < np.datetime64("2013-01-01")
    c1, _, _ = fit(d["source"][first], d["q"][first], d["gate"][first])
    c2, _, _ = fit(d["source"][~first], d["q"][~first], d["gate"][~first])
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as handle:
        w = csv.writer(handle)
        w.writerow(["source", "source_group", "target", "target_group", "horizon",
                    "coefficient", "fit_rows", "source_event_count", "sign",
                    "coef_2001_2012", "coef_2013_2023"])
        for i, target in enumerate(assets):
            for h, horizon in enumerate(m["horizons"]):
                for j, source in enumerate(assets):
                    if i == j:
                        continue
                    coef = float(m["coef"][i, h, j])
                    w.writerow([source, family(source, kinds[source]), target,
                                family(target, kinds[target]), int(horizon), coef,
                                int(m["count"][i, h]), int(m["events"][i, j]),
                                int(np.sign(coef)), float(c1[i, h, j]), float(c2[i, h, j])])
    return len(assets) * (len(assets) - 1) * len(m["horizons"])

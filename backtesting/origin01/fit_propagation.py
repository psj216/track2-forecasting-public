"""## Executive summary (read this first)

Fit all directed ridge edges once from fully matured historical target values.
The coefficient artifact cannot be refitted during final evaluation.
"""

import argparse
import json
from pathlib import Path

import numpy as np

from qfbench2_track_forecasting.origin01.propagation_model import fit


def train(training: Path, output: Path):
    data = np.load(training)
    coef, count, events = fit(data["source"], data["q"], data["gate"])
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output, coef=coef, count=count, events=events,
                        assets=data["assets"], horizons=data["horizons"],
                        max_target_end=np.datetime64("2023-12-31"))
    return {"trained_models": int((count >= 30).sum()),
            "total_models": int(count.size), "coefficient_nonzero": int((coef != 0).sum()),
            "median_fit_rows": float(np.median(count)),
            "max_fit_label": "2023-12-31"}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--training", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(train(a.training, a.out), indent=2))

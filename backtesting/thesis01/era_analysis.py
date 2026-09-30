"""## Executive summary (read this first)

Report era-specific sparse-grid behavior. Pre-2013 episodes provide development
signal diagnostics only; they never become independent OOS score evidence.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .diagnostics import aggregate, correlation
from .rolling_signal_eval import prepared


def episode(year: int) -> str:
    if year < 2007:
        return "pre-GFC"
    if year <= 2010:
        return "GFC/aftermath"
    if year <= 2019:
        return "post-GFC low-rate"
    if year <= 2021:
        return "COVID"
    return "inflation/hiking"


def summarize(panel: Path, private_ledger: Path, output: Path) -> dict:
    data, signals, betas, _ = prepared(panel)
    rows = json.loads(private_ledger.read_text())["primary"]
    origins = pd.to_datetime(data["origins"])
    result = {}
    for name in ("same", "lag"):
        result[name] = {}
        for era in ("pre-GFC", "GFC/aftermath", "post-GFC low-rate",
                    "COVID", "inflation/hiking"):
            mask = np.asarray([episode(d.year) == era for d in origins])
            x = np.broadcast_to(signals[name][:, :, None], data["normalized"].shape)
            ic = correlation(x[mask].ravel(), data["normalized"][mask].ravel())
            part = [r for r in rows if r["signal"] == name and r["episode"] == era]
            result[name][era] = {"sparse_origin_count": int(mask.sum()),
                                 "signal_ic": ic,
                                 "crps": aggregate(part) if part else None,
                                 "crps_is_oos": bool(part),
                                 "frozen_beta_positive": int(np.nansum(betas[name] > 0)),
                                 "frozen_beta_negative": int(np.nansum(betas[name] < 0))}
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--private-ledger", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    summarize(args.panel, args.private_ledger, args.out)

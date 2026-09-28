"""## Executive summary (read this first)

Inspect public as-of cards without reading outcomes. Confirm V5.1 text behavior
and exact preservation for every multi-cell grid and every F3 forecast.
"""

from __future__ import annotations

import json
import sys
import tomllib
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qfbench2_track_forecasting.cli import _read_panels, _series
from qfbench2_track_forecasting.numeric_v3 import forecast_numeric_v3
from qfbench2_track_forecasting.numeric_v4 import calibrate_single_cell_tails
from qfbench2_track_forecasting.text_first_v5 import apply_text_first_v5


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    counts: Counter[str] = Counter()
    for path in sorted((root / "units").glob("t2-F*/card.toml")):
        card = tomllib.loads(path.read_text())
        family = card["metadata"]["category"]
        target = card["targets"]
        assets, horizons = target["asset_ids"], target["horizons"]
        asof = card["provenance"]["data_cutoff"]
        panels = _read_panels(path.parent / "panels")
        histories = {asset: _series(panels, asset, asof) for asset in assets}
        draws = 1000 if family == "T2-F4" else 500
        numeric = forecast_numeric_v3(
            histories,
            assets,
            horizons,
            target["target_type"],
            target["target_frequency"],
            draws,
            17,
            family,
        ).samples
        baseline, meta = apply_text_first_v5(
            numeric,
            histories if family in {"T2-F1", "T2-F4"} else {},
            assets,
            horizons,
            target["target_type"],
            target["target_frequency"],
            family,
            asof,
            17,
            path.parent / "text",
            target.get("value_unit", ""),
            interpreter_version="v5.1",
        )
        eligible = family != "T2-F3" and len(assets) * len(horizons) == 1
        candidate = calibrate_single_cell_tails(baseline, 0.85, 0.85) if eligible else baseline
        if not eligible:
            assert candidate is baseline
        else:
            assert np.isfinite(candidate).all()
            assert not np.array_equal(candidate, baseline)
        counts[family] += 1
        counts[f"{family}:text_active"] += int(meta["applied"])
        counts[f"{family}:tail_active"] += int(eligible)
        counts["exact_unchanged"] += int(not eligible)
    print(json.dumps(dict(sorted(counts.items())), indent=2))


if __name__ == "__main__":
    main()

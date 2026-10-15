"""## Executive summary (read this first)
Compare neutral-text monthly output to the unchanged frozen kernel at helper-resolved steps.
This checks step selection, spread and dependence without inventing scoring math or outcomes.
"""

import json
import pathlib
import sys
import tomllib

import numpy as np
import pandas as pd

sys.path.insert(0, "/opt/finalfit03")
from official_horizons import monthly_horizon_steps

from qfbench2_track_forecasting.cli import _draw, _read_panels, _series
from qfbench2_track_forecasting.numeric_v1 import (
    _diff_without_gaps,
    _observation_period_business_days,
)

unit, out = map(pathlib.Path, sys.argv[1:3])
card = tomllib.loads((unit / "card.toml").read_text())
spec = json.loads((unit / "forecast_spec.json").read_text())
meta = json.loads((out / "forecast_meta.json").read_text())
assert (
    meta["forecast_adjustment_applied"] is False
), "Kernel comparator restricted to neutral text fixtures."
assets = card["targets"]["asset_ids"]
keys = card["targets"]["horizons"]
asof = card["provenance"]["data_cutoff"]
panels = _read_panels(unit)
hist = {a: _series(panels, a, asof) for a in assets}
step_matrix = monthly_horizon_steps(
    assets,
    keys,
    {a: str(h.index[-1])[:10] for a, h in hist.items()},
    asof=asof,
    card=card,
    forecast_spec=spec,
).astype(int)
union = sorted(set(step_matrix.ravel().tolist()))
period = _observation_period_business_days(
    pd.DataFrame({a: _diff_without_gaps(h) for a, h in hist.items()}).dropna()
)
raw, stats = _draw(
    panels,
    assets,
    [s * period for s in union],
    asof,
    meta["n_draws"],
    17,
    target_type="level",
    target_frequency="monthly",
    family=card["metadata"]["category"],
)
assert stats["observation_horizons"] == union
wanted = np.stack(
    [raw[:, ai, [union.index(int(s)) for s in step_matrix[ai]]] for ai in range(len(assets))],
    axis=1,
)
frame = pd.read_parquet(out / "forecast.parquet").set_index(["draw", "asset", "horizon"])
actual = (
    frame.reindex(pd.MultiIndex.from_product([range(meta["n_draws"]), assets, keys]))["value"]
    .to_numpy()
    .reshape(wanted.shape)
)
assert np.array_equal(
    wanted, actual
), "Candidate changed more than explicit monthly step selection."
print(
    json.dumps(
        dict(
            kernel_exact=True,
            assets=assets,
            output_keys=keys,
            step_matrix=step_matrix.tolist(),
            monthly_union=union,
            cell_std=actual.std(axis=0).tolist(),
            covariance_exact=True,
        )
    )
)

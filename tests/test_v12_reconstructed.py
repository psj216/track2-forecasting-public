import json

import numpy as np
import pandas as pd

from qfbench2_track_forecasting.v12.joint_dataset import make_dataset
from qfbench2_track_forecasting.v12.joint_features import features
from qfbench2_track_forecasting.v12.train import fit
from qfbench2_track_forecasting.v12.engine import JointEngine


def panel(n=1100):
    rng = np.random.default_rng(17)
    dates = pd.bdate_range("2000-01-03", periods=n)
    curves = [np.cumsum(rng.standard_normal(n)) for _ in range(6)]
    return pd.DataFrame([(date, f"ASSET_{k}", float(curves[k][i]))
                         for k in range(6) for i, date in enumerate(dates)],
                        columns=["date", "asset", "value"])


def test_mask_target_end_and_date_native():
    p = panel()
    d = make_dataset(p, sorted(p.asset.unique()), fit_cutoff="2004-01-01", max_origins=80)
    assert d.x.shape[1:] == (6, 19)
    assert d.g.shape[1] == 21
    assert d.y.shape[1:] == (5, 6)
    assert np.all(d.target_end[d.fit_mask("2003-01-01").any(axis=2)] <= np.datetime64("2003-01-01"))


def test_future_mutation_invariant():
    p = panel(800)
    x, g, cov = features(p, ["ASSET_0", "ASSET_1"], "2002-02-01")
    altered = p.copy()
    altered.loc[altered.date > "2002-02-01", "value"] = 999999
    xx, gg, cc = features(altered, ["ASSET_0", "ASSET_1"], "2002-02-01")
    np.testing.assert_array_equal(x, xx)
    np.testing.assert_array_equal(g, gg)
    np.testing.assert_array_equal(cov, cc)
    assert np.isfinite(g).all() and g[7] > 0
    assert g[5] != 0 and g[6] != 0


def test_fit_psd_shape_seed_and_runtime(tmp_path):
    p = panel()
    assets = sorted(p.asset.unique())
    d = make_dataset(p, assets, fit_cutoff="2004-02-01", max_origins=80)
    a = fit(d, "2004-02-01")
    path = tmp_path / "artifact.json"
    path.write_text(json.dumps(a))
    e = JointEngine(path)
    forecast1, _ = e.forecast(p, assets[:3], [5, 21, 63, 126], "2004-01-15", 64, 42)
    forecast2, _ = e.forecast(p, assets[:3], [5, 21, 63, 126], "2004-01-15", 64, 42)
    assert forecast1.shape == (64, 4, 3)
    assert np.isfinite(forecast1).all()
    np.testing.assert_array_equal(forecast1, forecast2)
    for cov in a["state_covariance"]:
        assert min(np.linalg.eigvalsh(cov)) >= -1e-8


def test_unsupported_decoder_explicit(tmp_path):
    p = panel()
    d = make_dataset(p, sorted(p.asset.unique()), max_origins=80)
    a = fit(d)
    path = tmp_path / "artifact.json"
    path.write_text(json.dumps(a))
    import pytest
    with pytest.raises(ValueError, match="Untrained decoder"):
        JointEngine(path).forecast(p, ["UNKNOWN"], [21], "2004-01-15")

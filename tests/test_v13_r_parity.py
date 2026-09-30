"""Parity regressions for reconstructed target units and scale-neutral PCA."""

import numpy as np
import pandas as pd

from qfbench2_track_forecasting.v12.joint_dataset import make_dataset
from qfbench2_track_forecasting.v12.latent_state import fit_factors
from backtesting.v13_copula.evaluate_proxy import eligible


def test_factor_target_is_cumulative_increment_and_level_is_difference():
    dates = pd.bdate_range('2000-01-03', periods=800)
    rows = [(d, a, float(i * .01 if a == 'LEVEL' else .002))
            for i, d in enumerate(dates) for a in ('LEVEL', 'RETURN', 'THIRD')]
    panel = pd.DataFrame(rows, columns=['date', 'asset', 'value'])
    data = make_dataset(panel, ['LEVEL', 'RETURN', 'THIRD'],
                        target_types={'RETURN': 'log_return'}, max_origins=1)
    assert np.isclose(data.y[0, 0, 0], 0.05)
    assert np.isclose(data.y[0, 0, 1], 5 * .002)
    assert np.isclose(data.y[0, 1, 1], 21 * .002)


def test_pca_factors_invariant_to_asset_units():
    rng = np.random.default_rng(7)
    y = rng.normal(size=(150, 5))
    mask = np.ones_like(y, dtype=bool)
    mask[::4, 2] = False
    baseline = fit_factors(y, mask)
    converted = fit_factors(y * np.array([1., 100., .01, 2., 3.]), mask)
    assert np.isclose(baseline[3], converted[3], atol=1e-9)
    np.testing.assert_allclose(abs(baseline[2]), abs(converted[2]), atol=1e-9)


def test_proxy_return_truth_uses_horizon_sum(tmp_path):
    card = tmp_path / 'card.toml'
    card.write_text('''[provenance]
data_cutoff = "2000-02-01"
[targets]
asset_ids = ["RETURN"]
horizons = [5, 21]
target_type = "log_return"
target_frequency = "daily"
''')
    dates = pd.bdate_range('2000-01-03', periods=100)
    history = pd.DataFrame({'RETURN': np.full(100, .002)}, index=dates)
    info = eligible(tmp_path, history)
    assert info is not None
    np.testing.assert_allclose(info[3][:, 0], [.01, .042])

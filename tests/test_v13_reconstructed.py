import json

import numpy as np
import pandas as pd
import pytest

from qfbench2_track_forecasting.v12.engine import JointEngine
from qfbench2_track_forecasting.v12.joint_dataset import make_dataset
from qfbench2_track_forecasting.v12.train import fit
from qfbench2_track_forecasting.v13.engine import CopulaEngine
from qfbench2_track_forecasting.v13.historical_copula_bank import HistoricalBank
from qfbench2_track_forecasting.v13.rank_copula import percentile_ranks
from qfbench2_track_forecasting.v13.support_gate import supported


@pytest.fixture
def setup_engine(tmp_path):
    rng = np.random.default_rng(91)
    dates = pd.bdate_range("2000-01-03", periods=1100)
    assets = ["AAA", "BBB", "CCC"]
    curves = [np.cumsum(rng.normal(0, 0.2, len(dates))) + 100 for _ in assets]
    panel = pd.DataFrame([(date, a, curves[k][i]) for k,a in enumerate(assets)
                          for i,date in enumerate(dates)], columns=["date", "asset", "value"])
    d = make_dataset(panel, assets, max_origins=90)
    artifact = fit(d, decoder_types={a:"level" for a in assets})
    path = tmp_path / "artifact.json"
    path.write_text(json.dumps(artifact))
    return CopulaEngine(path), JointEngine(path), panel, assets


def test_finite_marginals_rank_alignment_and_seed(setup_engine):
    e, _, panel, assets = setup_engine
    n = 128
    rng = np.random.default_rng(44)
    base = rng.normal(size=(n, 2, 2))
    base[:, 1, 0] += base[:, 0, 0]
    worlds, meta = e.forecast(base, panel, assets[:2], [21, 63], "2004-01-01", seed=8)
    again, _ = e.forecast(base, panel, assets[:2], [21, 63], "2004-01-01", seed=8)
    assert meta["fallback"] is None
    for name in "ABC":
        assert np.array_equal(worlds[name], again[name])
        np.testing.assert_array_equal(np.sort(worlds["A"], axis=0),
                                      np.sort(worlds[name], axis=0))
    np.testing.assert_array_equal(percentile_ranks(worlds["A"]), percentile_ranks(base))
    # A whole source row carries both horizons; swapping source rows would fail.
    assert np.array_equal(np.argsort(worlds["A"][:, 0, 0], kind="stable"),
                          np.argsort(base[:, 0, 0], kind="stable"))


def test_stable_ties_and_exact_whole_card_fallback(setup_engine):
    e, _, panel, assets = setup_engine
    base = np.zeros((64, 2, 2))
    base[::3] = 1
    expected = percentile_ranks(base)
    assert np.array_equal(expected, percentile_ranks(base))
    output, meta = e.forecast(base, panel, assets[:2], [21, 63], "2004-01-01",
                              target_frequency="monthly")
    assert meta["fallback"] == "whole_card_v51"
    for name in "ABC":
        np.testing.assert_array_equal(output[name], base)
    unknown, _ = e.forecast(base, panel, ["AAA", "UNKNOWN"], [21, 63], "2004-01-01")
    np.testing.assert_array_equal(unknown["A"], base)


def test_no_future_access_and_marginal_statistical_match(setup_engine):
    e, v12, panel, assets = setup_engine
    rng = np.random.default_rng(22)
    base = rng.normal(size=(5000, 2, 1))
    asof = "2004-01-01"
    output, _ = e.forecast(base, panel, assets[:1], [5, 21], asof, seed=2)
    v12_out, _ = v12.forecast(panel, assets[:1], [5, 21], asof, 5000, 73)
    for j in range(2):
        sd = np.std(v12_out[:, j, 0])
        assert abs(np.std(output["A"][:, j, 0]) / sd - 1) < 0.1
        assert np.max(abs(np.quantile(output["A"][:, j, 0], [.05,.5,.95]) -
                          np.quantile(v12_out[:, j, 0], [.05,.5,.95]))) < 0.12 * sd
    future = panel.copy()
    future.loc[future.date > asof, "value"] += 1e6
    altered, _ = e.forecast(base, future, assets[:1], [5, 21], asof, seed=2)
    np.testing.assert_array_equal(output["A"], altered["A"])


def test_cutoff_local_bank_reference(tmp_path):
    path = tmp_path / "bank.npz"
    dates = np.array(["2001-01-01", "2001-01-02", "2001-02-01"], dtype="datetime64[ns]")
    ends = np.array([["2001-01-03"], ["2001-01-04"], ["2001-02-05"]], dtype="datetime64[ns]")
    values = np.array([[[1., 10.]], [[2., 20.]], [[999., 999.]]])
    kwargs = dict(dates=dates, target_end=ends, mask=np.ones_like(values, bool),
                  state=np.zeros((3, 19)), assets=np.array(["AAA", "BBB"]), horizons=np.array([21]))
    np.savez(path, values=values, **kwargs)
    original = HistoricalBank(path).rank_worlds(np.zeros(19), "2001-01-10",
                                            ["AAA", "BBB"], [21], 64, 9)
    values[-1] = -999
    np.savez(path, values=values, **kwargs)
    altered = HistoricalBank(path).rank_worlds(np.zeros(19), "2001-01-10",
                                           ["AAA", "BBB"], [21], 64, 9)
    np.testing.assert_array_equal(original, altered)
    assert np.array_equal(original[:, 0, 0] >= .5, original[:, 0, 1] >= .5)


def test_support_manifest_threshold_and_type(setup_engine):
    e, _, _, assets = setup_engine
    ok, _ = supported(e.artifact, assets[:2], "level", "daily")
    assert ok
    assert not supported(e.artifact, assets[:2], "log_return", "daily")[0]
    artifact = dict(e.artifact, fit_cells_by_asset=[99, 500, 500])
    assert not supported(artifact, assets[:2], "level", "daily")[0]


def test_runtime_never_fits(setup_engine, monkeypatch):
    e, _, panel, assets = setup_engine
    from qfbench2_track_forecasting.v12 import train
    monkeypatch.setattr(train, "fit", lambda *_args, **_kwargs: (_ for _ in ()).throw(
        AssertionError("runtime fit invoked")))
    base = np.arange(64 * 2, dtype=float).reshape(64, 2, 1)
    output, _ = e.forecast(base, panel, assets[:1], [21, 63], "2004-01-01")
    assert output["A"].shape == base.shape


def test_bank_duplicate_prototypes_preserve_every_finite_marginal(setup_engine, tmp_path):
    e, _, panel, assets = setup_engine
    bank = tmp_path / "bank.npz"
    np.savez(bank, dates=np.array(["2003-01-01", "2003-02-01"], dtype="datetime64[ns]"),
             target_end=np.array([["2003-03-01", "2003-04-01"],
                                  ["2003-03-02", "2003-04-02"]], dtype="datetime64[ns]"),
             values=np.array([[[1., 2.], [3., 4.]], [[5., 6.], [7., 8.]]]),
             mask=np.ones((2, 2, 2), bool), state=np.zeros((2, 19)),
             assets=np.array(assets[:2]), horizons=np.array([21, 63]))
    e.bank = HistoricalBank(bank)
    base = np.random.default_rng(7).normal(size=(128, 2, 2))
    out, meta = e.forecast(base, panel, assets[:2], [21, 63], "2004-01-01", seed=12)
    assert meta["bank_used"]
    for name in "BC":
        np.testing.assert_array_equal(np.sort(out[name], axis=0), np.sort(out["A"], axis=0))

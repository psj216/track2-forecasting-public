"""## Executive summary (read this first)

Exercise the V5 success route, its cutoff and ambiguity fallbacks, and exact
F2/F3 preservation with independent synthetic histories and dated documents.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from qfbench2_track_forecasting.text_first_v5 import _asset_direction, apply_text_first_v5


def _corpus(root: Path, timestamp: str, text: str) -> None:
    (root / "dated.txt").write_text(text)
    (root / "corpus_index.json").write_text(
        json.dumps(
            {
                "documents": [
                    {
                        "doc_id": "dated",
                        "timestamp": timestamp,
                        "file": "dated.txt",
                        "doc_type": "fomc_statement",
                        "source": "synthetic",
                    },
                ]
            }
        )
    )


def _inputs() -> tuple[pd.Series, np.ndarray, str]:
    dates = pd.bdate_range("2018-01-01", periods=1200)
    rng = np.random.default_rng(17)
    series = pd.Series(2.0 + np.cumsum(rng.normal(0, 0.02, len(dates))), index=dates)
    samples = rng.normal(series.iloc[-1], 0.2, size=(1000, 1, 2))
    return series, samples, str(dates[-1].date())


def test_dated_risk_signal_activates_pre_asof_worlds(tmp_path: Path) -> None:
    series, samples, asof = _inputs()
    _corpus(tmp_path, asof, "Several banks face funding stress and bank failures are increasing.")
    result, meta = apply_text_first_v5(
        samples,
        {"UST_2Y": series},
        ["UST_2Y"],
        [21, 63],
        "level",
        "daily",
        "T2-F4",
        asof,
        5,
        tmp_path,
        "percent",
    )
    assert meta["applied"] and meta["evidence_ids"] == ["dated"]
    assert meta["last_world_date"] == asof
    assert meta["directions"] == {"UST_2Y": -1}
    changed = np.any(result != samples, axis=(1, 2))
    assert changed.sum() == meta["sleeve_draws"]
    assert np.array_equal(result[~changed], samples[~changed])
    assert np.isfinite(result).all()


def test_post_asof_and_ambiguous_text_are_exact_fallback(tmp_path: Path) -> None:
    series, samples, asof = _inputs()
    _corpus(
        tmp_path,
        str((pd.Timestamp(asof) + pd.Timedelta(days=1)).date()),
        "Banks face severe funding stress and bank failures are increasing.",
    )
    for text_is_late in (True, False):
        if not text_is_late:
            _corpus(tmp_path, asof, "Monetary policy remains under discussion.")
        result, meta = apply_text_first_v5(
            samples,
            {"UST_2Y": series},
            ["UST_2Y"],
            [21, 63],
            "level",
            "daily",
            "T2-F4",
            asof,
            5,
            tmp_path,
            "percent",
        )
        assert not meta["applied"] and np.array_equal(result, samples)


def test_f2_f3_exactly_return_original_buffer(tmp_path: Path) -> None:
    _, samples, asof = _inputs()
    for family in ("T2-F2", "T2-F3"):
        result, meta = apply_text_first_v5(
            samples,
            {},
            ["UST_2Y"],
            [21, 63],
            "level",
            "daily",
            family,
            asof,
            5,
            tmp_path,
            "percent",
        )
        assert result is samples and meta["numeric_fallback_exact"]
        assert np.array_equal(result, samples)


def test_fx_quote_direction_is_explicit() -> None:
    from qfbench2_track_forecasting.text_first_v5 import Event

    stress = Event("liquidity_stress", 0.9, ("dated",), "bank funding stress")
    assert _asset_direction(stress, "AUD", "usd_per_aud") == -1
    assert _asset_direction(stress, "JPY", "jpy_per_usd") == -1
    assert _asset_direction(stress, "CHF", "chf_per_usd") == -1
    assert _asset_direction(stress, "DKK", "dkk_per_usd") == 0

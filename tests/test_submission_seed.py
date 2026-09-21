"""## Executive summary (read this first)

The harness seed is the default; an explicit CLI seed wins. Test selection before sampling.
"""

from pathlib import Path

import pytest

from qfbench2_track_forecasting import cli


@pytest.mark.parametrize(
    ("environment", "arguments", "selected"),
    [(None, [], 0), ("137", [], 137), ("137", ["--seed", "29"], 29)],
)
def test_harness_seed_selection(monkeypatch, tmp_path, environment, arguments, selected):
    if environment is None:
        monkeypatch.delenv("QFBENCH_SEED", raising=False)
    else:
        monkeypatch.setenv("QFBENCH_SEED", environment)

    class SamplingReached(Exception):
        pass

    def inspect_seed(*args, **_kwargs):
        assert args[5] == selected
        raise SamplingReached

    monkeypatch.setattr(cli, "_draw", inspect_seed)
    unit = Path(__file__).parents[1] / "units/t2-F4-short-vol-2018"
    with pytest.raises(SamplingReached):
        cli.main(
            [
                "--panels",
                str(unit / "panels"),
                "--text",
                str(unit / "text"),
                "--asof",
                "2018-01-26",
                "--out",
                str(tmp_path / "forecast.parquet"),
                *arguments,
            ]
        )

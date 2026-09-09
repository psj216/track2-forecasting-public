"""## Executive summary (read this first)

Compare dynamic cross-asset transmission candidates with frozen Numeric v2.1 on every public
multi-asset card. Each candidate starts from the exact same V2.1 draws and only reorders marginal
values across draws. This isolates the joint-dependence effect: marginal CRPS and tail pinball must
remain unchanged by construction.

The metric implementations are imported from the pinned public toolkit through the existing
universe backtest helper. No private normalization scale or realized card answer is used.
"""

from __future__ import annotations

import argparse
import pathlib
from typing import Any

import pandas as pd

from qfbench2_track_forecasting.numeric_v3 import (
    V3_CONFIG,
    TransmissionConfig,
    apply_dynamic_transmission,
)
from qfbench2_track_forecasting.numeric_v21 import V21_CONFIG, forecast_numeric_v21

from .universe_backtest import (
    _components,
    _seed,
    cutoff_dates,
    future_observations,
    load_universe,
    summarize_paired,
)


def candidate_configs() -> tuple[TransmissionConfig, ...]:
    """One-factor transmission-strength candidates around the initial V3 design."""
    return (
        TransmissionConfig(
            name="dynamic transmission 0.15",
            strength=0.15,
            long_window=1260,
            identity_shrinkage=0.0,
        ),
        V3_CONFIG,
        TransmissionConfig(
            name="dynamic transmission 0.35",
            strength=0.35,
            long_window=1260,
            identity_shrinkage=0.0,
        ),
    )


def run_transmission_backtest(
    root: pathlib.Path,
    cutoff_count: int,
    n_draws: int,
    configs: tuple[TransmissionConfig, ...] | None = None,
    seed_salt: str = "",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return multi-asset case details and V2.1-paired diagnostic summaries."""
    selected = configs or candidate_configs()
    rows: list[dict[str, Any]] = []
    for case in load_universe(root):
        if len(case.assets) < 2:
            continue
        for cutoff in cutoff_dates(case, cutoff_count):
            histories = {
                asset: series[series.index.astype(str).str.slice(0, 10) <= cutoff]
                for asset, series in case.histories.items()
            }
            observed = future_observations(case, cutoff)
            baseline = forecast_numeric_v21(
                histories,
                case.assets,
                case.horizons,
                case.target_type,
                case.target_frequency,
                n_draws,
                _seed(case.unit_id, cutoff, seed_salt),
            )
            rows.append(
                {
                    "unit_id": case.unit_id,
                    "family": case.family,
                    "cutoff": cutoff,
                    "candidate": V21_CONFIG.name,
                    **_components(baseline.samples.reshape(n_draws, -1), observed),
                }
            )
            for config in selected:
                forecast = apply_dynamic_transmission(
                    baseline,
                    histories,
                    case.assets,
                    case.target_type,
                    config,
                    family=case.family,
                    reference_horizon_index=case.horizons.index(max(case.horizons)),
                )
                rows.append(
                    {
                        "unit_id": case.unit_id,
                        "family": case.family,
                        "cutoff": cutoff,
                        "candidate": config.name,
                        **_components(forecast.samples.reshape(n_draws, -1), observed),
                    }
                )
    detail = pd.DataFrame(rows)
    return detail, summarize_paired(detail, V21_CONFIG.name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Dynamic transmission pseudo-asof comparison")
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path("."))
    parser.add_argument("--cutoffs", type=int, default=3)
    parser.add_argument("--n-draws", type=int, default=500)
    parser.add_argument("--seed-salt", default="transmission-v1")
    args = parser.parse_args()
    detail, summary = run_transmission_backtest(
        args.root, args.cutoffs, args.n_draws, seed_salt=args.seed_salt
    )
    print(f"multi-asset cards: {detail['unit_id'].nunique()}")
    print(f"historical cases: {detail[['unit_id', 'cutoff']].drop_duplicates().shape[0]}")
    print(summary.to_string(float_format=lambda value: f"{value:.6f}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

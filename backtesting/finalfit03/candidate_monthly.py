"""## Executive summary (read this first)
Isolated candidate entrypoint for the official explicit-month horizon contract.
The original package, immutable image, model constants and daily route are unchanged.
Only monthly sampling lengths are translated; original authored keys remain in outputs.
Per-asset monthly cells select from the unchanged kernel on the union of required steps.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tomllib

import numpy as np
import pandas as pd
from official_horizons import HorizonMetadataError, monthly_horizon_steps

from qfbench2_track_forecasting import cli
from qfbench2_track_forecasting.integrated_v4 import _history_steps
from qfbench2_track_forecasting.numeric_v1 import (
    _diff_without_gaps,
    _observation_period_business_days,
)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--panels", type=pathlib.Path)
    parser.add_argument("--card", type=pathlib.Path)
    parser.add_argument("--asof")
    parser.add_argument("--out", type=pathlib.Path)
    args, _ = parser.parse_known_args(argv)
    if "--help" in argv or args.panels is None:
        return cli.main(argv)
    card_path = args.card
    if card_path is None:
        card_path = next(
            (
                p
                for p in [args.panels / "card.toml", args.panels.parent / "card.toml"]
                if p.is_file()
            ),
            None,
        )
    if card_path is None:
        return cli.main(argv)
    card = tomllib.loads(card_path.read_text())
    if card["targets"].get("target_frequency", "daily") != "monthly":
        return cli.main(argv)
    spec_path = card_path.parent / "forecast_spec.json"
    spec = json.loads(spec_path.read_text()) if spec_path.is_file() else None
    assets = card["targets"]["asset_ids"]
    keys = card["targets"]["horizons"]
    panels = cli._read_panels(args.panels)
    histories = {a: cli._series(panels, a, args.asof) for a in assets}

    def daily_cadence(history):
        dates = pd.DatetimeIndex(pd.to_datetime(history.index))
        if len(dates) < 30 or dates.has_duplicates:
            return False
        gaps = np.diff(dates.to_numpy()).astype("timedelta64[D]").astype(float)
        per_month = pd.Series(1, index=dates.to_period("M")).groupby(level=0).sum()
        return bool(0 < np.median(gaps) <= 3 and per_month.median() >= 8)

    explicit_periods = any(
        "observation_periods" in source.get("targets", {}) for source in (card, spec or {})
    ) or any(q.get("observation_period") for q in (spec or {}).get("questions", []))
    if all(daily_cadence(history) for history in histories.values()):
        if explicit_periods:
            raise SystemExit("Monthly observation periods conflict with daily target observations.")
        print(
            "Legacy dense-daily input declared monthly; daily sampling retained.", file=sys.stderr
        )
        return cli.main(argv)
    if card["targets"].get("target_type", "level") != "level":
        raise SystemExit("Explicit monthly mapping requires monthly level targets.")
    for history in histories.values():
        periods = pd.DatetimeIndex(history.index).to_period("M")
        if periods.has_duplicates or len(periods) < 3:
            raise SystemExit("Monthly target series need unique monthly observations.")
        if not np.isfinite(history.to_numpy()).all():
            raise SystemExit("Monthly target observations must be finite.")
        if np.median(np.diff(periods.asi8)) != 1:
            raise SystemExit("The selected target series do not have monthly cadence.")
    try:
        monthly = monthly_horizon_steps(
            assets,
            keys,
            {a: str(s.index[-1])[:10] for a, s in histories.items()},
            asof=args.asof,
            card=card,
            forecast_spec=spec,
        ).astype(int)
    except HorizonMetadataError as error:
        raise SystemExit(str(error)) from None
    steps = sorted(set(monthly.ravel().tolist()))
    indices = [[steps.index(int(value)) for value in row] for row in monthly]
    memo = {}

    def select_cells(full):
        return np.stack([full[:, ai, positions] for ai, positions in enumerate(indices)], axis=1)

    original_draw, original_apply, original_rationale = (
        cli._draw,
        cli.apply_text_first_v5,
        cli._rationale,
    )
    receipt = dict(
        official_helper_source="f43655cdb624a3e5e5fed772ed9313ef57a54bc5",
        authored_horizon_keys=keys,
        observation_steps=monthly[0].tolist()
        if np.all(monthly == monthly[0])
        else monthly.tolist(),
        per_asset_observation_steps=monthly.tolist(),
        sampling_step_union=steps,
        last_observation_dates={a: str(s.index[-1])[:10] for a, s in histories.items()},
        output_keys_preserved=True,
    )

    def draw(
        panels,
        assets,
        horizons,
        asof,
        n_draws,
        seed,
        target_type="level",
        target_frequency="daily",
        family="T2-F1",
    ):
        prepared = {
            a: histories[a] if target_type == "log_return" else _diff_without_gaps(histories[a])
            for a in assets
        }
        period = _observation_period_business_days(pd.DataFrame(prepared).dropna())
        effective = [s * period for s in steps]
        samples, stats = original_draw(
            panels, assets, effective, asof, n_draws, seed, target_type, target_frequency, family
        )
        if stats["observation_horizons"] != steps:
            raise SystemExit("Monthly adapter sampling-step mismatch; refuse output.")
        receipt["numeric_observation_steps"] = stats["observation_horizons"]
        receipt["numeric_period_business_days"] = period
        memo["full_numeric_samples"] = samples
        return select_cells(samples), stats

    def apply(
        samples,
        histories,
        assets,
        horizons,
        target_type,
        target_frequency,
        family,
        asof,
        seed,
        text_dir,
        value_unit,
        interpreter_version="v5",
    ):
        if family not in {"T2-F1", "T2-F4"}:
            return original_apply(
                samples,
                histories,
                assets,
                horizons,
                target_type,
                target_frequency,
                family,
                asof,
                seed,
                text_dir,
                value_unit,
                interpreter_version,
            )
        history_steps = _history_steps(histories, assets, target_type, asof)
        period = _observation_period_business_days(history_steps)
        adjusted, metadata = original_apply(
            memo["full_numeric_samples"],
            histories,
            assets,
            [s * period for s in steps],
            target_type,
            target_frequency,
            family,
            asof,
            seed,
            text_dir,
            value_unit,
            interpreter_version,
        )
        return select_cells(adjusted), metadata

    def rationale(*a, **kw):
        original = original_rationale(*a, **kw)
        paragraph = (
            "A requested business-day horizon is mapped to the panel's "
            "observation frequency before sampling;"
        )
        original = original.replace(
            paragraph,
            "Monthly sampling uses the task's explicit observation periods; "
            "authored horizon keys are retained.",
        )
        return (
            original
            + "\n## Monthly horizon compatibility receipt\n\n"
            + json.dumps(receipt, sort_keys=True)
            + "\n"
        )

    cli._draw, cli.apply_text_first_v5, cli._rationale = draw, apply, rationale
    try:
        result = cli.main(argv)
        metadata_path = args.out.parent / "forecast_meta.json"
        metadata = json.loads(metadata_path.read_text())
        metadata["monthly_horizon_mapping"] = receipt
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
        return result
    finally:
        cli._draw, cli.apply_text_first_v5, cli._rationale = (
            original_draw,
            original_apply,
            original_rationale,
        )


if __name__ == "__main__":
    raise SystemExit(main())

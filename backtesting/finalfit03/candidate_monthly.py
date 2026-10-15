"""## Executive summary (read this first)
Isolated candidate entrypoint for the official explicit-month horizon contract.
The original package, immutable image, model constants and daily route are unchanged.
Only monthly sampling lengths are translated; original authored keys remain in outputs.
Different per-asset step grids fail explicitly rather than invent a joint adaptation.
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
    dense = []
    for history in histories.values():
        dates = pd.DatetimeIndex(history.index)
        dense.append(len(dates.to_period("M").unique()) != len(dates))
    explicit = any(
        field in source.get("targets", {})
        for source in (card, spec or {})
        for field in ["observation_periods", "target_dates"]
    ) or any(
        q.get("observation_period") or q.get("target_date")
        for q in (spec or {}).get("questions", [])
    )
    if any(dense):
        if all(dense) and not explicit:
            print(
                "Legacy dense-daily input declared monthly; "
                "original daily-cadence behavior retained.",
                file=sys.stderr,
            )
            return cli.main(argv)
        raise SystemExit(
            "Monthly mapping requires one observation per month for every target asset."
        )
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
    if not np.all(monthly == monthly[0]):
        raise SystemExit(
            "Different per-asset monthly step grids require separate validation; "
            "unsupported by this minimal candidate."
        )
    steps = monthly[0].tolist()
    original_draw, original_apply, original_rationale = (
        cli._draw,
        cli.apply_text_first_v5,
        cli._rationale,
    )
    receipt = dict(
        official_helper_source="f43655cdb624a3e5e5fed772ed9313ef57a54bc5",
        authored_horizon_keys=keys,
        observation_steps=steps,
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
        return samples, stats

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
        history_steps = _history_steps(histories, assets, target_type, asof)
        period = _observation_period_business_days(history_steps)
        return original_apply(
            samples,
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

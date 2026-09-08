"""Track-2 Numeric v1 submission CLI.

Implements the `forecast` verb from the shared submission contract:

    forecast --panels /input/panels/ --text /input/text/ --asof YYYY-MM-DD \
             --out /output/forecast.parquet

and writes the three deliverables the contract requires next to `--out`:

    forecast.parquet         the scored artifact — joint draws [draw, asset, horizon, value]
    forecast_meta.json       the sidecar g1_schema validates
    forecast_rationale.md    required, NEVER scored — the derivation, for human review

This Phase 3 implementation is the numeric-only anchor for later text ablation. It separates level
and log-return targets, blends recent and long history, detects regime fragility, and samples
joint historical blocks along one coherent path. It reads no text yet and says so in its sidecar.

Run offline. No network and no model weights.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

import numpy as np
import pandas as pd

from .limits import ParseLimits
from .numeric_v1 import forecast_numeric_v1

DEFAULT_DRAWS = 500
_RATIONALE_NAME = "forecast_rationale.md"


def _read_panels(panels_dir: pathlib.Path) -> dict[str, pd.DataFrame]:
    """Every parquet under --panels, keyed by filename stem.

    Accepts the contract layout (`/input/panels/*.parquet`) and also tolerates a unit that keeps
    its panels one level up, which is how the shipped exemplar was laid out before this CLI
    existed. Tolerating it here means a card authored either way still runs.
    """
    found = sorted(panels_dir.glob("*.parquet"))
    if not found and panels_dir.parent.is_dir():
        found = sorted(panels_dir.parent.glob("*.parquet"))
    if not found:
        raise SystemExit(f"no .parquet found under {panels_dir} (or its parent)")
    return {p.stem: pd.read_parquet(p) for p in found}


#: Both spellings occur in the shipped cards — the exemplar unit uses `asset_id`, the pilot and
#: prospective batches use `asset`. A reference implementation has to read either, or it works on
#: some cards and not others for a reason that has nothing to do with forecasting.
_ASSET_COLS = ("asset", "asset_id")


def _asset_col(df: pd.DataFrame) -> str | None:
    return next((c for c in _ASSET_COLS if c in df.columns), None)


def _series(panels: dict[str, pd.DataFrame], asset: str, asof: str) -> pd.Series:
    """The history of one asset up to and including the as-of, from whichever panel holds it."""
    for df in panels.values():
        col = _asset_col(df)
        if col is None:
            continue
        sub = df[df[col].astype(str) == asset]
        if sub.empty:
            continue
        sub = sub.copy()
        # Dates arrive as either strings or datetimes depending on how the panel was written.
        sub["date"] = sub["date"].astype(str).str.slice(0, 10)
        sub = sub[sub["date"] <= asof].sort_values("date")
        if not sub.empty:
            return sub.set_index("date")["value"].astype(float)
    seen = sorted(
        {
            str(v)
            for df in panels.values()
            if (c := _asset_col(df)) is not None
            for v in df[c].unique()
        }
    )
    raise SystemExit(
        f"asset {asset!r} not present in any panel at or before {asof}. "
        f"Panels carry: {', '.join(seen) if seen else '(no asset column found)'}"
    )


def _draw(
    panels: dict[str, pd.DataFrame],
    assets: list[str],
    horizons: list[int],
    asof: str,
    n_draws: int,
    seed: int,
    target_type: str = "level",
) -> tuple[np.ndarray, dict[str, Any]]:
    """Target-aware joint block bootstrap with regime diagnostics and coherent horizons."""
    hist = {a: _series(panels, a, asof) for a in assets}
    try:
        result = forecast_numeric_v1(hist, assets, horizons, target_type, n_draws, seed)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    return result.samples, result.metadata


def _rationale(
    unit_id: str,
    asof: str,
    assets: list[str],
    horizons: list[int],
    n_draws: int,
    stats: dict[str, Any],
    text_dir: pathlib.Path,
) -> str:
    n_docs = len(list(text_dir.glob("*.txt"))) if text_dir.is_dir() else 0
    ladder = "\n".join(
        f"| {a} | {stats['anchor'][a]:.4f} | {stats['daily_sd'][a]:.4f} | "
        f"{stats['daily_sd'][a] * np.sqrt(h):.4f} | {h} |"
        for a in assets
        for h in horizons
    )
    return f"""# Forecast rationale — {unit_id}

As of **{asof}**, joint distribution over {", ".join(assets)} at horizon(s)
{", ".join(str(h) for h in horizons)} business days. {n_draws} draws.

## Target and anchor

Target type: **{stats["target_type"]}**. Level forecasts start from the last observed level.
Return forecasts start from zero and accumulate daily returns. The engine used
{stats["n_history_rows"]} overlapping rows dated no later than the as-of.

## Adjustments

The centre uses a strongly shrunk blend of 20, 60, 120 and long-window daily drift. It is capped
relative to forecast uncertainty so a short trend cannot dominate a long horizon.

## Scale and shape

Five-day historical blocks are sampled from a blend of recent and full history. This preserves
observed non-Gaussian tails and volatility clustering. Current fragility is
**{stats['regime']['fragility']:.3f}**; recent-history weight is
**{stats['regime']['recent_weight']:.3f}** and uncertainty scale is
**{stats['regime']['uncertainty_scale']:.3f}**.

The draws are **joint**: each sampled block contains every asset. Each draw is also one path
through time, and every requested horizon is read from that same path.

## Adjustment ledger

| asset | model anchor | effective daily sd | sd at horizon | horizon (BD) |
|---|---|---|---|---|
{ladder}

Daily drift: {stats['daily_drift']}.

## What the text corpus contributed

**Nothing.** {n_docs} document(s) were present and none was read. This Phase 3 model is the
numeric-only anchor for the later reasoning ablation.

## What would change this forecast

New numeric observations that change momentum, volatility, correlation or fragility. Text
evidence is intentionally deferred to the reasoning layer.
"""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="forecast",
        description="QFBench 2.0 Track-2 Numeric v1 submission.",
    )
    p.add_argument("--panels", type=pathlib.Path, required=True)
    p.add_argument("--text", type=pathlib.Path, required=True)
    p.add_argument("--asof", required=True)
    p.add_argument(
        "--out",
        type=pathlib.Path,
        required=True,
        help="path to forecast.parquet; the sidecars are written beside it",
    )
    p.add_argument(
        "--card",
        type=pathlib.Path,
        default=None,
        help="card.toml; defaults to <panels>/../card.toml. Supplies assets/horizons.",
    )
    p.add_argument("--n-draws", type=int, default=None)
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args(argv)

    # --panels names the unit root (contract) but a card may still keep a panels/ subdir, so look
    # in the panels dir first and only then one level up. Deriving it as parent/ unconditionally
    # resolves to "/" when --panels is /input/, which is how this was wrong the first time.
    card_path = a.card
    if card_path is None:
        for cand in (a.panels / "card.toml", a.panels.parent / "card.toml"):
            if cand.exists():
                card_path = cand
                break
    if card_path is None or not card_path.exists():
        raise SystemExit(
            f"card.toml not found in {a.panels} or {a.panels.parent}; pass --card explicitly"
        )
    import tomllib

    card = tomllib.loads(card_path.read_text())
    tgt = card["targets"]
    assets = list(tgt["asset_ids"])
    horizons = [int(h) for h in tgt["horizons"]]
    unit_id = card["task"]["id"]
    # The card's `n_draws_min` is AUTHORITATIVE and was previously advisory: the reference
    # producer read it, the scorer never did, and the scorer instead compared the submission
    # against the participant's own declared `n_draws`. It is now a floor on both sides — this
    # producer honours it, and `limits.min_draws` enforces the contract floor in the scorer, in
    # code no missing module can skip.
    card_floor = int(card.get("scoring", {}).get("params", {}).get("n_draws_min", 0) or 0)
    floor = max(card_floor, DEFAULT_DRAWS, ParseLimits().min_draws)
    n_draws = max(a.n_draws or floor, floor)
    if n_draws > ParseLimits().max_draws:
        raise SystemExit(
            f"--n-draws {n_draws} exceeds the contract ceiling {ParseLimits().max_draws}; the "
            "scorer refuses a submission above it"
        )

    panels = _read_panels(a.panels)
    target_type = str(tgt.get("target_type", "level"))
    samples, stats = _draw(
        panels, assets, horizons, a.asof, n_draws, a.seed, target_type=target_type
    )

    out_dir = a.out.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {"draw": d, "asset": asset, "horizon": h, "value": float(samples[d, ai, hi])}
            for d in range(n_draws)
            for ai, asset in enumerate(assets)
            for hi, h in enumerate(horizons)
        ]
    ).to_parquet(a.out, index=False)

    (out_dir / "forecast_meta.json").write_text(
        json.dumps(
            {
                "unit_id": unit_id,
                "asof": a.asof,
                "representation": "samples",
                "asset_ids": assets,
                "horizons": horizons,
                "n_draws": n_draws,
                "target": target_type,
                "rationale": {
                    "file": _RATIONALE_NAME,
                    "method": "regime-aware joint block bootstrap v1, no text",
                },
            },
            indent=2,
        )
        + "\n"
    )

    (out_dir / _RATIONALE_NAME).write_text(
        _rationale(unit_id, a.asof, assets, horizons, n_draws, stats, a.text)
    )

    print(f"wrote {a.out.name}, forecast_meta.json and {_RATIONALE_NAME} to {out_dir}")
    print(f"  {len(assets)} asset(s) x {len(horizons)} horizon(s), {n_draws} draws")
    return 0


if __name__ == "__main__":
    sys.exit(main())

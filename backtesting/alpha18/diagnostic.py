"""## Executive summary (read this first)
Freeze exact-source research inputs, reproduce the safe CLI, and diagnose exposed history.
Targets, individual losses and draws stay in a separate private work directory.
Scoring math is imported from the pinned official toolkit, never reimplemented.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib
import importlib.util
import io
import json
import os
import pathlib
import re
import shutil
import sys
import time
import tomllib

import numpy as np
import pandas as pd

G10 = {"AUD", "CAD", "CHF", "DKK", "EUR", "GBP", "JPY", "NOK", "NZD", "SEK"}
HORIZONS = [1, 2, 3, 4]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def load(path):
    return json.loads(path.read_text())


def args():
    p = argparse.ArgumentParser()
    p.add_argument("stage", choices=["prepare", "bridge", "forecast", "score"])
    p.add_argument("--repo", type=pathlib.Path, required=True)
    p.add_argument("--baseline", type=pathlib.Path, required=True)
    p.add_argument("--official", type=pathlib.Path, required=True)
    p.add_argument("--work", type=pathlib.Path, required=True)
    p.add_argument("--vintages", type=pathlib.Path)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--stop", type=int, default=10000)
    return p.parse_args()


def baseline_cli(a):
    os.environ.update(FORECAST_MODE="text-first-v5.1", NUMERIC_VARIANT="v3", TEXT_INTEGRATION="on")
    for k in list(os.environ):
        if k.startswith("MODEL_") or k in {"TEAM_KEY", "HOUSE_TOKEN"}:
            os.environ.pop(k)
    sys.path.insert(0, str(a.baseline))
    from qfbench2_track_forecasting import cli

    assert pathlib.Path(cli.__file__).resolve().is_relative_to(a.baseline)
    return cli


def bridge(a):
    cli = baseline_cli(a)
    identity = load(a.repo / "FINALFIT03-IMAGE-BUILD.json")["identity"]["production"]
    matches = {
        n: sha(a.baseline / "qfbench2_track_forecasting" / n) == h for n, h in identity.items()
    }
    assert len(matches) == 26 and all(matches.values())
    prior = load(a.repo / "backtesting/v51_delivery_emergency11/results/determinism_audit.json")
    rows = []
    for item in prior["units"]:
        unit = a.baseline / "units" / item["unit"]
        card = tomllib.loads((unit / "card.toml").read_text())
        out = a.work / "bridge" / unit.name / "forecast.parquet"
        argv = [
            "--panels",
            str(unit),
            "--text",
            str(unit / "text"),
            "--asof",
            card["provenance"]["data_cutoff"],
            "--out",
            str(out),
        ]
        with contextlib.redirect_stdout(io.StringIO()):
            rc = cli.main(argv)
        values = pd.read_parquet(out)["value"].to_numpy(dtype=np.float64)
        rows.append(
            dict(
                unit=unit.name,
                exit_code=rc,
                parquet_exact=sha(out) == item["hashes"][0]["forecast.parquet"],
                values_exact=hashlib.sha256(values.tobytes()).hexdigest()
                == item["numeric_hashes"][0],
                parquet_sha256=sha(out),
            )
        )
        print("BRIDGE", unit.name, rows[-1]["parquet_exact"], flush=True)
    result = dict(
        executive_summary="New host bridge to archived safe Docker outputs, not new Docker.",
        source_matches=matches,
        runs=rows,
        passed=all(x["parquet_exact"] and x["values_exact"] and x["exit_code"] == 0 for x in rows),
        python=sys.version,
        numpy=np.__version__,
        pandas=pd.__version__,
        pyarrow=importlib.import_module("pyarrow").__version__,
        common=importlib.import_module("qfbench2_common").__version__,
        dependency_note=(
            "Math libraries match image; common2.6.1 vs image2."
            "4.2. Exact four-output bridge required."
        ),
    )
    put(a.repo / "ALPHA18-BASELINE-IDENTITY.json", result)
    assert result["passed"]


def normalized_frame(path):
    f = pd.read_parquet(path).rename(columns={"asset_id": "asset"})
    f["date"] = pd.to_datetime(f["date"]).dt.strftime("%Y-%m-%d")
    return f[["date", "asset", "value"]].copy()


def prepare(a):
    """Construct no forecasts and inspect no forecast error during roster selection."""
    units = a.official / "units"
    eligible, excluded, paths = [], [], {}
    for unit in sorted(units.iterdir()):
        if not (unit / "card.toml").is_file():
            continue
        c = tomllib.loads((unit / "card.toml").read_text())
        t = c.get("targets", {})
        assets = t.get("asset_ids", [])
        reason = None
        if not unit.name.startswith("t2-F"):
            reason = "not_historical_family_card"
        elif t.get("target_frequency", "daily") != "daily" or t.get("target_type") != "level":
            reason = "not_daily_level_market_target"
        elif not assets or any(not (x.startswith("UST_") or x in G10) for x in assets):
            reason = "outside_fixed_UST_G10_roster"
        if reason:
            excluded.append(dict(card_id=unit.name, reason=reason))
            continue
        eligible.append((unit, c))
    # Label-only source selection is by maximum date coverage and lexical tie-break, not errors.
    for stem in ("rates_daily", "g10_fx_daily"):
        candidates = []
        for p in sorted(units.glob("*/" + stem + ".parquet")):
            f = normalized_frame(p)
            candidates.append((f["date"].max(), len(f), str(p), p, f))
        _, _, _, p, f = max(candidates, key=lambda x: x[:3])
        paths[stem] = dict(
            path=str(p.relative_to(a.official)),
            sha256=sha(p),
            last_date=f["date"].max(),
            rows=len(f),
        )
        f.to_parquet(a.work / ("labels-" + stem + ".parquet"), index=False)
    roster = []
    for unit, c in eligible:
        origin = str(c["provenance"]["data_cutoff"])
        name = "card-" + unit.name
        dest = a.work / "inputs" / name
        dest.mkdir(parents=True, exist_ok=True)
        content = (unit / "card.toml").read_text()
        content = re.sub(r"(?m)^(horizons\s*=\s*)\[[^\n]*\]", r"\g<1>[1, 2, 3, 4]", content)
        (dest / "card.toml").write_text(content)
        shutil.copytree(unit / "text", dest / "text", dirs_exist_ok=True)
        files = {}
        for p in sorted(unit.glob("*.parquet")):
            f = normalized_frame(p)
            # Date cutoff, never later sibling panel data, determines the numeric input.
            f = f[f["date"] <= origin]
            f.to_parquet(dest / p.name, index=False)
            files[p.name] = dict(
                source_sha256=sha(p),
                input_sha256=sha(dest / p.name),
                last_date=f["date"].max(),
                rows=len(f),
            )
        roster.append(
            dict(
                id=name,
                group="authored_market_projection",
                card_id=unit.name,
                origin=origin,
                family=c["metadata"]["category"],
                assets=c["targets"]["asset_ids"],
                horizons=HORIZONS,
                input_files=files,
                original_card_sha256=sha(unit / "card.toml"),
                projected_card_sha256=sha(dest / "card.toml"),
                text_hashes={
                    p.name: sha(p) for p in sorted((dest / "text").glob("*")) if p.is_file()
                },
                availability=(
                    "Organizer staged cutoff; independent historical H1"
                    "0/H15 release-vintage proof UNKNOWN"
                ),
            )
        )
    # The previous study's existing vintages are reused only as input data, never its forecasts.
    if a.vintages:
        for p in sorted(a.vintages.glob("????-??-??.csv")):
            origin = p.stem
            v = pd.read_csv(p)
            expected = (pd.Timestamp(origin) - pd.Timedelta(days=1)).strftime("%Y%m%d")
            assert list(v.columns)[1:] == [
                "DGS2_" + expected,
                "DGS5_" + expected,
                "DGS10_" + expected,
            ]
            rows = []
            for col, asset in zip(v.columns[1:], ["UST_2Y", "UST_5Y", "UST_10Y"], strict=True):
                x = pd.DataFrame(
                    dict(
                        date=v.iloc[:, 0], asset=asset, value=pd.to_numeric(v[col], errors="coerce")
                    )
                )
                x = x.dropna()
                x = x[x["date"] < origin]
                rows.append(x)
            f = pd.concat(rows, ignore_index=True)
            dest = a.work / "inputs" / ("vintage-" + origin)
            (dest / "text").mkdir(parents=True, exist_ok=True)
            f.to_parquet(dest / "rates_daily.parquet", index=False)
            card = (
                'schema_version="2.0"\n[task]\nid="alpha18-'
                + origin
                + '"\ntrack="forecasting"\n[metadata]\ncategory="T2-F3"\n'
                + '[targets]\nasset_ids=["UST_2Y","UST_5Y","UST_10Y"]\n'
                + 'horizons=[1,2,3,4]\ntarget_type="level"\ntarget_frequency="daily"\n'
                + 'value_unit="percent"\n[provenance]\ndata_cutoff="'
                + origin
                + '"\n'
            )
            (dest / "card.toml").write_text(card)
            roster.append(
                dict(
                    id=dest.name,
                    group="past_vintage_UST",
                    origin=origin,
                    family="T2-F3",
                    assets=["UST_2Y", "UST_5Y", "UST_10Y"],
                    horizons=HORIZONS,
                    raw_vintage_sha256=sha(p),
                    projected_card_sha256=sha(dest / "card.toml"),
                    input_files={
                        "rates_daily.parquet": dict(
                            input_sha256=sha(dest / "rates_daily.parquet"),
                            last_date=f["date"].max(),
                            rows=len(f),
                        )
                    },
                    availability=(
                        "Previous-calendar-day ALFRED vintage; observations"
                        " strictly before origin. Original R17 retrieval re"
                        "ceipt reused."
                    ),
                )
            )
    manifest = dict(
        executive_summary=(
            "Complete deterministic diagnostic roster frozen be" "fore forecasts/errors."
        ),
        official_commit="24582e957b0cbb9ea7268bec9636188a0e2c21fa",
        horizons=HORIZONS,
        seed=0,
        draws=1000,
        cards=roster,
        excluded=excluded,
        label_only_sources=paths,
        contamination="EXPLORATORY_EXPOSED_HISTORY",
        labels_never_forecast_inputs=True,
        target_calendar="pandas BDay (Mon–Fri); exact-date missing labels blocked, never imputed",
        inference_clock_note=(
            "Authored historical card dates do not independentl"
            "y prove publication-time vintage authenticity."
        ),
    )
    put(a.repo / "backtesting/alpha18/input-manifest.json", manifest)
    print(
        json.dumps(
            dict(
                stage="PREPARED",
                cards=len(eligible),
                vintages=len(roster) - len(eligible),
                exclusions=len(excluded),
                families=pd.Series([x["family"] for x in roster]).value_counts().to_dict(),
            )
        ),
        flush=True,
    )


def forecast(a):
    assert load(a.repo / "ALPHA18-BASELINE-IDENTITY.json")["passed"]
    cli = baseline_cli(a)
    m = load(a.repo / "backtesting/alpha18/input-manifest.json")
    cards = m["cards"][a.start : a.stop]
    start = time.monotonic()
    receipts = []
    for i, row in enumerate(cards):
        unit = a.work / "inputs" / row["id"]
        for n, v in row["input_files"].items():
            assert sha(unit / n) == v["input_sha256"]
        assert sha(unit / "card.toml") == row["projected_card_sha256"]
        out = a.work / "forecasts" / row["id"] / "forecast.parquet"
        receipt = out.parent / "receipt.json"
        if receipt.exists() and load(receipt).get("passed"):
            receipts.append(load(receipt))
            continue
        argv = [
            "--panels",
            str(unit),
            "--text",
            str(unit / "text"),
            "--asof",
            row["origin"],
            "--out",
            str(out),
            "--n-draws",
            "1000",
            "--seed",
            "0",
        ]
        with contextlib.redirect_stdout(io.StringIO()) as log:
            rc = cli.main(argv)
        out.with_suffix(".log").write_text(log.getvalue())
        f = pd.read_parquet(out)
        assert rc == 0 and np.isfinite(f["value"]).all()
        assert set(f["horizon"]) == set(HORIZONS)
        assert len(f) == 1000 * len(row["assets"]) * 4
        r = dict(
            id=row["id"],
            passed=True,
            forecast_sha256=sha(out),
            rows=len(f),
            command=argv,
            meta_sha256=sha(out.parent / "forecast_meta.json"),
        )
        put(receipt, r)
        receipts.append(r)
        if i % 10 == 0 or i == len(cards) - 1:
            print(
                "FORECAST",
                a.start + i + 1,
                len(m["cards"]),
                row["id"],
                round(time.monotonic() - start, 2),
                flush=True,
            )
    put(
        a.repo / (f"backtesting/alpha18/forecast-batch-{a.start}-{a.stop}.json"),
        dict(
            executive_summary="New exact-safe host CLI diagnostic forecasts; no target data read.",
            input_manifest_sha256=sha(a.repo / "backtesting/alpha18/input-manifest.json"),
            executed=len(receipts),
            passed=all(x["passed"] for x in receipts),
            receipts=receipts,
            host_execution=True,
            new_Docker_execution=False,
        ),
    )


def official_score_module(a):
    name = "alpha18_official"
    spec = importlib.util.spec_from_file_location(
        name,
        a.official / "qfbench2_track_forecasting/__init__.py",
        submodule_search_locations=[str(a.official / "qfbench2_track_forecasting")],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return importlib.import_module(name + ".scoring")


def summarize(f):
    if f.empty:
        return dict(n=0)

    def avg(k):
        return float(f[k].mean())

    result = dict(
        n=len(f),
        origins=int(f["origin"].nunique()),
        assets=int(f["asset"].nunique()),
        mean_standardized_error=avg("z_error"),
        median_standardized_error=float(f["z_error"].median()),
        positive_error_fraction=avg("positive_error"),
        directional_accuracy=avg("direction"),
        mean_crps_sd=avg("crps_sd"),
        mean_tail_sd=avg("tail_sd"),
        mean_predictive_sd_over_past_scale=avg("spread_ratio"),
        rmse_standardized=float(np.sqrt((f["z_error"] ** 2).mean())),
        mean_prediction_variance_standardized=avg("pred_var"),
        coverage50=avg("coverage50"),
        coverage80=avg("coverage80"),
        coverage90=avg("coverage90"),
        coverage98=avg("coverage98"),
        below01=avg("below01"),
        above99=avg("above99"),
        quantile_hit={
            str(q): avg("hit" + str(q)) for q in (0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99)
        },
    )
    if f["asset"].nunique() == 1:
        result["raw_same_asset_units"] = dict(
            mean_error=float(f["raw_mean_error"].mean()),
            median_error=float(f["raw_median_error"].median()),
            mean_crps=float(f["raw_crps"].mean()),
            mean_tail=float(f["raw_tail"].mean()),
        )
    result["mean_input_age_business_days"] = float(f["input_age_bd"].mean())
    return result


def score(a):
    """The only stage allowed to open label-only files; no forecasting here."""
    from qfbench2_common.scoring import crps

    scoring = official_score_module(a)
    m = load(a.repo / "backtesting/alpha18/input-manifest.json")
    labels = {}
    for stem in m["label_only_sources"]:
        f = normalized_frame(a.work / ("labels-" + stem + ".parquet"))
        labels[stem] = f.pivot(index="date", columns="asset", values="value")
    cells, grids, blocked = [], [], []
    quantiles = np.array([0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99])
    for row in m["cards"]:
        unit = a.work / "inputs" / row["id"]
        folder = a.work / "forecasts" / row["id"]
        receipt = load(folder / "receipt.json")
        assert receipt["forecast_sha256"] == sha(folder / "forecast.parquet")
        fc = pd.read_parquet(folder / "forecast.parquet")
        meta = load(folder / "forecast_meta.json")
        data = pd.concat([normalized_frame(p) for p in unit.glob("*.parquet")], ignore_index=True)
        vals, truths, scales, cell_rows = [], [], [], []
        for asset in row["assets"]:
            hist = data[data["asset"] == asset].set_index("date")["value"].sort_index()
            diff = hist.diff().dropna()
            vol = max(float(diff.tail(252).std()), 1e-8)
            vol_ratio = float(diff.tail(20).std() / vol)
            input_age_bd = int(
                np.busday_count(np.datetime64(hist.index[-1]), np.datetime64(row["origin"]))
            )
            for h in HORIZONS:
                date = (pd.Timestamp(row["origin"]) + pd.offsets.BDay(h)).strftime("%Y-%m-%d")
                table = labels["rates_daily" if asset.startswith("UST_") else "g10_fx_daily"]
                if (
                    asset not in table
                    or date not in table.index
                    or not np.isfinite(table.loc[date, asset])
                ):
                    blocked.append(
                        dict(
                            id=row["id"],
                            asset=asset,
                            horizon=h,
                            reason="exact_target_quote_missing",
                        )
                    )
                    continue
                y = float(table.loc[date, asset])
                v = (
                    fc[(fc["asset"] == asset) & (fc["horizon"] == h)]
                    .sort_values("draw")["value"]
                    .to_numpy()
                )
                assert len(v) == 1000
                scale = vol * np.sqrt(h)
                q = dict(zip(quantiles, np.quantile(v, quantiles), strict=True))
                mu = float(v.mean())
                err = (y - mu) / scale
                tail = scoring.TAIL_METRICS["pinball"](
                    v[:, None], np.array([y]), (0.01, 0.05, 0.95, 0.99)
                )
                r = dict(
                    id=row["id"],
                    origin=row["origin"],
                    group=row["group"],
                    family=row["family"],
                    asset=asset,
                    horizon=h,
                    year=int(row["origin"][:4]),
                    era="<=2016"
                    if row["origin"] < "2017"
                    else "2017-2019"
                    if row["origin"] < "2020"
                    else "2020-2021"
                    if row["origin"] < "2022"
                    else "2022-2024",
                    asset_group="UST" if asset.startswith("UST_") else "G10FX",
                    text_applied=bool(meta["forecast_adjustment_applied"]),
                    input_age_bd=input_age_bd,
                    vol_state="low"
                    if vol_ratio < 0.75
                    else "high"
                    if vol_ratio > 1.25
                    else "middle",
                    raw_mean_error=y - mu,
                    raw_median_error=y - float(q[0.5]),
                    z_error=err,
                    positive_error=float(y > mu),
                    direction=float(np.sign(mu - hist.iloc[-1]) == np.sign(y - hist.iloc[-1])),
                    raw_crps=float(crps.crps_ensemble(v, y)),
                    crps_sd=float(crps.crps_ensemble(v, y) / scale),
                    raw_tail=float(tail),
                    tail_sd=float(tail / scale),
                    spread_ratio=float(v.std() / scale),
                    pred_var=float(v.var() / scale**2),
                    coverage50=float(q[0.25] <= y <= q[0.75]),
                    coverage80=float(q[0.1] <= y <= q[0.9]),
                    coverage90=float(q[0.05] <= y <= q[0.95]),
                    coverage98=float(q[0.01] <= y <= q[0.99]),
                    below01=float(y < q[0.01]),
                    above99=float(y > q[0.99]),
                    **{
                        "hit" + str(t): float(y <= q[t])
                        for t in (0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99)
                    },
                )
                cells.append(r)
                cell_rows.append(r)
                vals.append(v)
                truths.append(y)
                scales.append(scale)
        if vals:
            s = np.stack(vals, axis=1)
            y = np.array(truths)
            result = scoring._composite(
                s,
                y,
                weights=(0.5, 0.3, 0.2) if len(y) > 1 else (5 / 7, 0, 2 / 7),
                tail_levels=(0.01, 0.05, 0.95, 0.99),
                joint="variogram",
                tail_metric="pinball",
                ref_scale=None,
            )
            # Mixed raw units cannot form an interpretable aggregate.
            # Standardization is diagnostic only.
            center = s.mean(axis=0)
            z = (s - center) / np.array(scales)
            yz = (y - center) / np.array(scales)
            standardized = crps.variogram_score(z, yz, p=0.5)
            grids.append(
                dict(
                    id=row["id"],
                    origin=row["origin"],
                    group=row["group"],
                    family=row["family"],
                    cells=len(y),
                    complete=len(y) == len(row["assets"]) * 4,
                    raw_components=result,
                    standardized_variogram_per_ordered_pair=float(
                        standardized / max(len(y) * (len(y) - 1), 1)
                    ),
                )
            )
    f = pd.DataFrame(cells)
    f.to_parquet(a.work / "individual-diagnostics.parquet", index=False)
    put(a.work / "grid-diagnostics.json", grids)
    put(a.work / "blocked-cells.json", blocked)
    out = dict(
        executive_summary=(
            "Exact-safe CLI short-horizon diagnostics on expose"
            "d history; no alpha experiment yet."
        ),
        status="DIAGNOSTICS_EXECUTED",
        contamination="EXPLORATORY_EXPOSED_HISTORY",
        independent_alpha_verified="UNKNOWN",
        official_M0_normalization=False,
        official_composite=None,
        score_definition=(
            "Imported official fair ensemble CRPS, variogram p="
            ".5, tail pinball .01/.05/.95/.99. SD diagnostics d"
            "ivide by pre-asof 252-observation daily SD*sqrt(h)"
            ", not M0. Raw composites stay private because unit"
            "s differ; no cross-unit official score."
        ),
        requested_forecasts=len(m["cards"]),
        forecasts_completed=len(grids),
        cells=len(cells),
        blocked_cells=len(blocked),
        distinct_origins=int(f["origin"].nunique()),
        dates=[str(f["origin"].min()), str(f["origin"].max())],
        overall=summarize(f),
        partitions={},
    )
    for col in [
        "group",
        "asset_group",
        "asset",
        "horizon",
        "family",
        "year",
        "era",
        "vol_state",
        "text_applied",
        "input_age_bd",
    ]:
        out["partitions"][col] = {str(k): summarize(v) for k, v in f.groupby(col, sort=True)}
    out["group_horizon"] = {
        g: {str(h): summarize(vv) for h, vv in v.groupby("horizon")} for g, v in f.groupby("group")
    }
    out["group_asset"] = {
        g: {str(h): summarize(vv) for h, vv in v.groupby("asset")} for g, v in f.groupby("group")
    }
    out["group_era"] = {
        g: {str(h): summarize(vv) for h, vv in v.groupby("era")} for g, v in f.groupby("group")
    }
    out["unit_grid_sizes"] = (
        pd.Series([v["cells"] for v in grids]).value_counts().sort_index().to_dict()
    )
    out["single_cell_diagnostic"] = dict(
        n=len(f),
        note=(
            "Each marginal is evaluated separately; the project"
            "ed full grids all have4+horizon cells. No actual o"
            "ne-cell authored card performance is claimed."
        ),
    )
    out["joint_diagnostic"] = {
        g: dict(
            n=len(v),
            mean_sd_variogram_per_pair=float(
                np.mean([r["standardized_variogram_per_ordered_pair"] for r in v])
            ),
        )
        for g in sorted({r["group"] for r in grids})
        if (v := [r for r in grids if r["group"] == g])
    }
    out["private_evidence_hashes"] = {
        p.name: sha(p)
        for p in [
            a.work / "individual-diagnostics.parquet",
            a.work / "grid-diagnostics.json",
            a.work / "blocked-cells.json",
        ]
    }
    put(a.repo / "ALPHA18-SHORT-HORIZON-DIAGNOSTICS.json", out)
    print(
        json.dumps(
            {
                k: out[k]
                for k in [
                    "status",
                    "requested_forecasts",
                    "forecasts_completed",
                    "cells",
                    "blocked_cells",
                    "distinct_origins",
                    "dates",
                    "overall",
                ]
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    a = args()
    a.repo, a.baseline, a.official, a.work = (
        x.resolve() for x in (a.repo, a.baseline, a.official, a.work)
    )
    a.work.mkdir(parents=True, exist_ok=True)
    {"prepare": prepare, "bridge": bridge, "forecast": forecast, "score": score}[a.stage](a)

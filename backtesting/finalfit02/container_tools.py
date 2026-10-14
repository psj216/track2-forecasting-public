"""## Executive summary (read this first)
Prepare synthetic contract inputs and inspect outputs; never score or supply answers.
Executed in the exact safe image for fixture generation, and with current official
validator sources mounted for validation. Monthly mappings are task inputs, not truth.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import tomllib
import uuid

import numpy as np
import pandas as pd


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_toml(value, path):
    lines = ["# Executive summary: synthetic contract fixture, not a ranked card or market forecast."]

    def visit(obj, prefix):
        if prefix:
            lines.append("[" + ".".join(prefix) + "]")
        for key, v in obj.items():
            if not isinstance(v, dict):
                lines.append(key + " = " + json.dumps(v, ensure_ascii=True))
        lines.append("")
        for key, v in obj.items():
            if isinstance(v, dict):
                visit(v, prefix + [key])

    visit(value, [])
    path.write_text("\n".join(lines))


def prepare(root):
    official = pathlib.Path("/official")
    definitions = [
        ("f1-ust", "t2-F1-ust-positioning-2018", ["UST_10Y"], "daily", "percent_per_annum"),
        ("f2-eur", "t2-F2-draghi-precommit-2014", ["EUR"], "daily", "usd_per_eur"),
        ("f3-ust", "t2-F3-sep-dots-curve-2023", ["UST_2Y", "UST_5Y", "UST_10Y", "UST_30Y"], "daily", "percent_per_annum"),
        ("f4-jpy", "t2-F4-jpy-carry-2007", ["JPY"], "daily", "jpy_per_usd"),
        ("f3-em", "t2-F3-em-transfer-joint-2013", ["INR", "BRL"], "daily", "inr_per_usd; brl_per_usd"),
        ("monthly-a", "t2-F1-cpi-glidepath-2023", ["CPI_ALL"], "monthly", "index"),
        ("monthly-b", "t2-F1-cpi-glidepath-2023", ["CPI_ALL"], "monthly", "index"),
        ("monthly-missing", "t2-F1-cpi-glidepath-2023", ["CPI_ALL"], "monthly", "index"),
        ("monthly-conflict", "t2-F1-cpi-glidepath-2023", ["CPI_ALL"], "monthly", "index"),
        ("missing-history", "t2-F1-ust-positioning-2018", ["UST_10Y"], "daily", "percent_per_annum"),
        ("future-sentinel", "t2-F1-ust-positioning-2018", ["UST_10Y"], "daily", "percent_per_annum"),
    ]
    manifest = []
    for name, source, assets, frequency, unit in definitions:
        dest = root / "inputs" / name
        dest.mkdir(parents=True)
        card = tomllib.loads((official / "units" / source / "card.toml").read_text())
        asof = "2018-09-14"
        card["task"].update(id="fit02-" + name, title="Synthetic contract test " + name, split="validation")
        card["metadata"].update(description="SYNTHETIC_CONTRACT_TEST; no market outcomes", horizons=[1, 2, 3, 4], n_assets=len(assets), target_frequency=frequency)
        card["provenance"].update(data_cutoff=asof, data_source="Deterministic synthetic inputs; no actual market observations", license="MIT")
        card["contamination"]["canary_guid"] = str(uuid.uuid4())
        unit = card["targets"].get("value_unit", unit)
        card["targets"] = dict(asset_ids=assets, horizons=[1, 2, 3, 4], target_type="level", target_frequency=frequency, value_unit=unit, leakage_checked=True)
        card["panels"] = {"panel_ids": ["synthetic_history"], "synthetic_history": {"frequency": "monthly" if frequency == "monthly" else "business_daily", "asset_ids": assets, "source": "synthetic"}}
        card["text"] = dict(source="synthetic", path="text/", cutoff=asof, cutoff_checked=True, n_documents=1, doc_types=["cb_speech"])
        minimum = 1000 if card["metadata"]["category"] == "T2-F4" else 500
        card["scoring"]["params"]["n_draws_min"] = minimum
        card["environment"] = dict(cpus=2, memory="4G", gpu=False, network="restricted")
        spec = dict(schema_version="2", card_id=card["task"]["id"], track="forecasting", card_family=card["metadata"]["category"], targets=dict(card["targets"]), output_format="samples", n_draws_min=minimum)
        if frequency == "monthly":
            periods = ["2018-09", "2018-10", "2018-11", "2018-12"]
            if name == "monthly-b":
                periods = ["2018-10", "2018-11", "2018-12", "2019-01"]
            if name != "monthly-missing":
                spec["targets"]["observation_periods"] = periods
            if name == "monthly-conflict":
                card["targets"]["observation_periods"] = ["2018-10", "2018-11", "2018-12", "2019-01"]
        write_toml(card, dest / "card.toml")
        (dest / "forecast_spec.json").write_text(json.dumps(spec, indent=2))
        text = dest / "text"
        text.mkdir()
        (text / "doc.txt").write_text("Executive summary: synthetic neutral dated information. No policy or market forecast is supplied.\n")
        (text / "corpus_index.json").write_text(json.dumps(dict(card_id=card["task"]["id"], asof=asof, documents=[dict(doc_id="synthetic-neutral", timestamp=asof, source="synthetic", doc_type="cb_speech", file="doc.txt")])))
        dates = pd.date_range("2013-01-01", "2018-08-01", freq="MS") if frequency == "monthly" else pd.bdate_range(end=asof, periods=300)
        rows = []
        anchors = {"EUR": 1.2, "JPY": 110., "INR": 65., "BRL": 3., "CPI_ALL": 250.}
        for ai, asset in enumerate(assets):
            anchor = anchors.get(asset, 2. + ai * .3)
            size = .001 if asset == "EUR" else .04 if asset.startswith("UST") else .08 if asset in {"JPY", "INR"} else .01 if asset == "BRL" else .35
            values = anchor + np.cumsum(size * (np.sin(np.arange(len(dates)) * .43 + ai) + .3 * np.cos(np.arange(len(dates)) * .17)))
            rows.extend(dict(date=str(date)[:10], asset=asset, value=float(value)) for date, value in zip(dates, values, strict=True))
        frame = pd.DataFrame(rows)
        if name == "missing-history":
            frame = frame.iloc[:2]
        if name == "future-sentinel":
            frame = pd.concat([frame, pd.DataFrame([dict(date="2018-09-17", asset="UST_10Y", value=999999.)])], ignore_index=True)
        frame.to_parquet(dest / "synthetic_history.parquet", index=False)
        manifest.append(dict(name=name, input_kind="SYNTHETIC_CONTRACT_TEST", source_card=source, family=card["metadata"]["category"], asof=asof, assets=assets, horizons=[1, 2, 3, 4], frequency=frequency, units=unit, n_draws=minimum, expected_failure=name in {"missing-history", "monthly-missing", "monthly-conflict"}, post_cutoff_sentinel=name == "future-sentinel", files={str(p.relative_to(dest)): sha(p) for p in dest.rglob("*") if p.is_file()}))
    (root / "synthetic-input-manifest.json").write_text(json.dumps(manifest, indent=2))


def validate(out, unit):
    import jsonschema
    from qfbench2_common.taskcard import load_schema
    from qfbench2_track_forecasting.grid import grid_from_card, check_declared_grid, build_sample_matrix
    from qfbench2_track_forecasting.limits import DEFAULT_LIMITS, inspect_parquet
    from qfbench2_track_forecasting.cutoff import bind_metadata, scan_text_corpus_cutoff
    from qfbench2_track_forecasting.horizons import monthly_horizon_steps

    card = tomllib.loads((unit / "card.toml").read_text())
    meta = json.loads((out / "forecast_meta.json").read_text())
    jsonschema.validate(meta, load_schema("forecast.schema.json"))
    jsonschema.validate(card, load_schema("taskcard.schema.json"))
    grid = grid_from_card(card)
    check_declared_grid(meta, grid)
    bind_metadata(meta, card, unit_handle=unit.name)
    facts = inspect_parquet(out / "forecast.parquet", what="forecast.parquet", limits=DEFAULT_LIMITS)
    matrix = build_sample_matrix(out / "forecast.parquet", facts, grid, meta["n_draws"], limits=DEFAULT_LIMITS)
    assert np.isfinite(matrix).all()
    assert meta["forecast_mode"] == "text-first-v5.1"
    assert meta["n_draws"] >= card["scoring"]["params"]["n_draws_min"]
    assert (out / "forecast_rationale.md").stat().st_size > 0
    assert sum(p.stat().st_size for p in out.iterdir() if p.is_file()) < 64 * 1024**2
    scan_text_corpus_cutoff(unit / "text", meta["asof"])
    hashes = {p.name: sha(p) for p in out.iterdir() if p.is_file()}
    monthly = None
    latest = {}
    for path in unit.glob("*.parquet"):
        df = pd.read_parquet(path)
        if "date" not in df:
            continue
        date = df["date"].astype(str).str[:10]
        if unit.name != "future-sentinel":
            assert date.max() <= meta["asof"]
        col = "asset" if "asset" in df else "asset_id"
        for asset in grid.assets:
            subset = df[(df[col] == asset) & (date <= meta["asof"])]
            if len(subset):
                latest[asset] = str(subset["date"].max())[:10]
    if card["targets"].get("target_frequency") == "monthly":
        spec = json.loads((unit / "forecast_spec.json").read_text()) if (unit / "forecast_spec.json").is_file() else None
        monthly = monthly_horizon_steps(list(grid.assets), list(grid.horizons), latest, asof=meta["asof"], card=card, forecast_spec=spec).tolist()
    values = pd.read_parquet(out / "forecast.parquet")
    statistics = values.groupby(["asset", "horizon"])["value"].agg(["mean", "std", "min", "max"]).reset_index().to_dict("records")
    print(json.dumps(dict(valid=True, hashes=hashes, n_draws=meta["n_draws"], shape=list(matrix.shape), statistics=statistics, assets=list(grid.assets), horizons=list(grid.horizons), expected_monthly_steps=monthly, latest_input_dates=latest, adjustment_applied=meta["forecast_adjustment_applied"], fallback=meta["rationale"]["text_evidence"], cutoff_pass=True, current_schema_pass=True)))


if __name__ == "__main__":
    if sys.argv[1] == "prepare":
        prepare(pathlib.Path(sys.argv[2]))
    else:
        validate(pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]))

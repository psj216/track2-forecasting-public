"""## Executive summary (read this first)

One preregistered FOMC-calendar variance experiment. Import the unchanged safe
CLI and official scorer; never rewrite forecasting or scoring math. Raw inputs,
draws, targets and per-origin results remain outside the public repository.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib
import io
import json
import os
import sys
import types
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")


def event_counts(origin, horizons, events, shift=0):
    start = datetime.fromisoformat(origin + "T17:00:00").replace(
        tzinfo=ZoneInfo("America/New_York")
    )
    counts = []
    for h in horizons:
        end = (
            (pd.Timestamp(origin) + pd.offsets.BDay(h))
            .to_pydatetime()
            .replace(hour=17, tzinfo=ZoneInfo("America/New_York"))
        )
        n = 0
        for event in events:
            available = datetime.fromisoformat(event["available_at"])
            date = pd.Timestamp(event["scheduled_date"]) + pd.Timedelta(days=shift)
            instant = date.to_pydatetime().replace(hour=14, tzinfo=ZoneInfo("America/New_York"))
            n += int(available <= start and start < instant <= end)
        counts.append(n)
    return np.asarray(counts, dtype=float)


def adjust(samples, counts, horizons, beta):
    out = samples.copy()
    for i, (n, h) in enumerate(zip(counts, horizons, strict=True)):
        if n == 0 or beta == 0:
            continue
        center = samples[:, :, i].mean(axis=0)
        out[:, :, i] = center + np.sqrt(1 + beta * n / h) * (samples[:, :, i] - center)
    return out


def generate(a, lock, cli):
    origins = lock["training_origins"] + lock["evaluation_origins"]
    horizons = lock["primary_horizons_BD"] + lock["secondary_horizons_BD"]
    assets = lock["assets"]
    for j, origin in enumerate(origins[a.start : a.stop]):
        for lag in [0, 1] if origin in lock["evaluation_origins"] else [0]:
            folder = a.work / "private/forecasts" / f"{origin}-lag{lag}"
            array_file = folder / "samples.npy"
            if array_file.exists():
                continue
            folder.mkdir(parents=True, exist_ok=True)
            panels = folder / "panels"
            panels.mkdir(exist_ok=True)
            text = folder / "text"
            text.mkdir(exist_ok=True)
            (text / "corpus_index.json").write_text('{"documents":[]}\n')
            vintage = (pd.Timestamp(origin) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
            raw_path = a.work / "private/vintages" / f"{origin}.csv"
            receipt = json.loads(raw_path.with_suffix(".receipt.json").read_text())
            assert sha(raw_path) == receipt["sha256"]
            frame = pd.read_csv(raw_path)
            assert list(frame.columns) == ["observation_date"] + [
                f'{s}_{vintage.replace("-", "")}' for s in ["DGS2", "DGS5", "DGS10"]
            ]
            frame["date"] = pd.to_datetime(frame["observation_date"])
            cutoff = pd.Timestamp(origin) - pd.offsets.BDay(1 + lag)
            frame = frame.loc[(frame["date"] >= "2000-01-01") & (frame["date"] <= cutoff)]
            long = []
            for series, asset in zip(["DGS2", "DGS5", "DGS10"], assets, strict=True):
                column = series + "_" + vintage.replace("-", "")
                f = frame[["date", column]].rename(columns={column: "value"}).dropna()
                f["date"] = f["date"].dt.strftime("%Y-%m-%d")
                f["asset"] = asset
                f["panel_id"] = "rates_daily"
                long.append(f)
            pd.concat(long, ignore_index=True).to_parquet(
                panels / "rates_daily.parquet", index=False
            )
            card = folder / "card.toml"
            card.write_text(
                '[task]\nid="R17-controlled-' + origin + '"\n'
                '[metadata]\ncategory="T2-F3"\n[targets]\nasset_ids=' + json.dumps(assets) + "\n"
                "horizons="
                + json.dumps(horizons)
                + '\ntarget_type="level"\ntarget_frequency="daily"\n'
                'value_unit="percent"\n[scoring.params]\nn_draws_min=1000\n'
            )
            argv = [
                "--panels",
                str(panels),
                "--text",
                str(text),
                "--asof",
                origin,
                "--card",
                str(card),
                "--n-draws",
                "1000",
                "--seed",
                "0",
                "--out",
                str(folder / "forecast.parquet"),
            ]
            with contextlib.redirect_stdout(io.StringIO()):
                assert cli.main(argv) == 0
            output = pd.read_parquet(folder / "forecast.parquet")
            values = output["value"].to_numpy(dtype=np.float64).reshape(1000, 3, 6)
            assert np.isfinite(values).all()
            meta = json.loads((folder / "forecast_meta.json").read_text())
            assert meta["forecast_mode"] == "text-first-v5.1"
            assert meta["forecast_adjustment_applied"] is False
            assert meta["reasoning_skipped_reason"] == "family_frozen"
            np.save(array_file, values)
            write(
                folder / "input-receipt.json",
                {
                    "origin": origin,
                    "lag": lag,
                    "vintage": vintage,
                    "input_last_date": max(f["date"].max() for f in long),
                    "input_observation_cutoff": cutoff.strftime("%Y-%m-%d"),
                    "raw_sha256": sha(raw_path),
                    "panel_sha256": sha(panels / "rates_daily.parquet"),
                    "card_sha256": sha(card),
                    "forecast_sha256": sha(folder / "forecast.parquet"),
                    "sample_sha256": sha(array_file),
                    "shape": list(values.shape),
                    "command": argv,
                    "strictly_before_origin": True,
                    "metadata": {
                        "mode": meta["forecast_mode"],
                        "adjustment": meta["forecast_adjustment_applied"],
                        "reason": meta["reasoning_skipped_reason"],
                    },
                },
            )
            if origin == lock["evaluation_origins"][0] and lag == 0:
                first = (folder / "forecast.parquet").read_bytes()
                with contextlib.redirect_stdout(io.StringIO()):
                    assert cli.main(argv) == 0
                assert (folder / "forecast.parquet").read_bytes() == first
        if j % 8 == 0 or j == len(origins[a.start : a.stop]) - 1:
            print(
                json.dumps({"stage": "FORECAST_GENERATE", "batch_origin": j + 1, "origin": origin}),
                flush=True,
            )


def outcome(frame, origin, horizons, assets):
    dates = [(pd.Timestamp(origin) + pd.offsets.BDay(h)).strftime("%Y-%m-%d") for h in horizons]
    return frame.reindex(dates)[assets].to_numpy(dtype=float).T, dates


def score(scoring, samples, y, scales=None, single=False):
    return scoring._composite(
        samples.reshape(len(samples), -1),
        y.reshape(-1),
        weights=(5 / 7, 0, 2 / 7) if single else (0.5, 0.3, 0.2),
        tail_levels=(0.01, 0.05, 0.95, 0.99),
        joint="variogram",
        tail_metric="pinball",
        ref_scale=scales,
    )


def load_targets(a, lock):
    path = a.repo / lock["target_source"]["path"]
    assert sha(path) == lock["target_source"]["sha256"]
    f = pd.read_parquet(path).pivot(index="date", columns="asset", values="value")
    f.index = pd.to_datetime(f.index).strftime("%Y-%m-%d")
    return f


def train(a, lock, events, scoring):
    assert json.loads((a.work / "bridge-receipt.json").read_text())["passed"]
    frame = load_targets(a, lock)
    numerator = 0.0
    denominator = 0.0
    rows = []
    blocked = []
    secondary = []
    event_origins = 0
    for origin in lock["training_origins"]:
        samples = np.load(a.work / "private/forecasts" / f"{origin}-lag0/samples.npy")
        y, dates = outcome(frame, origin, [1, 2, 4], lock["assets"])
        if max(dates) > lock["training_cutoff"] or not np.isfinite(y).all():
            blocked.append(origin)
            continue
        n = event_counts(origin, [1, 2, 4], events)
        x = np.broadcast_to(n / np.array([1, 2, 4]), (3, 3))
        p = samples[:, :, :3]
        v = p.var(axis=0)
        mu = p.mean(axis=0)
        assert (v > 0).all()
        numerator += float(np.sum(x * ((y - mu) ** 2 / v - 1)))
        denominator += float(np.sum(x * x))
        event_origins += int(n.any())
        rows.append(score(scoring, p, y))
        sy, sd = outcome(frame, origin, [5, 10, 12], lock["assets"])
        if max(sd) <= lock["training_cutoff"] and np.isfinite(sy).all():
            secondary.append(score(scoring, samples[:, :, 3:], sy))
    assert denominator > 0
    scales = {k: float(np.mean([r[k] for r in rows])) for k in ["marginal", "joint", "tail"]}
    scales_secondary = {k: float(np.mean([r[k] for r in secondary])) for k in scales}
    fitted = {
        "executive_summary": "Single frozen-rule coefficient fit on matured2022-23 primary data; no2024 outcomes used.",
        "beta": float(np.clip(numerator / denominator, 0, 4)),
        "unclipped_beta": numerator / denominator,
        "training_origins_used": len(rows),
        "training_origins_blocked": len(blocked),
        "training_event_origins": event_origins,
        "fit_denominator": denominator,
        "primary_training_scales": scales,
        "secondary_training_scales": scales_secondary,
        "secondary_training_origins": len(secondary),
        "official_M0_normalization": False,
        "lock_sha256": sha(a.repo / "R17-LOCKED-HYPOTHESIS.json"),
    }
    write(a.work / "fitted.json", fitted)
    print(json.dumps(fitted), flush=True)


def evaluate(a, lock, events, scoring):
    fitted = json.loads((a.work / "fitted.json").read_text())
    beta = fitted["beta"]
    frame = load_targets(a, lock)
    rows = []
    blocked = []
    secondary = []
    cells = []
    audits = []
    for origin in lock["evaluation_origins"]:
        base = np.load(a.work / "private/forecasts" / f"{origin}-lag0/samples.npy")
        lagbase = np.load(a.work / "private/forecasts" / f"{origin}-lag1/samples.npy")
        counts = event_counts(origin, [1, 2, 4, 5, 10, 12], events)
        cand = adjust(base, counts, [1, 2, 4, 5, 10, 12], beta)
        placebo = adjust(
            base, event_counts(origin, [1, 2, 4, 5, 10, 12], events, 7), [1, 2, 4, 5, 10, 12], beta
        )
        lagcand = adjust(lagbase, counts, [1, 2, 4, 5, 10, 12], beta)
        assert cand.shape == base.shape and np.isfinite(cand).all()
        assert np.allclose(cand.mean(axis=0), base.mean(axis=0), rtol=0, atol=1e-12)
        assert np.array_equal(cand, adjust(base, counts, [1, 2, 4, 5, 10, 12], beta))
        for hi, n in enumerate(counts):
            if n == 0:
                assert np.array_equal(cand[:, :, hi], base[:, :, hi])
        quarter = origin[:4] + "Q" + str((int(origin[5:7]) - 1) // 3 + 1)
        y, dates = outcome(frame, origin, [1, 2, 4], lock["assets"])
        if np.isfinite(y).all():
            scale = fitted["primary_training_scales"]
            row = {
                "origin": origin,
                "quarter": quarter,
                "event_exposed": bool(counts[:3].any()),
                "base": score(scoring, base[:, :, :3], y, scale),
                "candidate": score(scoring, cand[:, :, :3], y, scale),
                "placebo": score(scoring, placebo[:, :, :3], y, scale),
                "lag_base": score(scoring, lagbase[:, :, :3], y, scale),
                "lag_candidate": score(scoring, lagcand[:, :, :3], y, scale),
            }
            rows.append(row)
            for ai, asset in enumerate(lock["assets"]):
                for hi, h in enumerate([1, 2, 4]):
                    cells.append(
                        {
                            "origin": origin,
                            "asset": asset,
                            "horizon": h,
                            "base": score(
                                scoring,
                                base[:, ai : ai + 1, hi : hi + 1],
                                y[ai : ai + 1, hi : hi + 1],
                                scale,
                                True,
                            ),
                            "candidate": score(
                                scoring,
                                cand[:, ai : ai + 1, hi : hi + 1],
                                y[ai : ai + 1, hi : hi + 1],
                                scale,
                                True,
                            ),
                        }
                    )
        else:
            blocked.append(
                {"origin": origin, "reason": "missing_primary_target_quote", "target_dates": dates}
            )
        sy, sd = outcome(frame, origin, [5, 10, 12], lock["assets"])
        if np.isfinite(sy).all():
            scale = fitted["secondary_training_scales"]
            secondary.append(
                {
                    "origin": origin,
                    "base": score(scoring, base[:, :, 3:], sy, scale),
                    "candidate": score(scoring, cand[:, :, 3:], sy, scale),
                }
            )
        audits.append(
            {
                "origin": origin,
                "counts": counts.tolist(),
                "shape": list(base.shape),
                "max_mean_difference": float(np.max(np.abs(cand.mean(0) - base.mean(0)))),
                "max_sd_ratio": float(np.max(cand.std(0) / base.std(0))),
                "extra_lag_changes_baseline": not np.array_equal(base, lagbase),
                "zero_event_exact": True,
                "repeat_exact": True,
            }
        )
    write(
        a.work / "private/evaluation.json",
        {
            "rows": rows,
            "cells": cells,
            "secondary": secondary,
            "blocked": blocked,
            "audits": audits,
        },
    )
    print(
        json.dumps(
            {
                "primary_complete_origins": len(rows),
                "blocked": len(blocked),
                "primary_event_exposed_origins": sum(r["event_exposed"] for r in rows),
                "secondary_complete_origins": len(secondary),
                "single_cells": len(cells),
            }
        ),
        flush=True,
    )


def summarize(a, lock):
    d = json.loads((a.work / "private/evaluation.json").read_text())
    rows = d["rows"]

    def summary(rs, left="candidate", right="base"):
        if not rs:
            return {"n": 0, "ratio": None}
        result = {"n": len(rs)}
        for k in ["marginal", "joint", "tail", "composite"]:
            b = float(np.mean([r[right][k] for r in rs]))
            c = float(np.mean([r[left][k] for r in rs]))
            result[k] = {"baseline_mean": b, "candidate_mean": c, "ratio": c / b if b > 0 else None}
        return result

    rng = np.random.default_rng(17017)
    bs = []
    n = len(rows)
    for _ in range(1000):
        starts = rng.integers(0, n, size=(n + 3) // 4)
        idx = np.concatenate([(np.arange(s, s + 4) % n) for s in starts])[:n]
        subset = [rows[i] for i in idx]
        bs.append(summary(subset)["composite"]["ratio"])
    quarters = sorted({r["quarter"] for r in rows})
    leave = {q: summary([r for r in rows if r["quarter"] != q]) for q in quarters}
    gain = np.array([r["base"]["composite"] - r["candidate"]["composite"] for r in rows])
    removed = summary([r for i, r in enumerate(rows) if i != int(np.argmax(gain))])
    per_asset = {
        asset: summary([r for r in d["cells"] if r["asset"] == asset]) for asset in lock["assets"]
    }
    primary = summary(rows)
    ci = np.quantile(bs, [0.025, 0.975]).tolist()
    checks = {
        "enough_origins": n >= 30,
        "enough_event_origins": sum(r["event_exposed"] for r in rows) >= 5,
        "primary_2pct_gain": primary["composite"]["ratio"] <= 0.98,
        "bootstrap_upper_below_one": ci[1] < 1,
        "joint_not_worse_5pct": primary["joint"]["ratio"] <= 1.05,
        "tail_not_worse_5pct": primary["tail"]["ratio"] <= 1.05,
        "two_assets_improve": sum(v["marginal"]["ratio"] < 1 for v in per_asset.values()) >= 2,
        "leave_quarter_out_robust": all(x["composite"]["ratio"] < 1 for x in leave.values()),
        "remove_largest_gain_robust": removed["composite"]["ratio"] < 1,
    }
    result = {
        "executive_summary": "Single locked exposed-history calendar variance experiment; paired exact-source baseline and original metric functions. No official loss or independent alpha.",
        "protocol": lock["protocol"],
        "classification": "EXPLORATORY_SIGNAL_ONLY"
        if all(checks.values())
        else "NO_PREDICTABLE_SIGNAL",
        "contamination_status": "EXPLORATORY_EXPOSED_HISTORY",
        "independent_alpha_verified": "UNKNOWN",
        "official_M0_score": "NOT_COMPUTED",
        "fit": json.loads((a.work / "fitted.json").read_text()),
        "primary": primary,
        "primary_composite_ratio_ci95_block4": ci,
        "primary_event_exposed": summary([r for r in rows if r["event_exposed"]]),
        "primary_no_event": summary([r for r in rows if not r["event_exposed"]]),
        "primary_single_cells": summary(d["cells"]),
        "per_asset": per_asset,
        "per_horizon": {
            str(h): summary([r for r in d["cells"] if r["horizon"] == h]) for h in [1, 2, 4]
        },
        "per_quarter": {q: summary([r for r in rows if r["quarter"] == q]) for q in quarters},
        "secondary": summary(d["secondary"]),
        "lag_control": summary(rows, "lag_candidate", "lag_base"),
        "placebo_calendar": summary(rows, "placebo", "base"),
        "leave_one_quarter_out": leave,
        "remove_largest_gain_origin": removed,
        "primary_missing_quote_origins": len(d["blocked"]),
        "execution_controls": {
            "all_finite_shapes": True,
            "zero_event_exact": True,
            "location_preserved": True,
            "deterministic_repeat": True,
            "max_mean_difference": max(x["max_mean_difference"] for x in d["audits"]),
            "max_sd_ratio": max(x["max_sd_ratio"] for x in d["audits"]),
            "extra_lag_changes_baseline_origins": sum(
                x["extra_lag_changes_baseline"] for x in d["audits"]
            ),
        },
        "acceptance_checks": checks,
        "performance_gate_pass": all(checks.values()),
        "Final_eligible": False,
        "source_bridge": json.loads((a.work / "bridge-receipt.json").read_text()),
        "private_evaluation_sha256": sha(a.work / "private/evaluation.json"),
        "limits": [
            "UST-only controlled F3 route; no full text-corpus quality proof",
            "2022-24 exposed history and one2024 fold",
            "No live House, FX performance, extra Final assets or Final target evaluation",
            "Training-error normalization is not official expected-error M0 normalization",
        ],
    }
    write(a.repo / "R17-FEASIBILITY-RESULT.json", result)
    print(
        json.dumps(
            {
                "classification": result["classification"],
                "primary_ratio": primary["composite"]["ratio"],
                "CI95": ci,
                "acceptance_checks": checks,
            }
        ),
        flush=True,
    )


def main():
    p = argparse.ArgumentParser()
    for name in ["repo", "safe-source", "official", "work"]:
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--stage", choices=["generate", "train", "evaluate", "summarize"], required=True)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--stop", type=int, default=154)
    a = p.parse_args()
    lock = json.loads((a.repo / "R17-LOCKED-HYPOTHESIS.json").read_text())
    events = json.loads((a.repo / "backtesting/research17/frozen_calendar.json").read_text())[
        "events"
    ]
    os.environ.update(FORECAST_MODE="text-first-v5.1", NUMERIC_VARIANT="v3", TEXT_INTEGRATION="on")
    sys.path.insert(0, str(a.safe_source.resolve()))
    cli = importlib.import_module("qfbench2_track_forecasting.cli")
    assert Path(cli.__file__).is_relative_to(a.safe_source.resolve())
    package = types.ModuleType("r17_official")
    package.__path__ = [str((a.official / "qfbench2_track_forecasting").resolve())]
    sys.modules["r17_official"] = package
    scoring = importlib.import_module("r17_official.scoring")
    assert (
        sha(a.official / "qfbench2_track_forecasting/scoring.py")
        == "cbb541ef25665b401b1891e67d0bb300aef0014919e900a500e6f9128546c031"
    )
    if a.stage == "generate":
        generate(a, lock, cli)
    elif a.stage == "train":
        train(a, lock, events, scoring)
    elif a.stage == "evaluate":
        evaluate(a, lock, events, scoring)
    else:
        summarize(a, lock)


if __name__ == "__main__":
    main()

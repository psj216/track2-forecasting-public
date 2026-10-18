"""## Executive summary (read this first)
Execute the locked parameter-free observation-clock hypothesis with unchanged safe CLI code.
Generation never reads target tables. Evaluation imports official score math and is exposed research.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import pathlib
import re
import time

import numpy as np
import pandas as pd
from diagnostic import baseline_cli, load, normalized_frame, official_score_module, put, sha

ASSETS = ["UST_2Y", "UST_5Y", "UST_10Y"]
H = [1, 2, 3, 4]
COMPONENTS = ["marginal", "joint", "tail"]
WEIGHTS = np.array([0.5, 0.3, 0.2])


def observation_gap(frame, origin):
    """Refuse future or heterogeneous anchors; never infer a missing asset date."""
    last = frame.groupby("asset").date.max()
    if set(last.index) != set(ASSETS) or last.nunique() != 1 or last.iloc[0] > origin:
        raise ValueError("Require three complete, common, nonfuture UST anchor dates.")
    return int(np.busday_count(np.datetime64(last.iloc[0]), np.datetime64(origin)))


def matrix(path, keys):
    f = pd.read_parquet(path)
    return np.stack(
        [
            np.stack(
                [
                    f[(f.asset == asset) & (f.horizon == h)].sort_values("draw").value.to_numpy()
                    for h in keys
                ],
                axis=1,
            )
            for asset in ASSETS
        ],
        axis=1,
    )


def generate(a):
    lock = load(a.repo / "ALPHA18-LOCKED-HYPOTHESIS.json")
    manifest = load(a.repo / "backtesting/alpha18/input-manifest.json")
    assert sha(a.repo / "backtesting/alpha18/input-manifest.json") == lock["input_manifest_sha256"]
    assert load(a.repo / "ALPHA18-BASELINE-IDENTITY.json")["passed"]
    rows = [r for r in manifest["cards"] if r["group"] == "past_vintage_UST"]
    gaps = []
    for r in rows:
        f = normalized_frame(a.work / "inputs" / r["id"] / "rates_daily.parquet")
        gaps.append(observation_gap(f, r["origin"]))
    placebo = np.random.default_rng(18019).permutation(gaps)
    cli = baseline_cli(a)
    output = a.work / "experiment"
    receipts = []
    started = time.monotonic()
    for pos in range(a.start, min(a.stop, len(rows))):
        row = rows[pos]
        origin = row["origin"]
        original_input = a.work / "inputs" / row["id"]
        assert (
            sha(original_input / "rates_daily.parquet")
            == row["input_files"]["rates_daily.parquet"]["input_sha256"]
        )
        frame = normalized_frame(original_input / "rates_daily.parquet")
        folder = output / origin
        if (folder / "receipt.json").exists() and load(folder / "receipt.json")["passed"]:
            receipts.append(load(folder / "receipt.json"))
            continue
        record = dict(
            origin=origin,
            actual_gap=gaps[pos],
            placebo_gap=int(placebo[pos]),
            runs=[],
            passed=False,
        )

        def run(name, panel, steps):
            work = folder / name
            inp = work / "input"
            (inp / "text").mkdir(parents=True, exist_ok=True)
            panel.to_parquet(inp / "rates_daily.parquet", index=False)
            content = (original_input / "card.toml").read_text()
            content = re.sub(
                r"(?m)^horizons\s*=\s*\[[^\n]*\]", "horizons=" + json.dumps(steps), content
            )
            (inp / "card.toml").write_text(content)
            path = work / "raw-kernel" / "forecast.parquet"
            argv = [
                "--panels",
                str(inp),
                "--text",
                str(inp / "text"),
                "--asof",
                origin,
                "--out",
                str(path),
                "--n-draws",
                "1000",
                "--seed",
                "0",
            ]
            with contextlib.redirect_stdout(io.StringIO()) as log:
                assert cli.main(argv) == 0
            (work / "forecast.log").write_text(log.getvalue())
            samples = matrix(path, steps)
            assert samples.shape == (1000, 3, 4) and np.isfinite(samples).all()
            np.save(work / "samples.npy", samples)
            record["runs"].append(
                dict(
                    name=name,
                    command=argv,
                    steps=steps,
                    requested_keys=H,
                    input_sha256=sha(inp / "rates_daily.parquet"),
                    raw_kernel_parquet_sha256=sha(path),
                    sample_sha256=sha(work / "samples.npy"),
                )
            )
            return samples

        candidate = run("candidate", frame, [gaps[pos] + h for h in H])
        if int(placebo[pos]) != gaps[pos]:
            run("placebo", frame, [int(placebo[pos]) + h for h in H])
        else:
            record["placebo_reuses_candidate_exactly"] = True
        last = frame.date.max()
        lagged = frame[frame.date < last].copy()
        laggap = observation_gap(lagged, origin)
        record["lag_gap"] = laggap
        record["lag_dropped_observation_date"] = last
        run("lag_baseline", lagged, H)
        run("lag_candidate", lagged, [laggap + h for h in H])
        if pos == 0:
            repeated = run("candidate_repeat", frame, [gaps[pos] + h for h in H])
            assert np.array_equal(repeated, candidate)
            record["repeat_exact"] = True
        record["passed"] = True
        put(folder / "receipt.json", record)
        receipts.append(record)
        if (pos - a.start) % 10 == 0 or pos + 1 == min(a.stop, len(rows)):
            print(
                "ALPHA18_GENERATE",
                pos + 1,
                len(rows),
                origin,
                round(time.monotonic() - started, 2),
                flush=True,
            )
    public = dict(
        executive_summary="Locked candidate, lag and permuted-age generation; no targets read.",
        lock_sha256=sha(a.repo / "ALPHA18-LOCKED-HYPOTHESIS.json"),
        new_forecast_processes=sum(len(r["runs"]) for r in receipts),
        origins=len(receipts),
        passed=all(r["passed"] for r in receipts),
        receipts=receipts,
        new_Docker_execution=False,
    )
    put(a.repo / f"backtesting/alpha18/experiment-generation-{a.start}-{a.stop}.json", public)


def proxy(base, candidate):
    denominator = base.mean(axis=0)
    assert (denominator > 0).all()
    ratios = candidate.mean(axis=0) / denominator
    return dict(
        proxy=float(WEIGHTS @ ratios),
        ratios=dict(zip(COMPONENTS, ratios.tolist(), strict=True)),
        baseline_mean=dict(zip(COMPONENTS, denominator.tolist(), strict=True)),
        candidate_mean=dict(zip(COMPONENTS, candidate.mean(axis=0).tolist(), strict=True)),
    )


def evaluate(a):
    scoring = official_score_module(a)
    lock = load(a.repo / "ALPHA18-LOCKED-HYPOTHESIS.json")
    manifest = load(a.repo / "backtesting/alpha18/input-manifest.json")
    labels = normalized_frame(a.work / "labels-rates_daily.parquet").pivot(
        index="date", columns="asset", values="value"
    )
    rows = [r for r in manifest["cards"] if r["group"] == "past_vintage_UST"]
    completed = []
    incomplete = []
    cell_rows = []

    def score(samples, y):
        v = scoring._composite(
            samples.reshape(len(samples), -1),
            y.reshape(-1),
            weights=(0.5, 0.3, 0.2),
            tail_levels=(0.01, 0.05, 0.95, 0.99),
            joint="variogram",
            tail_metric="pinball",
            ref_scale=None,
        )
        return np.array([v[k] for k in COMPONENTS])

    for row in rows:
        origin = row["origin"]
        dates = [(pd.Timestamp(origin) + pd.offsets.BDay(h)).strftime("%Y-%m-%d") for h in H]
        y = labels.reindex(dates)[ASSETS].to_numpy().T
        folder = a.work / "experiment" / origin
        receipt = load(folder / "receipt.json")
        assert receipt["passed"]
        samples = {"baseline": matrix(a.work / "forecasts" / row["id"] / "forecast.parquet", H)}
        for name in ["candidate", "lag_baseline", "lag_candidate"]:
            sample_path = folder / name / "samples.npy"
            rec = next(x for x in receipt["runs"] if x["name"] == name)
            assert sha(sample_path) == rec["sample_sha256"]
            samples[name] = np.load(sample_path)
        samples["placebo"] = (
            samples["candidate"]
            if receipt.get("placebo_reuses_candidate_exactly")
            else np.load(folder / "placebo/samples.npy")
        )
        for ai, asset in enumerate(ASSETS):
            for hi, h in enumerate(H):
                if not np.isfinite(y[ai, hi]):
                    continue
                entry = dict(origin=origin, asset=asset, horizon=h)
                for name in ["baseline", "candidate"]:
                    entry[name] = score(
                        samples[name][:, ai : ai + 1, hi : hi + 1], y[ai : ai + 1, hi : hi + 1]
                    ).tolist()
                cell_rows.append(entry)
        if not np.isfinite(y).all():
            incomplete.append(dict(origin=origin, available_cells=int(np.isfinite(y).sum())))
            continue
        completed.append(
            dict(
                origin=origin,
                year=origin[:4],
                quarter=str(pd.Period(origin, freq="Q")),
                placebo_changed=receipt["actual_gap"] != receipt["placebo_gap"],
                components={name: score(s, y).tolist() for name, s in samples.items()},
            )
        )
    base = np.array([x["components"]["baseline"] for x in completed])
    cand = np.array([x["components"]["candidate"] for x in completed])
    result = proxy(base, cand)
    rng = np.random.default_rng(18018)
    n = len(base)
    bootstrap = []
    for _ in range(1000):
        starts = rng.integers(0, n - 3, size=int(np.ceil(n / 4)))
        ix = np.concatenate([np.arange(s, s + 4) for s in starts])[:n]
        bootstrap.append(proxy(base[ix], cand[ix])["proxy"])
    result["block95"] = np.quantile(bootstrap, [0.025, 0.975]).tolist()
    den = base.mean(axis=0)
    gain = ((base - cand) / den) @ WEIGHTS
    best = int(np.argmax(gain))
    result["remove_best_origin"] = proxy(
        np.delete(base, best, axis=0), np.delete(cand, best, axis=0)
    )
    quarter_gain = {
        q: float(gain[[x["quarter"] == q for x in completed]].sum())
        for q in sorted({x["quarter"] for x in completed})
    }
    best_quarter = max(quarter_gain, key=quarter_gain.get)
    mask = np.array([x["quarter"] != best_quarter for x in completed])
    result["remove_best_quarter"] = dict(quarter=best_quarter, **proxy(base[mask], cand[mask]))
    result["by_year"] = {}
    result["leave_one_year_out"] = {}
    for year in sorted({x["year"] for x in completed}):
        mask = np.array([x["year"] == year for x in completed])
        result["by_year"][year] = dict(origins=int(mask.sum()), **proxy(base[mask], cand[mask]))
        result["leave_one_year_out"][year] = proxy(base[~mask], cand[~mask])
    result["lag"] = proxy(
        np.array([x["components"]["lag_baseline"] for x in completed]),
        np.array([x["components"]["lag_candidate"] for x in completed]),
    )
    result["placebo"] = proxy(base, np.array([x["components"]["placebo"] for x in completed]))
    result["placebo"]["changed_complete_origins"] = sum(x["placebo_changed"] for x in completed)
    result["placebo"]["mechanism_identification"] = (
        "UNKNOWN_LOW_CHANGED_SAMPLE"
        if result["placebo"]["changed_complete_origins"] < 20
        else "SUFFICIENT_CHANGED_ORIGINS"
    )
    result["by_asset"] = {}
    result["by_horizon"] = {}
    # Matched observed marginal slices, including incomplete grids, are reported separately.
    for key, groupvals, dest in [("asset", ASSETS, "by_asset"), ("horizon", H, "by_horizon")]:
        for value in groupvals:
            sel = [x for x in cell_rows if x[key] == value]
            b = np.array([x["baseline"] for x in sel])
            c = np.array([x["candidate"] for x in sel])
            result[dest][str(value)] = dict(
                cells=len(sel),
                marginal_ratio=float(c[:, 0].mean() / b[:, 0].mean()),
                tail_ratio=float(c[:, 2].mean() / b[:, 2].mean()),
                single_cell_proxy=float(
                    (5 * c[:, 0].mean() / b[:, 0].mean() + 2 * c[:, 2].mean() / b[:, 2].mean()) / 7
                ),
            )
    b = np.array([x["baseline"] for x in cell_rows])
    c = np.array([x["candidate"] for x in cell_rows])
    result["all_available_single_cell_proxy"] = float(
        (5 * c[:, 0].mean() / b[:, 0].mean() + 2 * c[:, 2].mean() / b[:, 2].mean()) / 7
    )
    checks = dict(
        enough_complete_origins=n >= 30,
        primary_2percent=result["proxy"] <= 0.98,
        CI_upper_below_one=result["block95"][1] < 1,
        joint_no5percent_damage=result["ratios"]["joint"] <= 1.05,
        tail_no5percent_damage=result["ratios"]["tail"] <= 1.05,
        two_assets_improve=sum(v["marginal_ratio"] < 1 for v in result["by_asset"].values()) >= 2,
        horizon_no5percent_damage=all(
            v["marginal_ratio"] <= 1.05 for v in result["by_horizon"].values()
        ),
        best_origin_removed=result["remove_best_origin"]["proxy"] < 1,
        best_quarter_removed=result["remove_best_quarter"]["proxy"] < 1,
        all_leave_year_out=all(v["proxy"] < 1 for v in result["leave_one_year_out"].values()),
        lag_improves=result["lag"]["proxy"] < 1,
        age_specific_placebo="UNKNOWN"
        if result["placebo"]["changed_complete_origins"] < 20
        else result["proxy"] < result["placebo"]["proxy"],
    )
    if all(v is True for v in checks.values()):
        classification = "ALPHA_CANDIDATE_SUPPORTED_FOR_VALIDATION"
    elif result["proxy"] < 1:
        classification = "EXPLORATORY_IMPROVEMENT_ONLY"
    else:
        classification = "NO_REPRODUCIBLE_IMPROVEMENT"
    put(
        a.work / "experiment-individual-results.json",
        dict(complete=completed, incomplete=incomplete, cell_rows=cell_rows),
    )
    result.update(
        executive_summary=(
            "One locked original-kernel support-alignment exper"
            "iment on exposed stale-vintage UST; no fresh-close"
            " alpha demonstrated."
        ),
        classification=classification,
        protocol=lock["protocol"],
        lock_sha256=sha(a.repo / "ALPHA18-LOCKED-HYPOTHESIS.json"),
        origins_requested=len(rows),
        complete_origins=n,
        incomplete_origins=len(incomplete),
        observed_marginal_cells=len(cell_rows),
        assets=ASSETS,
        horizons=H,
        dates=[rows[0]["origin"], rows[-1]["origin"]],
        checks=checks,
        contamination="EXPLORATORY_EXPOSED_HISTORY",
        independent_OOS=False,
        independent_alpha_verified="UNKNOWN",
        official_M0_normalization=False,
        official_composite=None,
        metric=(
            "Same-complete-origin ratio-of-means raw CRPS/vario"
            "gram/pinball research proxy, weights .5/.3/.2. Not"
            " M0 and not an official score."
        ),
        parameters_fitted=0,
        candidate_models=1,
        fresh_close_effect="EXACT_BASELINE_AGE0",
        Final_promotion=False,
        individual_result_sha256=sha(a.work / "experiment-individual-results.json"),
    )
    put(a.repo / "ALPHA18-EXPERIMENT-RESULT.json", result)
    print(
        json.dumps(
            {
                k: result[k]
                for k in [
                    "classification",
                    "complete_origins",
                    "proxy",
                    "ratios",
                    "block95",
                    "checks",
                ]
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("stage", choices=["generate", "evaluate"])
    for key in ["repo", "baseline", "official", "work"]:
        p.add_argument("--" + key, type=pathlib.Path, required=True)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--stop", type=int, default=154)
    a = p.parse_args()
    for key in ["repo", "baseline", "official", "work"]:
        setattr(a, key, getattr(a, key).resolve())
    {"generate": generate, "evaluate": evaluate}[a.stage](a)

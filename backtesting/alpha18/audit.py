"""## Executive summary (read this first)
Audit baseline identity, repeatability, cutoff safety and descriptive error uncertainty.
These are diagnostic controls, not a candidate alpha experiment or independent validation.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import pathlib
import shutil
import sys

import numpy as np
import pandas as pd
from diagnostic import baseline_cli, load, normalized_frame, put, sha


def main():
    p = argparse.ArgumentParser()
    for name in ["repo", "baseline", "official", "common", "work"]:
        p.add_argument("--" + name, type=pathlib.Path, required=True)
    a = p.parse_args()
    for name in vars(a):
        setattr(a, name, getattr(a, name).resolve())
    manifest = load(a.repo / "backtesting/alpha18/input-manifest.json")
    f = pd.read_parquet(a.work / "individual-diagnostics.parquet")
    summary = {}
    # Descriptive uncertainty only: fixed 4-origin moving blocks, 1000 draws, seed18018.
    for group, sub in f.groupby("group"):
        origins = (
            sub.groupby("origin")[["z_error", "positive_error", "coverage90", "coverage98"]]
            .mean()
            .sort_index()
        )
        rng = np.random.default_rng(18018)
        matrix = origins.to_numpy()
        n = len(matrix)
        sims = []
        for _ in range(1000):
            starts = rng.integers(0, n - 3, size=int(np.ceil(n / 4)))
            ix = np.concatenate([np.arange(s, s + 4) for s in starts])[:n]
            sims.append(matrix[ix].mean(axis=0))
        low, high = np.quantile(sims, [0.025, 0.975], axis=0)
        summary[group] = dict(
            origins=n,
            origin_weighted_mean=origins.mean().to_dict(),
            moving_block95={
                col: [float(low[i]), float(high[i])] for i, col in enumerate(origins.columns)
            },
            calendar_note=(
                "Authored market cards are sparse/event-selected, s"
                "o four adjacent sampled origins are not fixed cale"
                "ndar blocks. Interval is descriptive, not an iid/s"
                "election-adjusted confidence guarantee."
            ),
            per_year={
                str(k): dict(
                    n=len(v),
                    mean_error=float(v.z_error.mean()),
                    coverage90=float(v.coverage90.mean()),
                )
                for k, v in sub.groupby("year")
            },
            leave_one_era_out={
                str(k): dict(
                    cells=len(sub[sub.era != k]),
                    mean_error=float(sub[sub.era != k].z_error.mean()),
                    coverage90=float(sub[sub.era != k].coverage90.mean()),
                )
                for k in sorted(sub.era.unique())
                if len(sub[sub.era != k])
            },
            error_without_largest_absolute_origin=None,
        )
        worst = origins.z_error.abs().idxmax()
        summary[group]["error_without_largest_absolute_origin"] = float(
            origins.drop(worst).z_error.mean()
        )
    # Current imported scorer files must match the authenticated source checkout bytes.
    import qfbench2_common
    from qfbench2_common.scoring import crps

    shared_source = a.common / "common/qfbench2_common"
    score_identity = dict(
        common_installed_tree_digest=qfbench2_common.package_tree_digest(),
        common_source_tree_digest=qfbench2_common.package_tree_digest(shared_source),
        crps_source_sha256=sha(pathlib.Path(crps.__file__)),
        crps_source_matches=sha(pathlib.Path(crps.__file__))
        == sha(shared_source / "scoring/crps.py"),
        track_scoring_sha256=sha(a.official / "qfbench2_track_forecasting/scoring.py"),
        track_tail_sha256=sha(a.official / "qfbench2_track_forecasting/tail.py"),
        metric_impl="Official source functions imported, no rewritten score math",
        official_M0_scales=False,
    )
    assert score_identity["crps_source_matches"]
    assert (
        score_identity["common_installed_tree_digest"]
        == score_identity["common_source_tree_digest"]
    )
    # Strict hash and date checks across every prepared input, excluding evaluation labels.
    dates_ok = True
    hashes_ok = True
    for row in manifest["cards"]:
        root = a.work / "inputs" / row["id"]
        for name, record in row["input_files"].items():
            dates_ok &= bool((normalized_frame(root / name)["date"] <= row["origin"]).all())
            hashes_ok &= sha(root / name) == record["input_sha256"]
    assert dates_ok and hashes_ok
    # Four projected family representatives: deterministic repeat and unchanged FF03 daily route.
    cli = baseline_cli(a)
    sys.path.insert(0, str(a.repo / "backtesting/finalfit03"))
    wrapper = importlib.import_module("candidate_monthly")
    controls = []
    for family in ["T2-F1", "T2-F2", "T2-F3", "T2-F4"]:
        row = next(
            r
            for r in manifest["cards"]
            if r["group"] == "authored_market_projection" and r["family"] == family
        )
        unit = a.work / "inputs" / row["id"]
        original = a.work / "forecasts" / row["id"] / "forecast.parquet"
        for route in ["repeat", "ff03_daily"]:
            out = a.work / "controls" / row["id"] / route / "forecast.parquet"
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
            fn = cli.main if route == "repeat" else wrapper.main
            with contextlib.redirect_stdout(io.StringIO()):
                assert fn(argv) == 0
            controls.append(
                dict(
                    family=family,
                    control=route,
                    parquet_identical=sha(out) == sha(original),
                    passed=sha(out) == sha(original),
                )
            )
            assert controls[-1]["passed"]
        # Future-value mutation is adversarial synthetic data, never a performance target.
        altered = a.work / "controls" / row["id"] / "future_mutated_input"
        shutil.copytree(unit, altered, dirs_exist_ok=True)
        for panel in altered.glob("*.parquet"):
            frame = pd.read_parquet(panel)
            end = frame.iloc[-1:].copy()
            end["date"] = (pd.Timestamp(row["origin"]) + pd.offsets.BDay(1)).strftime("%Y-%m-%d")
            end["value"] = 1e12
            pd.concat([frame, end], ignore_index=True).to_parquet(panel, index=False)
        out = a.work / "controls" / row["id"] / "future_mutation" / "forecast.parquet"
        argv = [
            "--panels",
            str(altered),
            "--text",
            str(altered / "text"),
            "--asof",
            row["origin"],
            "--out",
            str(out),
            "--n-draws",
            "1000",
            "--seed",
            "0",
        ]
        with contextlib.redirect_stdout(io.StringIO()):
            assert cli.main(argv) == 0
        controls.append(
            dict(
                family=family,
                control="future_panel_mutation",
                parquet_identical=sha(out) == sha(original),
                passed=sha(out) == sha(original),
            )
        )
        assert controls[-1]["passed"]
    put(
        a.repo / "backtesting/alpha18/diagnostic-controls.json",
        dict(
            executive_summary=(
                "Descriptive origin-block uncertainty and twelve ba"
                "seline controls, not candidate falsification."
            ),
            bootstrap_seed=18018,
            bootstrap_repetitions=1000,
            block_origins=4,
            uncertainty=summary,
            controls=controls,
            controls_passed=sum(x["passed"] for x in controls),
            input_hashes_passed=hashes_ok,
            input_date_cutoff_passed=dates_ok,
            scorer_identity=score_identity,
            limitations=[
                "No release vintage authentication for original H10/H15 panel rows",
                "Exposed selected events; raw metrics are not a random population sample",
                "No independent candidate performance",
                "No placebo/lag candidate tested because no alpha adapter selected yet",
            ],
        ),
    )
    print(json.dumps(dict(controls_passed=len(controls), uncertainty=summary)), flush=True)


if __name__ == "__main__":
    main()

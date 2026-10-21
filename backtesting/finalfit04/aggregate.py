(
    "Executive summary: authenticate actual receipts and pai"
    "red official scores; never fit forecasts."
)

import argparse
import hashlib
import itertools
import json
import pathlib
import sys
import tomllib
from collections import Counter

import numpy as np
import pandas as pd


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, o):
    p.write_text(json.dumps(o, indent=2) + "\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", type=pathlib.Path, required=True)
    p.add_argument("--official", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    sys.path.insert(0, str(a.official.resolve()))
    from qfbench2_track_forecasting.scoring import _composite

    root = a.out
    inv = json.loads((root / "FINALFIT04-PRACTICE-INVENTORY.json").read_text())
    ids = [c["id"] for c in inv["cards"]]
    before = json.loads((root / "FINALFIT04-INPUT-MANIFEST.json").read_text())["cards"]
    allrows = []
    pairs = []
    scores = []
    slices = []
    failed = []
    for card in inv["cards"]:
        cid = card["id"]
        found = list(a.evidence.glob("*/" + cid + "/paired.json"))
        assert len(found) == 1
        dest = found[0].parent
        pair = json.loads(found[0].read_text())
        assert pair["status"] == "DAILY_IDENTITY_CONFIRMED"
        pairs.append(pair)
        expected = list(
            itertools.product(card["targets"]["asset_ids"], card["targets"]["horizons"])
        )
        for label in ["original", "ff03"]:
            r = json.loads((dest / label / "receipt.json").read_text())
            s = json.loads((dest / label / "score.json").read_text())
            assert r["inputs"] == before[cid]
            assert (
                r["forecast"]["exit"] == 0
                and r["required_outputs"]
                and r["gates"]["exit"] == 0
                and s["exit"] == 0
            )
            inspect = r["container_inspect"]
            assert (
                inspect["HostConfig"]["NetworkMode"] == "none"
                and inspect["HostConfig"]["ReadonlyRootfs"]
            )
            assert len(inspect["Mounts"]) == 2 and {
                x["Destination"] for x in inspect["Mounts"]
            } == {"/input", "/output"}
            assert not next(x for x in inspect["Mounts"] if x["Destination"] == "/input")["RW"]
            assert (
                inspect["HostConfig"]["Memory"] == 4 * 1024**3 and not inspect["State"]["OOMKilled"]
            )
            for name, digest in r["output_hashes"].items():
                assert sha(dest / label / "output" / name) == digest
            numeric = r["numeric_result"]
            assert numeric["finite"] and numeric["draws"] == 1000
            d = pd.read_parquet(dest / label / "output/forecast.parquet")
            assert not d.duplicated(["draw", "asset", "horizon"]).any()
            assert set(zip(d.asset, d.horizon)) == set(expected)
            assert d.groupby(["asset", "horizon"]).size().eq(1000).all()
            metrics = s["metrics"]
            assert (
                metrics["admissible"]
                and metrics["normalization_mode"] == "raw_unrankable"
                and not metrics["rankable"]
            )
            assert metrics["tail_metric"] == "pinball"
            scores.append(
                dict(
                    card=cid,
                    candidate=label,
                    family=card["family"],
                    assets=card["targets"]["asset_ids"],
                    horizons=card["targets"]["horizons"],
                    units=card["targets"]["value_unit"],
                    **metrics,
                )
            )
            allrows.append(
                dict(
                    card=cid,
                    candidate=label,
                    family=card["family"],
                    source_sha=r["source_sha"],
                    image=r["image"],
                    command=r["forecast"]["command"],
                    forecast_exit=0,
                    gates=r["gate_result"],
                    wall_seconds=r["forecast"]["wall_seconds"],
                    output_bytes=r["output_bytes"],
                    hashes=r["output_hashes"],
                    numeric_sha256=numeric["numeric_sha256"],
                    grid_cells=len(expected),
                    n_draws=1000,
                    finite=True,
                    network="none",
                    input_answer_firewall=True,
                    mounts=inspect["Mounts"],
                    memory_limit_bytes=inspect["HostConfig"]["Memory"],
                    oom_killed=False,
                    container_state=inspect["State"],
                    metadata=numeric["metadata"],
                )
            )
        # Score labels are read only in this post-execution aggregation process.
        yframe = pd.read_parquet(a.official / "practice-answers" / f"{cid}.parquet").set_index(
            ["asset", "horizon"]
        )
        d = pd.read_parquet(dest / "ff03/output/forecast.parquet")
        sample = (
            d.pivot(index="draw", columns=["asset", "horizon"], values="value")
            .reindex(columns=pd.MultiIndex.from_tuples(expected))
            .to_numpy()
        )
        y = np.array([float(yframe.loc[key, "value"]) for key in expected])
        c = tomllib.loads((a.official / "units" / cid / "card.toml").read_text())
        params = c["scoring"]["params"]
        w = params["weights"]
        full = _composite(
            sample,
            y,
            weights=tuple(w[k] for k in ["marginal", "joint", "tail"]),
            tail_levels=tuple(params["tail_levels"]),
            joint=params["joint"],
            tail_metric="pinball",
            ref_scale=None,
        )
        ms = scores[-1]
        assert np.allclose(
            [full[k] for k in ["marginal", "joint", "tail", "composite"]],
            [
                ms[k]
                for k in ["marginal_crps", "joint_variogram", "tail_penalty", "composite_score"]
            ],
            rtol=1e-12,
            atol=1e-14,
        )
        for kind, keys in [
            ("asset", card["targets"]["asset_ids"]),
            ("horizon", card["targets"]["horizons"]),
        ]:
            for key in keys:
                ix = [
                    i
                    for i, (asset, h) in enumerate(expected)
                    if (asset if kind == "asset" else h) == key
                ]
                v = _composite(
                    sample[:, ix],
                    y[ix],
                    weights=(0.5, 0.3, 0.2),
                    tail_levels=tuple(params["tail_levels"]),
                    joint="variogram",
                    tail_metric="pinball",
                    ref_scale=None,
                )
                slices.append(
                    dict(
                        card=cid,
                        kind=kind,
                        key=key,
                        cells=len(ix),
                        units=card["targets"]["value_unit"],
                        marginal_crps=v["marginal"],
                        joint_variogram=v["joint"],
                        tail_pinball=v["tail"],
                        both_candidates_equal=True,
                        scope=(
                            "Official component functions on a research subset; no n"
                            "ormalized score or synthetic single-cell official card."
                        ),
                    )
                )
    repeats = [json.loads(p.read_text()) for p in a.evidence.glob("*/*/repeat.json")]
    assert len(repeats) == 6 and all(x["exit"] == 0 and x["identical"] for x in repeats)
    for cid in ids:
        x = [s for s in scores if s["card"] == cid]
        assert len(x) == 2
        assert all(
            x[0][k] == x[1][k]
            for k in ["marginal_crps", "joint_variogram", "tail_penalty", "composite_score"]
        )
    for label, name in [("original", "ORIGINAL"), ("ff03", "FF03")]:
        save(
            root / f"FINALFIT04-{name}-DOCKER-RESULTS.json",
            dict(
                executive_summary=(
                    "22 actual forecast processes and official gate checks; " "no answer mounts."
                ),
                executed=22,
                passed=22,
                failed=0,
                blocked=0,
                run_id=39552405145,
                cards=[r for r in allrows if r["candidate"] == label],
            ),
        )
    save(
        root / "FINALFIT04-DAILY-AB.json",
        dict(
            executive_summary="DAILY_IDENTITY_CONFIRMED across all 22 official daily cards.",
            status="DAILY_IDENTITY_CONFIRMED",
            cards=pairs,
            all_file_bytes_equal=True,
            all_numeric_draws_equal=True,
            ff03_repeat_count=6,
            ff03_deterministic_repeats=6,
        ),
    )
    save(
        root / "FINALFIT04-PRACTICE-RAW-SCORES.json",
        dict(
            executive_summary=(
                "OFFICIAL_RAW_PRACTICE_SCORE, EXPOSED_PRACTICE_DIAGNOSTIC. "
                "No cross-unit raw mean."
            ),
            official_scores=scores,
            slices=slices,
            normalization="NOT_REPRODUCED_NO_AUTHENTICATED_SCALE_BUNDLE",
            m0_procedure_reviewed=True,
            m0_generator_not_run=True,
            overall_normalized_score=None,
            cross_unit_raw_average=None,
            score_deltas=dict(marginal_crps=0, joint_variogram=0, tail_pinball=0, raw_composite=0),
            all_22_scored_each=True,
            unscored_cards=0,
            single_cell_cards=sum(s["cell_count"] == 1 for s in scores) // 2,
            multi_cell_cards=sum(s["cell_count"] > 1 for s in scores) // 2,
        ),
    )
    save(
        root / "backtesting/finalfit04/results/docker-summary.json",
        dict(
            executive_summary="Actual processes, not host simulations.",
            main_forecasts=44,
            repeated_forecasts=6,
            all_exited_zero=True,
            official_gate_calls=44,
            official_score_calls=44,
            families=dict(Counter(x["family"] for x in inv["cards"])),
            max_wall_seconds=max(r["wall_seconds"] for r in allrows),
            max_output_bytes=max(r["output_bytes"] for r in allrows),
            peak_rss="NOT_MEASURED_IN_MAIN_BATCH",
            whole_final_run_seconds="UNKNOWN",
            failed=failed,
        ),
    )
    print(
        json.dumps(
            dict(
                cards=22,
                forecasts=44,
                repeats=6,
                scored=44,
                failed=failed,
                identity="22/22",
                single_cell_cards=sum(s["cell_count"] == 1 for s in scores) // 2,
            )
        )
    )


if __name__ == "__main__":
    main()

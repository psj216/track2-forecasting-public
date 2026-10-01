"""## Executive summary (read this first)

Prepare private historical labels and real no-text V5.1 draws. Scale targets
use the square root of future summed innovation squares divided by V5.1 SD.
No 2025 market row is accepted.
"""

import argparse
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from qfbench2_track_forecasting.thesis01.v51_shift import v51_no_text_prior
from qfbench2_track_forecasting.thesis01.asset_semantics import family
from qfbench2_track_forecasting.thesis01.innovations import innovations
from qfbench2_track_forecasting.thesis01.scaling import scaled
from qfbench2_track_forecasting.surprise01 import HORIZONS, SEED
from qfbench2_track_forecasting.v12.data_parity import _label
from .build_market_extension import historical_market


def event_origin(event, observations):
    day = pd.Timestamp(event["release_date"])
    timestamp = event.get("release_timestamp")
    if timestamp:
        local = pd.Timestamp(timestamp).tz_convert("America/New_York")
        # Conservative common observation time: H.10 noon, then rates/factors.
        if local.hour >= 12:
            day += pd.offsets.BDay(1)
    else:
        day += pd.offsets.BDay(1)
    pos = int(observations.searchsorted(day))
    if pos >= len(observations):
        return None
    origin = observations[pos]
    if np.busday_count(np.datetime64(day.date()), np.datetime64(origin.date())) > 3:
        return None
    return origin


def baseline_group(series, kinds, origin, group):
    roster = []
    for a, s in series.items():
        past = s.loc[:origin]
        if family(a, kinds[a]) == group and len(past) >= 252:
            lag = np.busday_count(np.datetime64(past.index[-1].date()), np.datetime64(origin.date()))
            if lag <= 3:
                roster.append(a)
    assets = sorted(roster)
    if not assets:
        return [], None
    runtime_family = {"FX": "T2-F2", "Rates": "T2-F1", "Factor/Equity": "T2-F4"}[group]
    draws = 1000 if group == "Factor/Equity" else 500
    samples = [v51_no_text_prior(series[a], a, kinds[a], list(HORIZONS), runtime_family,
                                str(origin.date()), SEED, draws) for a in assets]
    return assets, np.stack(samples, axis=1)


def _initialize_cache(root, cache_root):
    global _SERIES, _KINDS, _CACHE_ROOT
    _SERIES, _KINDS = historical_market(Path(root))
    _CACHE_ROOT = Path(cache_root)


def _cache_task(key):
    stamp, group = key
    cache = _CACHE_ROOT / (stamp + "_" + group.replace("/", "_") + ".npz")
    valid = False
    if cache.exists():
        try:
            with np.load(cache) as saved:
                x = saved['samples']
                valid = x.ndim == 3 and x.shape[2] == len(HORIZONS) and np.isfinite(x).all()
        except (OSError, ValueError, EOFError):
            pass
    if not valid:
        assets, samples = baseline_group(_SERIES, _KINDS, pd.Timestamp(stamp), group)
        if assets:
            temporary = cache.with_suffix('.pending.npz')
            np.savez_compressed(temporary, assets=np.asarray(assets), samples=samples)
            temporary.replace(cache)
    return key


def prepare(root, ledger, private_root):
    if private_root.resolve().is_relative_to(root.resolve()):
        raise ValueError("Private labels and raw draws must remain outside Git")
    ledger_bytes = ledger.read_bytes()
    events = json.loads(ledger_bytes)
    events = [e for e in events if "2001-01-01" <= e["release_date"] <= "2024-12-18"
              and e["standardized_surprise"] is not None]
    series, kinds = historical_market(root)
    dates = pd.bdate_range("2000-01-03", "2024-12-18")
    panel = pd.DataFrame({a: s.reindex(dates) for a, s in series.items()}, index=dates)
    _, sigma = scaled(innovations(panel, kinds))
    tasks = defaultdict(list)
    for e in events:
        for a, s in series.items():
            origin = event_origin(e, s.index)
            if origin is None or origin < pd.Timestamp(e["release_date"]) or origin not in sigma.index:
                continue
            if not np.isfinite(sigma.loc[origin, a]):
                continue
            tasks[(str(origin.date()), family(a, kinds[a]))].append((e, a))
    rows = []
    cache_root = private_root / "draw_cache"
    cache_root.mkdir(parents=True, exist_ok=True)
    items = sorted(tasks.items())
    # Independent baseline calls only. Their asset order, seed and outputs
    # do not depend on worker completion order.
    with ProcessPoolExecutor(max_workers=6, initializer=_initialize_cache,
                             initargs=(str(root), str(cache_root))) as pool:
        for i, _ in enumerate(pool.map(_cache_task, [key for key, _ in items])):
            if i % 100 == 0:
                print(f"cached {i+1}/{len(items)} date/group baselines", flush=True)
    for task_index, ((stamp, group), entries) in enumerate(items):
        origin = pd.Timestamp(stamp)
        cache = cache_root / (stamp + "_" + group.replace("/", "_") + ".npz")
        if cache.exists():
            saved = np.load(cache)
            assets, samples = saved["assets"].tolist(), saved["samples"]
        else:
            assets, samples = baseline_group(series, kinds, origin, group)
            if not assets:
                continue
            np.savez_compressed(cache, assets=np.asarray(assets), samples=samples)
        for e, a in entries:
            if a not in assets:
                continue
            i = assets.index(a)
            scale_sigma = float(sigma.loc[origin, a])
            for hidx, h in enumerate(HORIZONS):
                label = _label(series[a], kinds[a], origin, h, "2024-12-19", False)
                if label is None or label[1] > pd.Timestamp("2024-12-18"):
                    continue
                native, end = label
                window = series[a].loc[origin:end]
                step = window.diff().iloc[1:].to_numpy() if kinds[a] == "level" else window.iloc[1:].to_numpy()
                path_scale = max(float(np.sqrt(np.sum(step ** 2))), 1e-12)
                sd = max(float(np.std(samples[:, i, hidx])), 1e-12)
                norm = scale_sigma * np.sqrt(h)
                truth = float(series[a].loc[origin] + native if kinds[a] == "level" else native)
                rows.append({"event_id": e["event_id"], "event_type": e["event_type"],
                             "reference_period": e["reference_period"], "release_date": e["release_date"],
                             "origin": stamp, "asset": a, "group": group, "horizon": h,
                             "target_end": str(end.date()), "surprise": e["standardized_surprise"],
                             "q": float(native / norm), "truth": truth, "sigma": scale_sigma,
                             "normalization": norm, "baseline_sd": sd,
                             "log_scale_response": float(np.log(path_scale / sd)),
                             "cache_file": cache.name, "asset_index": i, "horizon_index": hidx})
        if task_index % 50 == 0:
            print(f"prepared {task_index+1}/{len(items)} date/group tasks ({stamp})", flush=True)
    df = pd.DataFrame(rows)
    output = private_root / "training_cases.parquet"
    df.to_parquet(output, index=False)
    meta = {"cases": len(df), "event_family_records": int(df[["event_id", "event_type"]].drop_duplicates().shape[0]),
            "release_clusters": int(df["event_id"].nunique()),
            "first_event": df["release_date"].min(), "last_event": df["release_date"].max(),
            "max_target_end": df["target_end"].max(),
            "case_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "event_ledger_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
            "bin_edges": {k: np.quantile(np.abs(v["standardized_surprise"].to_numpy(float)), [1/3, 2/3]).tolist()
                          for k, v in pd.DataFrame([e for e in events if e["release_date"] <= "2016-12-31"]).groupby("event_type")}}
    (private_root / "training_manifest.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--ledger", type=Path, required=True)
    p.add_argument("--private-root", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(prepare(a.root, a.ledger, a.private_root), indent=2))

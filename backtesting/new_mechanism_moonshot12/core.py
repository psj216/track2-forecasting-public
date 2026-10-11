"""Executive summary: build past-only states and resample entire matured joint paths.

Every output draw shares one historical origin across every requested cell.
Scoring is imported from the pinned common toolkit, never reimplemented.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from qfbench2_common.scoring.crps import crps_ensemble
from qfbench2_track_forecasting.thesis01.scaling import scaled

PARENT = '126a7c628aa60783986450037309f5f59603276a'
MAIN = 'e1b5cf3b3a87966e902332ef3cc5c0ed2dbffee8'
BRANCH = 'track2/new-mechanism-moonshot-12'
LEDGER_HASH = '5a421fa5c10745c69469c683797bf42f4abf54288e8082984bcf39fda76968a6'
CENTER_HASH = '30f5113b24ee5f9e5335b39f5a224d45633307aeb0dd77621ce29addec56d05f'
SEED = 31812
KS = (8, 16, 32, 64)
YEARS = tuple(range(2016, 2025))
HORIZONS = (5, 21, 63, 126, 189)
FEATURE_NAMES = ('move5', 'move21', 'move63', 'move126', 'vol21', 'vol63', 'trend21', 'range126')
MIN_ANALOGS = 8
MIN_COVERAGE = .80
ORACLE_MEMBERS = 8
DRAW_COUNT = 1000


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [clean(v) for v in value]
    if isinstance(value, (np.integer, int)) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    return value


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(clean(value), indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def fingerprint(series, kinds, origins):
    """Business-calendar windows and original trailing scale are all prefix-safe."""
    dates = pd.bdate_range(min(s.index.min() for s in series.values()), max(s.index.max() for s in series.values()))
    steps = pd.DataFrame({a: (s.diff() if kinds[a] == 'level' else s).reindex(dates) for a, s in series.items()})
    raw = pd.DataFrame({a: s.reindex(dates) for a, s in series.items()}).ffill()
    for a in series:
        if kinds[a] != 'level':
            raw[a] = steps[a].fillna(0).cumsum()  # Synthetic cumulative index, not a price predictor.
    _, sigma252 = scaled(steps)
    sigma63 = steps.rolling(63, min_periods=50).std(ddof=0).shift(1).clip(lower=1e-8)
    features = {}
    for w in (5, 21, 63, 126):
        features[f'move{w}'] = steps.rolling(w, min_periods=max(1, int(np.ceil(.8*w)))).sum() / (sigma63 * np.sqrt(w))
    features['vol21'] = steps.rolling(21, min_periods=17).std(ddof=0) / sigma63
    features['vol63'] = steps.rolling(63, min_periods=50).std(ddof=0) / sigma252
    features['trend21'] = (raw - raw.rolling(21, min_periods=17).mean()) / sigma63
    low = raw.rolling(126, min_periods=101).min()
    width = raw.rolling(126, min_periods=101).max() - low
    features['range126'] = ((raw-low) / width.replace(0, np.nan)).fillna(.5).where(low.notna())
    columns = {f'{a}:{name}': features[name][a].reindex(origins) for a in sorted(series) for name in FEATURE_NAMES}
    out = pd.DataFrame(columns, index=origins)
    out['shared:move21'] = features['move21'].mean(axis=1).reindex(origins)
    out['shared:vol63'] = features['vol63'].mean(axis=1).reindex(origins)
    return out.replace([np.inf, -np.inf], np.nan), sigma63.reindex(origins)


def normalize_history(history, query):
    """One expanding-history median/IQR fitted strictly before the query origin."""
    median = history.median(axis=0)
    scale = history.quantile(.75) - history.quantile(.25)
    scale = scale.where(scale > 1e-8, 1.)
    return (history-median)/scale, (query-median)/scale


def shared_distances(history, query):
    x, q = normalize_history(history, query)
    valid = np.isfinite(x.to_numpy()) & np.isfinite(q.to_numpy())[None, :]
    coverage = valid.sum(axis=1) / len(query)
    diff = np.where(valid, x.to_numpy()-q.to_numpy()[None, :], 0.)
    distance = np.sqrt(np.sum(diff*diff, axis=1) / np.maximum(valid.sum(axis=1), 1))
    distance[coverage < MIN_COVERAGE] = np.inf
    return distance, coverage


def eligible_paths(ends, values, current_origin):
    """A complete path's last actual observed endpoint must be strictly earlier."""
    return np.isfinite(values).all(axis=1) & (~np.isnat(ends)).all(axis=1) & (ends.max(axis=1) < np.datetime64(current_origin, 'ns'))


def map_innovations(innovations, kinds, current_levels, current_scales):
    kinds = np.asarray(kinds)
    levels = kinds == 'level'
    return np.where(levels[None, :], current_levels[None, :] + innovations*current_scales[None, :], innovations)


def joint_draws(paths, selected, origin_index, count=DRAW_COUNT, weighted_distance=None):
    rng = np.random.default_rng(np.random.SeedSequence([SEED, origin_index]))
    selected = np.asarray(selected, int)
    weights = None
    if weighted_distance is not None:
        weights = 1. / (np.asarray(weighted_distance) + 1e-6)
        weights /= weights.sum()
    chosen = rng.choice(selected, size=count, replace=True, p=weights)
    return paths[chosen], chosen


def oracle_search(paths, truth, scales):
    """Exact best one-path plus deterministic eight-step greedy empirical oracle.

    Greedy additions exhaust every eligible origin, using common's biased CRPS
    as the empirical-measure objective. Final scenarios are repeated to 1000
    complete joint draws and rescored with the exact inherited fair estimator.
    This is a hindsight diagnostic, not a proof of the global optimum over all
    conceivable mixtures. Every candidate addition remains a whole scenario.
    """
    n, d = paths.shape
    scores = crps_ensemble(paths.reshape(1, n*d), np.tile(truth, n)).reshape(n, d) / scales
    selected = [int(np.argmin(scores.sum(axis=1)))]
    best = float('inf')
    best_cells = None
    best_selected = None
    curve = []
    for m in range(1, ORACLE_MEMBERS+1):
        if m > 1:
            old = np.broadcast_to(paths[np.asarray(selected)][:, None, :], (m-1, n, d))
            trial = np.concatenate([old, paths[None, :, :]], axis=0)
            loss = crps_ensemble(trial.reshape(m, n*d), np.tile(truth, n), fair=False).reshape(n, d) / scales
            selected.append(int(np.argmin(loss.sum(axis=1))))
        draws = paths[np.asarray(selected)[np.arange(DRAW_COUNT) % m]]
        cells = crps_ensemble(draws, truth) / scales
        score = float(cells.sum())
        curve.append(score)
        if score < best:
            best, best_cells, best_selected = score, cells, list(selected)
    return best_cells, best_selected, curve


def gate1(marginal, full=None):
    return marginal <= .65 and (full is None or full <= .70)


def gate2(summary):
    return all([summary['ratio'] <= .85, summary['equal_year_ratio'] <= .90,
                summary['improved_years'] >= 6, summary['max_year_gross_share'] <= .35,
                summary['max_asset_gross_share'] <= .35, summary['origin_upper95'] < 1,
                summary['random_p'] <= .05])

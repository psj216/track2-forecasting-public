"""Executive summary: reconstruct published M0 inputs, draws and expected-error scales.

This is the documented generator reconstruction, not the unpublished organizer source.
Losses are imported from the pinned official scorer elsewhere, never reimplemented here.
No label file or network is read by this module.
"""
from __future__ import annotations

import json
import math
import pathlib
import tomllib
import zlib
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.special import gamma, hyp1f1
from scipy.stats import norm
from qfbench2_track_forecasting.grid import grid_from_card
from qfbench2_track_forecasting.horizons import monthly_horizon_steps

TAIL_LEVELS = (.01, .05, .95, .99)


@dataclass
class Distribution:
    mean: np.ndarray
    covariance: np.ndarray
    samples: np.ndarray
    cells: tuple
    steps: np.ndarray
    audit: dict


def pair_variance(delta: float, variance: float) -> float:
    if variance <= 0:
        return 0.0
    s = math.sqrt(variance)
    absolute = s * math.sqrt(2 / math.pi) * math.exp(-delta**2 / (2 * variance)) + delta * (1 - 2 * norm.cdf(-delta / s))
    half = math.sqrt(s) * 2**.25 * gamma(.75) / math.sqrt(math.pi) * hyp1f1(-.25, .5, -delta**2 / (2 * variance))
    value = absolute - half**2
    if value < -1e-10 * max(absolute, 1):
        raise ValueError('negative variogram variance')
    return max(0., float(value))


def scales(mean, covariance, levels=TAIL_LEVELS):
    sd = np.sqrt(np.diag(covariance))
    marginal = float(sd.mean() / math.sqrt(math.pi))
    tail = float(norm.pdf(norm.ppf(levels)).mean() * sd.mean())
    joint = sum(pair_variance(float(mean[i]-mean[j]), float(covariance[i,i]+covariance[j,j]-2*covariance[i,j]))
                for i in range(len(mean)) for j in range(len(mean)) if i != j)
    result = dict(marginal=marginal, joint=joint, tail=tail)
    if not all(np.isfinite(v) and v >= 0 for v in result.values()):
        raise ValueError('invalid expected scale')
    return {k: v if v != 0 else 1. for k,v in result.items()}


def target_steps(dates, horizon, target_date):
    if len(dates) < 3 or target_date is None:
        return horizon
    try:
        target = pd.Timestamp(target_date)
    except (TypeError, ValueError):
        return horizon
    if pd.isna(target):
        return horizon
    intervals = np.diff(dates.values).astype('timedelta64[D]').astype(float)
    gap = max(10 * np.median(intervals), 5)
    spacing = intervals[intervals <= gap].mean()
    last = dates[-1]
    steps = (12*(target.year-last.year)+target.month-last.month if spacing > 20
             else round((target-last).days / spacing))
    if steps <= 0:
        return horizon
    return int(steps if max(steps,horizon)/max(min(steps,horizon),1) > 2 else horizon)


def reconstruct(unit: pathlib.Path) -> Distribution:
    unit = pathlib.Path(unit)
    card = tomllib.loads((unit/'card.toml').read_text())
    spec = grid_from_card(card)
    target = card['targets']; typ = target['target_type']
    if typ not in ('level', 'log_return'):
        raise ValueError('unsupported target type')
    cutoff = pd.Timestamp(card['provenance']['data_cutoff'])
    histories, series, anchors, trace = {}, {}, {}, {}
    panels = [(p, pd.read_parquet(p)) for p in sorted(unit.glob('*.parquet'))]
    for asset in sorted(spec.assets):
        selected = None
        for path, frame in panels:
            key = 'asset' if 'asset' in frame else 'asset_id'
            if key not in frame or not (frame[key] == asset).any():
                continue
            selected = frame.loc[frame[key] == asset, ['date','value']].copy()
            source = path.name
            break
        if selected is None:
            raise ValueError('missing asset '+asset)
        selected['date'] = pd.to_datetime(selected['date'], errors='raise')
        selected = selected.loc[selected.date <= cutoff].sort_values('date').tail(300)
        if len(selected) < 3 or selected.date.duplicated().any() or selected.date.isna().any():
            raise ValueError('insufficient or ambiguous history')
        values = selected.value.to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError('nonfinite history')
        dates = pd.DatetimeIndex(selected.date)
        gaps = np.diff(dates.values).astype('timedelta64[D]').astype(float)
        threshold = max(10*np.median(gaps),5)
        valid = gaps <= threshold
        if typ == 'log_return' and np.median(np.abs(values)) >= .2:
            raise ValueError('return tripwire')
        changes = np.diff(values) if typ == 'level' else values[1:]
        series[asset] = pd.Series(changes[valid], index=dates[1:][valid])
        histories[asset] = dates
        anchors[asset] = values[-1] if typ == 'level' else 0.
        trace[asset] = dict(source=source, observations=len(values), retained_steps=int(valid.sum()),
                            last_observation=str(dates[-1].date()), gap_threshold=float(threshold))
    aligned = pd.concat(series, axis=1, join='inner').dropna()
    if len(aligned) < 2:
        raise ValueError('insufficient aligned history')
    assets = list(aligned.columns)
    mu = aligned.mean().to_numpy()
    sigma = np.atleast_2d(np.cov(aligned.to_numpy(), rowvar=False, ddof=1))
    freq = target.get('target_frequency',card.get('metadata',{}).get('target_frequency','daily'))
    forecast_spec = json.loads((unit/'forecast_spec.json').read_text()) if (unit/'forecast_spec.json').exists() else {}
    if freq == 'monthly':
        # Explicit generic metadata only: never hardcode the four practice cards.
        steps = monthly_horizon_steps(spec.assets, spec.horizons,
            {a:str(histories[a][-1].date()) for a in spec.assets}, asof=str(cutoff.date()),
            card=card, forecast_spec=forecast_spec).ravel()
    elif freq in ('daily','business_daily'):
        declared_dates = target.get('target_dates', [None]*len(spec.horizons))
        steps = np.array([target_steps(histories[a],h,declared_dates[j])
                          for a in spec.assets for j,h in enumerate(spec.horizons)])
    else:
        raise ValueError('unsupported cadence')
    indices = [assets.index(a) for a,h in spec.cells()]
    mean = np.array([anchors[a]+s*mu[indices[i]] for i,((a,h),s) in enumerate(zip(spec.cells(),steps))])
    covariance = np.minimum.outer(steps,steps)*sigma[np.ix_(indices,indices)] + np.eye(len(steps))*1.1e-9
    fallback = False
    try:
        factor = np.linalg.cholesky(covariance)
    except np.linalg.LinAlgError:
        covariance = np.diag(np.diag(covariance)); factor = np.linalg.cholesky(covariance); fallback=True
    seed = zlib.crc32(card['task']['id'].encode()) & 0x7fffffff
    samples = mean + np.random.default_rng(seed).standard_normal((500,len(mean))) @ factor.T
    if not np.isfinite(samples).all():
        raise ValueError('nonfinite M0 draws')
    return Distribution(mean,covariance,samples,spec.cells(),steps,
        dict(assets=trace,aligned_rows=len(aligned),seed=seed,diagonal_fallback=fallback,
             mu=mu.tolist(),sigma=sigma.tolist(),frequency=freq))


def hedge(unit, original, *, selection_salt=17):
    """One fixed mixture; fallback depends only on supplied inputs, never a score."""
    original = np.asarray(original)
    card = tomllib.loads((pathlib.Path(unit)/'card.toml').read_text())
    target = card['targets']; freq=target.get('target_frequency',card.get('metadata',{}).get('target_frequency','daily'))
    if freq not in ('daily','business_daily'):
        return original.copy(), {'applied':False,'reason':'daily_only'}
    try:
        spec = grid_from_card(card)
        fx_assets = {'EUR','JPY','GBP','CHF','CAD','AUD','NZD','NOK','SEK','DKK','MXN','BRL','ZAR','KRW','INR'}
        if not all(a.startswith('UST_') or a in fx_assets for a in spec.assets):
            raise ValueError('unsupported asset class')
        params = card.get('scoring',{}).get('params',{})
        if params.get('tail_metric','pinball') != 'pinball' or params.get('joint','variogram') != 'variogram':
            raise ValueError('unsupported scoring contract')
        n = original.shape[0]
        if original.ndim!=2 or original.shape[1]!=spec.cell_count or n%10 or n//10>500 or n<max(200,params.get('n_draws_min',200)) or not np.isfinite(original).all():
            raise ValueError('unsupported output shape or draw count')
        m0 = reconstruct(unit)
        seed = zlib.crc32((card['task']['id']+':M0-HEDGE-10:'+str(selection_salt)).encode()) & 0x7fffffff
        rng = np.random.default_rng(seed)
        old = rng.choice(n,n*9//10,replace=False); new = rng.choice(500,n//10,replace=False)
        permutation = rng.permutation(n)
        mixed = np.concatenate([original[old],m0.samples[new]])[permutation]
        return mixed,dict(applied=True,alpha=.1,seed=seed,ff03_indices=old.tolist(),m0_indices=new.tolist(),permutation=permutation.tolist())
    except (ValueError,KeyError,IndexError,np.linalg.LinAlgError) as exc:
        return original.copy(),dict(applied=False,reason=str(exc))

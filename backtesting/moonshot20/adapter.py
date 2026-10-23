"""One frozen joint distribution transform over the unmodified FF03 entrypoint."""
import argparse
import json
import pathlib
import subprocess
import sys
import tomllib
import numpy as np
import pandas as pd
from qfbench2_track_forecasting import cli


def anchors_for(card, panels, asof):
    targets = card.get('targets', {})
    if targets.get('target_frequency') != 'daily' or targets.get('target_type') != 'level':
        raise ValueError('only explicit daily level contracts')
    if card.get('provenance', {}).get('data_cutoff') != asof:
        raise ValueError('ambiguous cutoff')
    for key in ('target_frequency', 'target_type'):
        if card.get('metadata', {}).get(key, targets[key]) != targets[key]:
            raise ValueError('conflicting contract')
    anchors = {}
    for asset in targets['asset_ids']:
        matches = []
        for frame in panels.values():
            col = cli._asset_col(frame)
            if col and (frame[col].astype(str) == asset).any():
                matches.append(frame)
        if len(matches) != 1:
            raise ValueError('ambiguous asset panel')
        history = cli._series({'panel': matches[0]}, asset, asof)
        dates = pd.DatetimeIndex(pd.to_datetime(history.index))
        if dates.has_duplicates or len(history) < 30 or dates.max() > pd.Timestamp(asof):
            raise ValueError('ambiguous anchor dates')
        gaps = np.diff(dates.values).astype('timedelta64[D]').astype(float)
        if not (0 < np.median(gaps) <= 3):
            raise ValueError('unsupported input cadence')
        value = float(history.iloc[-1])
        if not np.isfinite(value):
            raise ValueError('nonfinite anchor')
        anchors[asset] = value
    return anchors


def transform(frame, anchors, targets, seed):
    draws = np.sort(frame['draw'].unique())
    if len(draws) != 1000:
        raise ValueError('locked candidate requires 1000 joint draws')
    expected = {(a, h) for a in targets['asset_ids'] for h in targets['horizons']}
    if frame.duplicated(['draw', 'asset', 'horizon']).any():
        raise ValueError('duplicate grid')
    for _, block in frame.groupby('draw'):
        if set(zip(block.asset, block.horizon)) != expected:
            raise ValueError('incomplete grid')
    if not np.isfinite(frame.value.to_numpy()).all():
        raise ValueError('nonfinite original')
    selected = np.random.default_rng(seed).permutation(draws)[:700]
    result = frame.copy()
    mask = frame.draw.isin(selected)
    anchor = frame.asset.map(anchors).to_numpy(dtype=float)
    values = frame.value.to_numpy(dtype=float)
    result.loc[mask, 'value'] = anchor[mask] + 0.20 * (values[mask] - anchor[mask])
    if not np.isfinite(result.value.to_numpy()).all():
        raise ValueError('nonfinite transform')
    return result


def main():
    argv = sys.argv[1:]
    # Entire original monthly/text/numeric implementation executes first.
    original = subprocess.run([sys.executable, '/opt/finalfit03/candidate_monthly.py', *argv])
    if original.returncode:
        return original.returncode
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--panels', type=pathlib.Path)
    parser.add_argument('--card', type=pathlib.Path)
    parser.add_argument('--asof')
    parser.add_argument('--out', type=pathlib.Path)
    parser.add_argument('--seed', type=int, default=17)
    args, _ = parser.parse_known_args(argv)
    if '--help' in argv or args.panels is None or args.out is None:
        return 0
    try:
        cp = args.card or next(p for p in [args.panels/'card.toml', args.panels.parent/'card.toml'] if p.is_file())
        card = tomllib.loads(cp.read_text())
        # Bypass before panel loading for monthly/nonlevel contracts.
        if card.get('targets', {}).get('target_frequency') != 'daily' or card['targets'].get('target_type') != 'level':
            print('MOONSHOT20 bypass: non-daily-level contract', file=sys.stderr)
            return 0
        anchors = anchors_for(card, cli._read_panels(args.panels), args.asof)
        frame = pd.read_parquet(args.out)
        result = transform(frame, anchors, card['targets'], args.seed)
    except (ValueError, KeyError, TypeError, OSError, StopIteration, SystemExit) as error:
        print('MOONSHOT20 fallback: ' + str(error), file=sys.stderr)
        return 0
    # Fail visibly on output I/O errors; never hide a partially changed output.
    result.to_parquet(args.out, index=False)
    meta_path = args.out.parent/'forecast_meta.json'
    meta = json.loads(meta_path.read_text())
    meta['forecast_mode'] = 'moonshot20-spike70'
    meta['numeric_experiment'] = '700/1000 joint draws: anchor + 0.20*(FF03-anchor); remaining 300 unchanged'
    meta_path.write_text(json.dumps(meta, indent=2) + '\n')
    with (args.out.parent/'forecast_rationale.md').open('a') as handle:
        handle.write('\nMOONSHOT20-SPIKE70: after FF03 text integration, 700 of 1000 joint scenarios shrink deviations from the last as-of observation to 20%; 300 remain original. High-risk, performance unverified.\n')
    print('MOONSHOT20 applied: 700 joint scenarios; scale=0.20; no performance evaluation', file=sys.stderr)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

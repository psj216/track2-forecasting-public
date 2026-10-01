"""## Executive summary (read this first)

Freeze private source/label/baseline hashes and public coverage metadata.
No candidate score is computed. Realized labels stay outside Git.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from collections import Counter
import pandas as pd
from .source_audit import manifest
from .build_market_extension import historical_market, extension_status


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def freeze(root, private):
    results = root / 'backtesting/surprise01/results'
    meta = json.loads((private / 'training_manifest.json').read_text())
    events = json.loads((private / 'events.json').read_text())
    errors = json.loads((private / 'parse_errors.json').read_text())
    series, kinds = historical_market(root)
    market = []
    for a, s in series.items():
        raw = s.to_csv(float_format='%.17g', lineterminator='\n').encode()
        market.append({'asset': a, 'kind': kinds[a], 'rows': len(s),
                       'first': str(s.index.min().date()), 'last': str(s.index.max().date()),
                       'sha256': hashlib.sha256(raw).hexdigest(), 'extension_2025': False,
                       'unit': 'inherited native panel unit, no conversion',
                       'frequency': 'daily', 'calendar': 'observed dates, business-day horizons',
                       'source': ('Federal Reserve Board H.15' if a.startswith('UST_') else
                                  'French/AQR inherited factor panel' if kinds[a]=='log_return' else
                                  'Unverified inherited EM panel' if a in ('BRL','INR','CNY') else
                                  'Federal Reserve Board H.10')})
    tests = {}
    for name in ('all_tests', 'surprise_tests'):
        p = private / (name + '.xml')
        suite = ET.parse(p).getroot()[0]
        a = suite.attrib
        if int(a['failures']) or int(a['errors']):
            raise ValueError('Cannot freeze with failing tests')
        tests[name] = {'tests': int(a['tests']), 'skipped': int(a['skipped']),
                       'failures': int(a['failures']), 'errors': int(a['errors']), 'sha256': digest(p)}
    source = manifest(private / 'archive_manifest.json')
    source['parse_exclusions'] = [{k: r[k] for k in ('kind','key','url','error') if k in r} for r in errors]
    source['market_audit'] = market
    source['final_feasibility'] = extension_status()
    write(results / 'source_manifest.json', source)
    event = {'sha256': digest(private / 'events.json'), 'rows': len(events),
             'families': dict(Counter(e['event_type'] for e in events)),
             'first_release': min(e['release_date'] for e in events),
             'last_release': max(e['release_date'] for e in events),
             'timestamp_verified': sum(e['release_timestamp'] is not None for e in events),
             'parse_exclusions': len(errors), 'true_consensus_events': 0,
             'information_type': 'RELEASE_INNOVATION', 'training_coverage': meta}
    write(results / 'event_manifest.json', event)
    frozen = {**meta, 'event_sha256': event['sha256'],
              'raw_manifest_sha256': source['raw_manifest_sha256'],
              'market': market, 'final_feasibility': extension_status(),
              'draw_cache_sha256': {p.name: digest(p) for p in sorted((private/'draw_cache').glob('*.npz'))},
              'ocr_sha256': {p.name: digest(p) for p in sorted((private/'raw/retail').glob('*.ocr.txt'))},
              'tests': tests, 'python': sys.version,
              'packages': {n: importlib.metadata.version(n) for n in ('numpy','pandas','scipy','pyarrow','qfbench2-common','requests','beautifulsoup4','pypdf','fonttools')}}
    write(results.parent / 'frozen_inputs.json', frozen)
    print(json.dumps({'source_archives': len(source['sources']), 'event_rows': len(events),
                      'case_rows': meta['cases'], 'baseline_caches': len(frozen['draw_cache_sha256']),
                      'final_status': 'NO_INDEPENDENT_FINAL_HOLDOUT'}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, default=Path.cwd())
    p.add_argument('--private-root', type=Path, required=True)
    a = p.parse_args()
    freeze(a.root, a.private_root)

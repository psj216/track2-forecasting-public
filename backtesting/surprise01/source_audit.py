"""## Executive summary (read this first)

Inspect dated agency archives, hash private raw bytes, and retain acquisition errors.
No market outcome or score is read by this source-audit utility.
"""

import hashlib
import json
from pathlib import Path


def manifest(raw_manifest: Path):
    data = json.loads(raw_manifest.read_text())
    return {"sources": [{k: row[k] for k in ("kind", "key", "url", "retrieval_url", "sha256", "bytes", "status")
                         if k in row} for row in data],
            "raw_manifest_sha256": hashlib.sha256(raw_manifest.read_bytes()).hexdigest(),
            "retrieval_date": "2026-10-01",
            "consensus_available": False,
            "information_type": "RELEASE_INNOVATION"}


def collect(private_root, first_year=1998, last_year=2024):
    """Download the precommitted agency archive universe, never market outcomes."""
    import concurrent.futures
    import re
    from urllib.parse import urljoin
    import requests
    from bs4 import BeautifulSoup
    private_root = Path(private_root)
    private_root.mkdir(parents=True, exist_ok=True)
    index = {'cpi': 'https://www.bls.gov/bls/news-release/cpi.htm',
             'employment': 'https://www.bls.gov/bls/news-release/empsit.htm',
             'ip': 'https://www.federalreserve.gov/Releases/g17/',
             'retail': 'https://www.census.gov/retail/marts/historic_releases.html'}
    items = []
    for kind, url in index.items():
        response = requests.get(url, timeout=45)
        response.raise_for_status()
        (private_root / (kind + '_index.html')).write_bytes(response.content)
        by_date = {}
        for a in BeautifulSoup(response.content, 'html.parser').find_all('a', href=True):
            u = urljoin(url, a['href'])
            if kind in ('cpi', 'employment'):
                m = re.search(r'(cpi|empsit)_(\d{2})(\d{2})(\d{4}|\d{2})\.(htm|txt)$', u)
                if not m:
                    continue
                yyyy = int(m[4])
                if yyyy < 100:
                    yyyy += 2000 if yyyy < 50 else 1900
                key = f'{yyyy}-{m[2]}-{m[3]}'
            elif kind == 'ip':
                m = re.search(r'/g17/(\d{4})(\d{2})(\d{2})/(?:default\.htm)?$', u, re.I)
                if not m:
                    continue
                yyyy, key = int(m[1]), f'{m[1]}-{m[2]}-{m[3]}'
            else:
                m = re.search(r'/adv(\d{2})(\d{2})\.pdf$', u)
                if not m:
                    continue
                yyyy = 2000 + int(m[1]) if int(m[1]) < 50 else 1900 + int(m[1])
                key = f'{yyyy}-{m[2]}'
            if first_year <= yyyy <= last_year:
                by_date[key] = dict(kind=kind, key=key, url=u)
        items.extend(by_date.values())
    (private_root / 'requested_archives.json').write_text(json.dumps(items, indent=2) + '\n')

    def acquire(row):
        ext = 'pdf' if row['kind'] == 'retail' else ('txt' if row['url'].endswith('.txt') else 'html')
        path = private_root / 'raw' / row['kind'] / (row['key'] + '.' + ext)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            raw = path.read_bytes() if path.exists() else b''
            def usable(data):
                return len(data) >= 100 and (ext != 'pdf' or data.startswith(b'%PDF'))
            retrieval_url = row['url']
            if not usable(raw):
                response = requests.get(row['url'], timeout=35)
                response.raise_for_status()
                raw = response.content
                if not usable(raw):
                    retrieval_url = row['url'] + '?download=1'
                    response = requests.get(retrieval_url, timeout=35)
                    response.raise_for_status()
                    raw = response.content
                path.write_bytes(raw)
            if not usable(raw):
                raise ValueError('Empty or invalid archive response')
            return {**row, 'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(),
                    'retrieval_url': retrieval_url, 'bytes': len(raw), 'status': 'OK'}
        except Exception as e:
            return {**row, 'path': str(path), 'status': 'ERROR', 'error': str(e)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(acquire, items))
    output = private_root / 'archive_manifest.json'
    output.write_text(json.dumps(rows, indent=2) + '\n')
    return manifest(output)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--private-root', type=Path, required=True)
    p.add_argument('--public-manifest', type=Path, required=True)
    a = p.parse_args()
    result = collect(a.private_root)
    a.public_manifest.parent.mkdir(parents=True, exist_ok=True)
    a.public_manifest.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'archives': len(result['sources']), 'consensus_available': False}))

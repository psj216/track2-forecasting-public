"""Executive summary: original ECB point fields and conservative as-of states only.

No outcomes, model fitting or scores are imported. Original and amended versions
are distinct availability events; later corrections never overwrite earlier rows.
"""
import argparse
import csv
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from .source_acquisition import OUT, ROOT, digest, dump, enumerate_archive, write_csv

FEATURES = ('HICP_NCY', 'GDP_NCY', 'HICP_NCY_REV_SAME_TARGET',
            'GDP_NCY_REV_SAME_TARGET', 'SOURCE_AGE_BUSINESS_DAYS')


def parse_table(text, round_id):
    """Read the headline SPF rows under explicit calendar-year columns, never core HICP."""
    year, quarter = int(round_id[:4]), int(round_id[-1])
    lines = text.replace('\u2212', '-').replace('\xa0', ' ').splitlines()
    row_re = re.compile(rf'^\s*(?:SPF\s+Q{quarter}\s+{year}|Q{quarter}\s+{year}\s+SPF)\s+(.+)$')
    result = []
    for variable, heading in [('HICP', 'HICP inflation'), ('GDP', 'Real GDP growth')]:
        candidates = []
        for i, line in enumerate(lines):
            if not re.match(r'^\s*' + heading + r'(?:\s+20\d\d|\s*$)', line):
                continue
            years = None
            # Early reports repeat columns on the variable heading; later reports share a header.
            for header in [line] + list(reversed(lines[max(0, i-55):i])):
                yy = re.findall(r'\b20\d{2}\b', header)
                if len(yy) >= 3 and list(map(int, yy[:3])) == [year, year+1, year+2]:
                    years = list(map(int, yy[:3])); break
            if years is None:
                continue
            for j in range(i+1, min(i+9, len(lines))):
                match = row_re.match(lines[j])
                if match:
                    tokens = match[1].split()
                    if len(tokens) < 3:
                        raise ValueError('Truncated calendar row: ' + round_id)
                    values = [float(v) for v in tokens[:3]]
                    previous = None
                    for k in range(j+1, min(j+7, len(lines))):
                        if re.match(r'^\s*Previous SPF\b', lines[k]):
                            tail = lines[k].split(')', 1)[1].split()
                            previous = [None if v in ('-', '–') else float(v) for v in tail[:3]]
                            break
                    candidates.append((years, values, previous, j+1, text[:text.find(lines[j])].count('\f')+1, lines[j].strip()))
                    break
        if len(candidates) != 1:
            raise ValueError(f'{round_id} {variable}: expected one headline table row, found {len(candidates)}')
        years, values, previous, line_no, page, raw = candidates[0]
        for column, (target, value) in enumerate(zip(years, values)):
            result.append({'round_id': round_id, 'variable': variable, 'target_calendar_year': target,
                           'point_forecast': value, 'unit': 'annual_percentage_change',
                           'field_semantics': 'current-round headline SPF mean point forecast',
                           'pdf_page': page, 'text_line': line_no, 'raw_row': raw,
                           'retrospective_previous_value': '' if previous is None or previous[column] is None else previous[column]})
    return result


def activation(date):
    return pd.Timestamp(str(date) + ' 23:59:59', tz='Europe/Berlin').tz_convert('UTC')


def origin_cutoff(origin):
    previous = pd.Timestamp(origin) - pd.offsets.BDay(1)
    return previous.tz_localize('America/New_York') + pd.Timedelta(hours=16)


def same_target_revision(current, previous, variable, target):
    key = (variable, int(target))
    return None if previous is None or key not in previous else current[key] - previous[key]


def release_states(universe, fields):
    by_round = {}
    for row in fields:
        by_round.setdefault(row['round_id'], {})[(row['variable'], int(row['target_calendar_year']))] = float(row['point_forecast'])
    previous = None
    states = []
    for release in universe:
        current = by_round[release['round_id']]
        target = int(release['year']) + 1
        revisions = [same_target_revision(current, previous, v, target) for v in ('HICP', 'GDP')]
        states.append({'round_id': release['round_id'], 'publication_date': release['publication_date'],
                       'available_at': activation(release['publication_date']).isoformat(),
                       'target_calendar_year': target, 'HICP_NCY': current[('HICP', target)],
                       'GDP_NCY': current[('GDP', target)],
                       'HICP_NCY_REV_SAME_TARGET': revisions[0], 'GDP_NCY_REV_SAME_TARGET': revisions[1],
                       'eligible': all(v is not None for v in revisions)})
        previous = current
    return states


def asof_features(states, origin):
    cutoff = origin_cutoff(origin).tz_convert('UTC')
    known = [s for s in states if pd.Timestamp(s['available_at']) <= cutoff]
    if not known:
        return None
    state = max(known, key=lambda s: s['available_at'])
    # Latest release cannot be skipped in favour of an older complete release.
    if not state['eligible']:
        return None
    cutoff_local = cutoff.tz_convert('Europe/Berlin').date()
    age = int(np.busday_count(state['publication_date'], cutoff_local.isoformat()))
    if age > 90:
        return None
    return {**state, 'SOURCE_AGE_BUSINESS_DAYS': age}


def build(private):
    cache = private / 'source_cache'
    universe = enumerate_archive((cache / 'all-releases.html').read_bytes())
    fields, publications, errata, receipts, retrospective = [], [], [], [], []
    previous = None
    for number, row in enumerate(universe, 1):
        round_id = row['round_id']; pdf = cache / (round_id + '.pdf')
        receipt = json.loads((cache / (round_id + '.pdf.receipt.json')).read_text())
        if receipt['status'] != 'OK' or digest(pdf) != receipt['sha256']:
            raise ValueError('Source receipt mismatch ' + round_id)
        txt = cache / (round_id + '.txt')
        if not txt.exists():
            subprocess.run(['pdftotext', '-layout', str(pdf), str(txt)], check=True, timeout=30, capture_output=True)
        text = txt.read_text(); parsed = parse_table(text, round_id)
        for f in parsed:
            f.update(source_sha256=receipt['sha256'], official_url=row['pdf_url'], extraction_status='VERIFIED_TABLE_ROW')
            if f['retrospective_previous_value'] != '' and previous is not None:
                key = (f['variable'], f['target_calendar_year'])
                if key in previous:
                    retrospective.append({'round_id': round_id, 'variable': key[0], 'target_year': key[1],
                        'matches_preceding_original': abs(float(f['retrospective_previous_value']) - previous[key]) < 1e-10,
                        'previous_original': previous[key], 'retrospective_value': f['retrospective_previous_value']})
        previous = {(f['variable'], f['target_calendar_year']): f['point_forecast'] for f in parsed}
        fields.extend(parsed)
        meta_date = ''; html_text = ''; notices = []
        if row['html_url']:
            html = cache / (round_id + '.html')
            html_receipt = json.loads((cache / (round_id + '.html.receipt.json')).read_text())
            if digest(html) != html_receipt['sha256']:
                raise ValueError('HTML hash mismatch')
            soup = BeautifulSoup(html.read_bytes(), 'html.parser')
            meta = soup.find('meta', attrs={'property': 'article:published_time'})
            if meta:
                meta_date = meta['content'][:10]
                if meta_date != row['publication_date']:
                    raise ValueError('Publication metadata discrepancy ' + round_id)
            main = soup.find('main') or soup
            html_text = main.get_text(' ', strip=True)
            receipts.append({'round_id': round_id, 'kind': 'html', 'sha256': html_receipt['sha256'], 'official_url': row['html_url']})
        for body in (text, html_text):
            for match in re.finditer(r'\b(?:errat(?:um|a)|corrigendum|amended table|corrected (?:table|version|figure|value)|replacement spreadsheet)\b', body, re.I):
                notices.append(body[max(0, match.start()-100):match.end()+200])
        publications.append({'round_id': round_id, 'publication_date': row['publication_date'],
             'available_at': activation(row['publication_date']).isoformat(), 'intraday_known': False,
             'evidence_hierarchy': 2 if not meta_date else 3, 'archive_evidence': row['publication_evidence'],
             'html_publication_metadata': meta_date, 'timing_status': 'VERIFIED_DATE_CONSERVATIVE_EOD',
             'response_date_used': False, 'creation_time_used': False})
        errata.append({'round_id': round_id, 'notice_count': len(notices),
             'status': 'UNRESOLVED_NOTICE' if notices else 'NO_AMENDMENT_NOTICE_FOUND_IN_ORIGINAL_DOCUMENT',
             'notice_context': json.dumps(notices), 'historical_immutability_proven': False,
             'scope': 'Full original PDF and matching HTML; preceding-round headline table consistency',
             'pit_grade': 'B', 'rights': 'ECB attribution; private research preservation; derived values labelled'})
        receipts.append({'round_id': round_id, 'kind': 'pdf', 'sha256': receipt['sha256'], 'official_url': row['pdf_url']})
        print(f'stage=source_field_audit completed={number}/{len(universe)} round={round_id} output={OUT}', flush=True)
    states = release_states(universe, fields)
    write_csv(OUT / 'ecb_publication_ledger.csv', publications)
    write_csv(OUT / 'ecb_field_ledger.csv', fields)
    write_csv(OUT / 'ecb_errata_ledger.csv', errata)
    dump(private / 'source_states.json', {'states': states})
    dump(private / 'retrospective_consistency.json', {'comparisons': retrospective})
    unresolved = [r for r in errata if r['notice_count']]
    mismatches = [r for r in retrospective if not r['matches_preceding_original']]
    manifest = {'rounds_enumerated': len(universe), 'extracted_fields': len(fields),
        'usable_releases_before_age_filter': sum(s['eligible'] for s in states),
        'same_target_revision_events': sum(s['eligible'] for s in states),
        'field_revision_count': 2*sum(s['eligible'] for s in states), 'receipts': receipts,
        'parser_sha256': digest(__file__), 'archive_sha256': digest(cache / 'all-releases.html'),
        'retrospective_comparisons': len(retrospective), 'retrospective_mismatches': mismatches,
        'unresolved_amendment_notices': unresolved, 'historical_immutability_proven': False,
        'PIT': 'B; official original-round representations, no immutable historical hashes claimed',
        'current_history_csv_used': False, 'microdata_used': False, 'outcomes_loaded': False,
        'DATASET_READY': not unresolved and not mismatches}
    dump(OUT / 'ecb_pit_dataset_manifest.json', manifest)
    dump(OUT / 'ecb_dataset_readiness.json', {'DATASET_READY': manifest['DATASET_READY'],
         'critical_failures': ['unresolved amendment or preceding-round discrepancy'] if unresolved or mismatches else [],
         'source_statistics': {k: manifest[k] for k in ['rounds_enumerated', 'extracted_fields', 'usable_releases_before_age_filter', 'same_target_revision_events']},
         'pre_outcome_gate': True, 'model_fits': 0, 'forecast_scores': 0,
         'pending_checks': ['source tests', 'deterministic reconstruction', 'coverage']})
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--private', type=Path, required=True)
    build(parser.parse_args().private)

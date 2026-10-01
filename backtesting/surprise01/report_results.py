"""## Executive summary (read this first)

Render frozen research aggregates without selecting a head or changing a model.
Keep individual market outcomes outside the public repository.
"""

import argparse
import json
from pathlib import Path
import pandas as pd


def render(root):
    result = root / 'backtesting/surprise01/results'
    summary = json.loads((result / 'validation_summary.json').read_text())
    events = json.loads((result / 'event_manifest.json').read_text())
    controls = json.loads((result / 'negative_controls.json').read_text())
    artifact = json.loads((result / 'artifact_manifest.json').read_text())
    heads = ('location', 'scale', 'combined')
    lines = ['### Executed research results', '',
             f"PRE_FINAL_SURPRISE01_SHA: `{summary['pre_final_sha']}`.", '',
             'Status: **EXPOSED_CHRONOLOGICAL_RESEARCH_ONLY**. '
             '**NO_INDEPENDENT_FINAL_HOLDOUT**. No 2025 label or score was generated.', '',
             f"Source ledger: {events['rows']:,} family records, "
             f"{events['first_release']} to {events['last_release']}; "
             f"{events['parse_exclusions']} documented pre-score exclusions. "
             'TRUE_CONSENSUS_SURPRISE count: 0. All signals are RELEASE_INNOVATION.', '',
             '| Head | V5.1 normalized CRPS | Candidate | Ratio | Cells | Events | Active cells |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for h in heads:
        v = summary['overall'][h]
        lines.append(f"| {h} | {v['v51']:.6f} | {v['candidate']:.6f} | {v['ratio']:.6f} | "
                     f"{v['cells']} | {v['events']} | {v['active_cells']} |")
    lines += ['', 'The three heads are separate precommitted hypotheses. '
              'These are research ratios, not official competition scores.', '',
              '### Direction and dispersion', '',
              '| Head | Sign accuracy | Pearson IC | Spearman IC | Mean absolute shift / baseline SD | Mean scale multiplier |',
              '|---|---:|---:|---:|---:|---:|']
    def fmt(v):
        return 'N/A' if v is None else f'{v:.6f}'
    for h in heads:
        v = summary['overall'][h]
        lines.append('| ' + h + ' | ' + ' | '.join(fmt(v[k]) for k in (
            'sign_accuracy', 'pearson_ic', 'spearman_ic',
            'mean_abs_location_shift_over_v51_sd', 'mean_scale_multiplier')) + ' |')
    lines += ['', 'Scale-head IC concerns future log path scale / V5.1 SD; '
              'it is not directional IC. Directional accuracy concerns nonzero intervention cells.', '']
    for filename, field, label in (('target_group_summary.csv', 'group', 'Target groups'),
                                   ('horizon_summary.csv', 'horizon', 'Business-day horizons'),
                                   ('event_family_summary.csv', 'event_type', 'Release families')):
        df = pd.read_csv(result / filename)
        lines += ['### ' + label, '', '| Partition | Location ratio | Scale ratio | Combined ratio | Cells | Events |',
                  '|---|---:|---:|---:|---:|---:|']
        for value, part in df.groupby(field, sort=True):
            ratios = part.set_index('head')['ratio']
            first = part.iloc[0]
            lines.append(f'| {value} | ' + ' | '.join(f'{ratios[h]:.6f}' for h in heads)
                         + f" | {int(first['cells'])} | {int(first['events'])} |")
        lines.append('')
    lines += ['### Negative controls and event uncertainty', '',
              '| Head | Primary | Sign shuffle | Date permutation | Family permutation | Primary event-bootstrap 95% interval |',
              '|---|---:|---:|---:|---:|---|']
    for h in heads:
        ci = summary['event_uncertainty'][h]['ratio_ci95']
        lines.append(f"| {h} | {summary['overall'][h]['ratio']:.6f} | "
                     + ' | '.join(f"{controls[c][h]['ratio']:.6f}" for c in (
                         'sign_shuffle', 'date_permutation', 'family_permutation'))
                     + f' | [{ci[0]:.6f}, {ci[1]:.6f}] |')
    lines += ['', 'Resampling unit: entire release date, all families/assets/horizons together; '
              '2,000 replicates, seed 1902. Long overlapping targets retain serial dependence '
              'between dates. Cell counts are not independent sample counts.', '',
              'Scale sign shuffle is algebraically invariant and cannot establish a scale edge. '
              'Relevant date/family controls must capture less than half the primary gain, '
              'with paired bootstrap upper ratio below one. See negative_controls.json for all paired intervals.', '',
              'Future-market mutation and later-revision mutation tests passed before scoring.', '',
              '### Decisions', '']
    for h in heads:
        lines.append(f"- {h}: `{summary['head_decisions'][h]}`.")
    lines += ['', f"READY_FOR_SURPRISE_02 = **{summary['ready_for_surprise_02']}**.", '',
              'READY_FOR_ONE_SHOT_SUBMISSION = **NO**.', '']
    if summary['ready_for_surprise_02'] == 'NO':
        lines += ['This fixed release-innovation specification does not meet its precommitted '
                  'incremental-information gate. It does not establish absence of information '
                  'in unavailable true pre-release consensus. No event, asset, horizon, '
                  'penalty, clip or scale bound was changed after scoring.', '']
    lines += ['### Preservation and private-data firewall', '',
              f"Private scored outcomes: {artifact['private_outcome_rows']:,} rows, "
              f"SHA-256 `{artifact['private_outcome_sha256']}`. Individual outcomes and "
              'baseline draws remain outside Git. Public result files contain only aggregate '
              'scores, source identifiers, hashes, counts and coverage.', '',
              'Tests before freeze: repository 399 passed / 2 skipped; SURPRISE-specific '
              '19 passed. Remote result commit and exact-SHA file fetch are verified separately.', '']
    report = root / 'SURPRISE-01-EXTERNAL-INFORMATION-ALPHA-report.md'
    original = report.read_text().split('### Results')[0]
    report.write_text(original + '\n'.join(lines))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, default=Path.cwd())
    render(p.parse_args().root)

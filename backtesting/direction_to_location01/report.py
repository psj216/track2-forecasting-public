"""Executive summary: render the frozen primary verdict and all required exposed-study evidence."""
import argparse, json
from pathlib import Path
import pandas as pd
from .core import *

def table(rows,columns):
    def value(v):
        if v is None:return 'N/A'
        if isinstance(v,(int,float)):return f'{v:.6f}'
        return str(v)
    return '\n'.join(['| '+' | '.join(label for _,label in columns)+' |','| '+' | '.join('---' for _ in columns)+' |']+['| '+' | '.join(value(r[k]) for k,_ in columns)+' |' for r in rows])

def run(private):
    p=Path(private);verify_pre(p);primary=json.loads((OUT/'primary_summary.json').read_text());secondary=json.loads((OUT/'secondary_sensitivity.json').read_text());decision=json.loads((OUT/'final_decision.json').read_text());oracle=json.loads((OUT/'oracle_summary.json').read_text());boot=json.loads((OUT/'bootstrap_summary.json').read_text());null=json.loads((OUT/'negative_controls.json').read_text());conc=json.loads((OUT/'concentration_summary.json').read_text());year23=json.loads((OUT/'year2023_audit.json').read_text());dep=json.loads((OUT/'release_dependence.json').read_text());rel=primary['release_balanced_primary']['frozen_source_direction'];rows=[]
    for name in ['V5.1',PRIMARY,'DTL_005','DTL_020','OOD3_DIAGNOSTIC','PERFECT_LOCATION_ORACLE']:
        if name in primary['models']:s=primary['models'][name]
        elif name in secondary['models']:s=secondary['models'][name]
        else:s={'crps_ratio':oracle['R_ORACLE'],'oracle_capture':1.}
        rows.append(dict(model=name,ratio=s['crps_ratio'],capture=s['oracle_capture'],release_direction=rel['sign_accuracy'] if name not in ['V5.1','PERFECT_LOCATION_ORACLE'] else None,release_rank=rel['spearman'] if name not in ['V5.1','PERFECT_LOCATION_ORACLE'] else None))
    years=pd.read_csv(OUT/'year_summary.csv');horizons=pd.read_csv(OUT/'horizon_summary.csv');assets=pd.read_csv(OUT/'asset_summary.csv');spec=json.loads((OUT/'experiment_spec.json').read_text())
    text=f'''## Executive summary (read this first)

# DIRECTION-TO-LOCATION-01 — Conservative directional location translation

Primary verdict: **{decision['DTL01_RESULT']}**. Next axis: **{decision['NEXT']}**. Primary is exactly frozen SPD sign × **0.10** × original V5.1 SD. Secondary 0.05/0.20 and OOD3 do not select an amplitude or change this verdict. READY_FOR_SUBMISSION=false. No Development service was called and no submission was packaged.

## Frozen parent, direction and universe

Parent RESULT `{PARENT}`. LOCATION04 RESULT `{LOCATION04_RESULT}`, PRE `2e356b91dd98dae022b72494ea6d4c70a9a38ed7`. DTL PRE `{decision['PRE_RESULT_DTL01_SHA']}` was committed, pushed and remotely verified before any candidate CRPS. The original primary ratio, hashes and cell/release direction metrics reproduce within 1e-12. All original 552 cells, 59 forecast origins and 41 release IDs stay in scope: UST 2Y/5Y, five business-day horizons and original 2020–2024 folds. 2023 remains included.

All historical outcomes and the earlier fixed-sign curves were already exposed. 0.10 was specified by the user before this evaluation; 0.20 is not selected from the prior best curve. This is RESEARCH_EXPOSED, not independent OOS. Identical same-ledger fixed translations should reproduce earlier descriptive scores; this rerun is not new validation.

The original UST yield-level target, publication/PIT rules, 70-weekday expiry, past normalization scale, chronological purges and 2024-12-18 maturity cutoff remain unchanged. No SPD fit, V5.1 reconstruction, feature change, classifier or scale/tail/copula/rank change occurs. Draws and realized targets/cell losses are private.

## Overall primary and secondary scores

{table(rows,[('model','Model'),('ratio','CRPS ratio'),('capture','Oracle capture'),('release_direction','Frozen source release direction'),('release_rank','Frozen source release Spearman')])}

The direction/rank columns describe the preserved continuous SPD prediction, not a newly fitted direction model. OOD3 uses that same source but abstains on extreme train-standardized states. The future-informed oracle has no predictive direction metric; its capture1 is mathematical by construction, not alpha. Baseline has no SPD direction shift. Scoring imports pinned qfbench2-common v2.4.3 fair CRPS and retains each original past-scale divisor; ratios use sums of cell losses. This is research marginal CRPS, not the official multi-card composite.

## Annual primary breakdown

{table(years.loc[years.balance=='cell'].to_dict('records'),[('group','Year'),('crps_ratio','Primary ratio'),('oracle_capture','Capture'),('cells','Cells'),('releases','Releases')])}

## Horizon and asset breakdown

{table(horizons.loc[horizons.balance=='cell'].to_dict('records'),[('group','Business-day horizon'),('crps_ratio','Primary ratio'),('oracle_capture','Capture'),('cells','Cells')])}

{table(assets.loc[assets.balance=='cell'].to_dict('records'),[('group','Asset'),('crps_ratio','Primary ratio'),('oracle_capture','Capture'),('cells','Cells')])}

Release-balanced versions and all release aggregates remain in the CSV artifacts. No favorable subgroup replaces the complete primary ledger.

## 2023 safety audit, fully retained

2023 primary ratio {year23['crps_ratio']:.6f}; original full-magnitude SPD ratio {year23['original_full_SPD_ratio']:.6f}. Cell direction accuracy {year23['frozen_source_direction']['sign_accuracy']:.6f}, release accuracy {year23['release_balanced']['frozen_source_direction']['sign_accuracy']:.6f}. Cells {year23['cells']}, releases {year23['releases']}; OOD fraction {year23['OOD_fraction']:.6f}. Mean raw shift {year23['mean_raw_location_shift']:.6f}, mean absolute raw shift {year23['mean_abs_raw_location_shift']:.6f}. Its normalized total score delta is {year23['total_primary_score_delta']:.6f} and signed share of overall delta {year23['fraction_overall_primary_score_delta']:.6f}. Positive damage can coexist with net overall improvement; that share is not a positive-gain concentration measure. No 2023-excluded score is promoted or produced.

## Paired release and year block bootstrap

'''
    for block in ['release','year']:
        b=boot['blocks'][block];v=b['models'][PRIMARY];text+=f"{block}: {b['blocks']} blocks, {b['replicates']} replicates. Primary CRPS 95% CI `{v['crps_ratio_95ci']}`; ratio delta vs V5.1 `{v['delta_ratio_vs_V51_95ci']}`; mean normalized CRPS delta `{v['mean_normalized_CRPS_delta_95ci']}`; oracle capture `{v['oracle_capture_95ci']}`.\n\n"
    text+='All original assets/horizons of each sampled block stay together. Predictions are fixed; bootstrap does not refit direction. There is no naive IID-cell bootstrap. Five years and 41 related releases remain a small exposed information sample. Resampling does not create independent data.\n\n## Negative controls\n\n'
    for kind,data in null['controls'].items():text+=f"{kind}: `{data}`.\n\n"
    text+=f"Mutation checks: `{null['mutations']}`. Each stochastic control has exactly 2,000 fixed-seed replicates and the same 0.10 SD nonzero magnitude. Release packets are shuffled inside asset/horizon coverage strata, with nearest pre-outcome age matching; the release-shuffle null intentionally destroys historical association and is not a deployable PIT forecast. The date control permutes nonnegative activation delays and reuses only earlier frozen directions; it never backdates publication. It is a **safe delayed-mapping null**, not a literal unrestricted date permutation. Missing dated/prior-year donors receive zero shift on the unchanged full ledger, and coverage is reported. Random sign preserves exact cellular sign prevalence. These definitions were frozen before DTL scoring and are not selected after the outcome.\n\n## Concentration and repeated information\n\nNONCONCENTRATED={conc['NONCONCENTRATED']}.\n\n"
    for field,s in conc['dimensions'].items():text+=f"{field}: leave-one-block ratio range {s['leave_one_out_ratio_range']}; largest gross positive block gain share {s['largest_positive_gain_share']:.6f}; every deletion stays <1: {s['all_leave_one_out_below_baseline']}.\n\n"
    text+=f"{dep['unique_releases']} release IDs, not 552 independent information events. Share of cells in releases repeated across origins {dep['cells_sharing_releases_across_origins_fraction']:.6f}. Origins/release `{dep['origins_per_release']}`; cells/release `{dep['cells_per_release']}`. Original releases are not proven IID. No influential release, asset, horizon or year is removed from the primary.\n\n## Frozen primary gates and next axis\n\nDecision gate evidence: `{decision['primary_gates']}`. Secondary lead status: `{decision['secondary_lead_status']}`. Exactly one next axis: **{decision['NEXT']}**, not executed here. The full gate specification is experiment_spec.json. There is no analyst override, amplitude optimization, primary replacement or post-score scientific redesign. If the primary fails, no favorable secondary rescues it.\n\nA positive result means only that frozen SPD direction with the user-fixed small translation improves V5.1 on this exposed ledger. It does not validate the old SPD magnitude model, independent alpha, an official score, or a submission.\n\n## Verification and recovery\n\nResearch-specific, affected, full repository and pinned common-toolkit tests, protected parent file hashes, PRE/RESULT lineage, remote critical files, unchanged main and clean tree are recorded in execution_audit.json and the external completion receipt. The private recovery ZIP includes frozen inputs, candidate shifts/cell scores, null/bootstrap chunks, code/tests, report, STATUS and Git metadata, with CRC, member SHA256 and full archive SHA256 verification. The external receipt avoids circular commit/archive hashes.\n"
    (ROOT/'DIRECTION-TO-LOCATION-01-report.md').write_text(text);status('report',str(ROOT/'DIRECTION-TO-LOCATION-01-report.md'));print('REPORT rendered',flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private',type=Path,required=True);v=a.parse_args();run(v.private)

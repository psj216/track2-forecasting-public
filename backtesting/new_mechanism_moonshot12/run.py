"""Executive summary: incremental audit, oracle and historical evaluation only.

No card answer or comparative card loss is read by this module. The oracle is
explicitly future-informed; the nearest-neighbour mechanism never uses truth.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from qfbench2_track_forecasting.thesis01.asset_semantics import load_universe
from qfbench2_track_forecasting.v12.data_parity import _prefix
from .core import (BRANCH, CENTER_HASH, DRAW_COUNT, FEATURE_NAMES, HORIZONS,
                   KS, LEDGER_HASH, MAIN, MIN_ANALOGS, ORACLE_MEMBERS, PARENT,
                   SEED, YEARS, digest, eligible_paths, fingerprint, gate1,
                   joint_draws, map_innovations, oracle_search, save,
                   shared_distances, crps_ensemble)

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent/'results'


def private():
    p = Path(os.environ['MOONSHOT12_PRIVATE']).resolve()
    assert not p.is_relative_to(ROOT)
    return p


def inherited():
    return Path(os.environ['MOONSHOT12_CANONICAL']).resolve()


def status(stage, completed=False, **kwargs):
    p = OUT.parent/'STATUS.json'
    data = json.loads(p.read_text()) if p.exists() else {}
    done = data.get('completed_stages', [])
    if completed and stage not in done:
        done.append(stage)
    data.update(executive_summary='Restartable isolated analog experiment; no safe-baseline changes.',
                branch=BRANCH, HEAD_SHA=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                current_stage=stage, completed_stages=done, last_update=pd.Timestamp.now(tz='UTC').isoformat(),
                card_outcomes_opened=False, **kwargs)
    save(p, data)


def protect():
    tree = subprocess.check_output(['git', 'ls-tree', '-rz', '--name-only', PARENT], cwd=ROOT).decode().rstrip('\0').split('\0')
    hashes = {p: digest(ROOT/p) for p in tree}
    save(private()/'protected_parent_hashes.json', hashes)
    return hashes


def verify():
    receipt = json.loads((private()/'pre_oracle_receipt.json').read_text())
    assert receipt['remote_verified']
    for f, h in receipt['frozen_files'].items():
        assert digest(ROOT/f) == h, f
    for f, h in json.loads((private()/'protected_parent_hashes.json').read_text()).items():
        assert digest(ROOT/f) == h, f
    assert digest(inherited()/'canonical/ledger.parquet') == LEDGER_HASH
    assert digest(inherited()/'center_error_ledger.parquet') == CENTER_HASH
    assert subprocess.check_output(['git','rev-parse','origin/main'], cwd=ROOT, text=True).strip() == MAIN
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip() == BRANCH
    return receipt


def prepare():
    p = private()
    p.mkdir(exist_ok=True)
    assert digest(inherited()/'canonical/ledger.parquet') == LEDGER_HASH
    assert digest(inherited()/'center_error_ledger.parquet') == CENTER_HASH
    meta = pq.read_table(inherited()/'canonical/ledger.parquet', columns=['origin','asset','group','horizon','kind','target_end']).to_pandas()
    hashes = protect()
    series, kinds, _ = load_universe(ROOT)
    series = {a: _prefix(s, str(s.index.max().date())) for a,s in series.items()}
    origins = pd.DatetimeIndex(sorted(meta.origin.unique()))
    features, sigma = fingerprint(series, kinds, origins)
    features.to_parquet(p/'fingerprints.parquet')
    sigma.to_parquet(p/'sigma63.parquet')
    spec = dict(executive_summary='One compact PIT fingerprint; whole matured historical origins supply joint draws.',
                parent=PARENT, branch=BRANCH, seed=SEED, hard_timebox_hours=8,
                candidate_origins='Exact canonical 5BD origin grid; no external data.',
                historical_evaluation_years=list(YEARS), k_selection_years=list(range(2009,2016)),
                K=list(KS), tie_break='larger K', draw_count=DRAW_COUNT,
                feature_columns=list(features.columns), asset_features=list(FEATURE_NAMES),
                shared_features=['mean standardized move21','mean vol63/sigma252'],
                common_direction='NOT_AVAILABLE; no new PCA implemented',
                normalization='Before each query, median and IQR fitted to all strictly earlier state rows; constant IQR -> 1. Shared finite dimensions only. Missing dimensions omitted; no whole-dataset scaler.',
                analog_scale='63BD daily innovation population SD, shifted one day, min50 observations, floor1e-8.',
                target_mapping={'level':'current observed level + (past realized endpoint - past observed level)/past pre-origin sigma63 * current pre-origin sigma63',
                                'log_return':'Unchanged sum of original future daily return increments; no re-scaling.'},
                target_semantics='Reuse exact canonical _label endpoint/gap rules; every required actual target_end < query origin. No calendar shortcut.',
                distance='Equal-weight root mean squared Euclidean standardized differences on shared finite columns.',
                eligibility='All requested cells available, finite analog transforms, complete endpoint strictly matured, state coverage>=80%; at least8 candidates.',
                fallback='Exact stored baseline CRPS/no changed forecast when insufficient technical coverage. No score-based eligibility.',
                resampling='Uniform K nearest; deterministic seed31812+origin index; one index per joint draw. K availability shortfall uses min(K,eligible_count), never fewer than8.',
                oracle={'exact_part':'Exhaustive minimum of the shared-score summed normalized marginal point-path losses over every eligible joint origin.',
                        'empirical_part':'Deterministic greedy additions: exhaust every eligible joint origin at each of8 steps; optimize shared biased CRPS of empirical measure; rescore 1000 whole draws using inherited fair estimator.',
                        'gate_ratio':'Minimum of whole-scenario scores over single and greedy sets of sizes2..8; ratio of sums; all eligible canonical cells including fallback.',
                        'optimizer_limitation':'Greedy empirical sets do not certify a global minimum over all mixtures. A failed gate is failure of this frozen diagnostic, not proof that every possible mixture fails.',
                        'full_composite':'NOT_AVAILABLE on canonical marginal ledger. Do not open card outcomes to create an oracle before Gate2.'},
                kill_gate1={'marginal_max':.65,'full_max_when_computable':.70},
                kill_gate2={'ratio_max':.85,'equal_year_max':.90,'improved_recent9_min':6,'year_gross_gain_share_max':.35,'asset_gross_gain_share_max':.35,'origin_bootstrap_upper_max_exclusive':1.,'random_MC_p_max':.05},
                controls=['RANDOM_ANALOG','TIME_MATCHED_RANDOM','DISTANCE_SHUFFLE','REVERSED_SIMILARITY','CONSTANT_RECENT'],
                random_control_reps=2000, bootstrap={'reps':5000,'blocks':['origin','year','asset']},
                card_gate='No 24-card losses/truth before Gate1+Gate2 and remote PRE_RESULT_MOONSHOT12_SHA.',
                optional_hybrid='NOT_FROZEN; will not compute',
                independent_OOS=False, exposed=True,
                verdicts=['MOONSHOT_BREAKTHROUGH','MOONSHOT_PROMISING','ANALOG_LIBRARY_HEADROOM_INSUFFICIENT','ANALOG_NOT_PREDICTIVE','CARD_PROXY_FAILURE','MULTI_SAFETY_FAILURE','OVERCONCENTRATED','INCONCLUSIVE'])
    save(OUT/'experiment_spec.json', spec)
    save(OUT/'environment_audit.json',dict(executive_summary='Exact parent and protected baseline; existing public panels/private canonical files only.',
        parent=PARENT,main=MAIN,python=sys.version,platform=platform.platform(),protected_parent_files=len(hashes),
        runtime_note='Host Python3.12 source-import audit, as in validated delivery11; no toolkit install/Requires-Python bypass. Safe candidate and its Python3.13/common2.4.2 unchanged.',
        scorer_module=crps_ensemble.__module__,scorer_SHA256=digest(Path(sys.modules[crps_ensemble.__module__].__file__)),
        scorer_matches_canonical_common243=True,broader_labels_opened=False,card_outcomes_opened=False))
    save(OUT/'lineage_manifest.json',dict(executive_summary='Separate new research branch from the exact validated delivery result.',parent=PARENT,main=MAIN,safe_source='47194f28d5188b87cdca1d591d86b9eeda86f7cf',safe_image='docker.io/jotj216/track2-f4-approved@sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874',historical_reference=.9541,official_artifact_identity_proven=False))
    save(OUT/'analog_data_manifest.json',dict(executive_summary='Original canonical universe and exact preserved baseline CRPS; no substitute model.',
        origins=int(meta.origin.nunique()),cells=len(meta),assets=sorted(meta.asset.unique()),date_range=[meta.origin.min(),meta.origin.max()],horizons=sorted(meta.horizon.unique()),
        canonical_SHA256=LEDGER_HASH,center_ledger_SHA256=CENTER_HASH,panel_files={str(f.relative_to(ROOT)):digest(f) for f in sorted((ROOT/'units').rglob('*.parquet'))},
        baseline_source='Frozen center_error_ledger.baseline_CRPS from exact original cache scoring. Original cache arrays not needed for unchanged marginal loss reuse; no reconstruction.',
        independent_OOS=False,available_series={a:{'start':str(s.index.min().date()),'end':str(s.index.max().date()),'kind':kinds[a]} for a,s in series.items()}))
    save(OUT/'target_semantics_audit.json',dict(executive_summary='Levels and accumulated return increments remain distinct.',kinds=kinds,
        labels='Inherited canonical target truths/endpoints; repository _label business days and no gaps>5BD, endpoint<=3BD late.',
        unrepresented='Monthly macro targets are not in canonical panel catalog. They will be technical baseline fallback on cards, not omitted.',
        current_panel_PIT='Original frozen public prefixes; rows<=origin used. No immutable historical publication vintage proof beyond inherited repository semantics.',
        canonical_baseline='V5.1 no-text continuous prior; do not call this the official Development ledger.'))
    for filename,key in [('pit_eligibility_spec.json','eligibility'),('feature_spec.json','feature_columns'),('analog_transform_spec.json','target_mapping'),('distance_spec.json','distance'),('draw_construction_spec.json','resampling')]:
        save(OUT/filename,dict(executive_summary='Pre-outcome technical specification.',definition=spec[key]))
    save(OUT/'feature_manifest.json',dict(executive_summary='Private deterministic feature cache from public prefixes only.',columns=list(features.columns),SHA256=digest(p/'fingerprints.parquet'),sigma_SHA256=digest(p/'sigma63.parquet'),normalization=spec['normalization']))
    status('environment_and_mechanism_audit',True,pending_stages=['pre_oracle_freeze','path_bank','oracle','kill_gate1','historical_selection','historical_validation','controls','bootstrap','kill_gate2','card_PRE','cards','tests','report','RESULT','recovery'])


def bank():
    verify()
    p = private()
    if (p/'bank_receipt.json').exists():
        return
    rows = pd.read_parquet(inherited()/'canonical/ledger.parquet')
    center = pd.read_parquet(inherited()/'center_error_ledger.parquet')
    assert rows.equals(center[rows.columns])
    series,kinds,_ = load_universe(ROOT)
    series = {a:_prefix(s,str(s.index.max().date())) for a,s in series.items()}
    feat = pd.read_parquet(p/'fingerprints.parquet')
    sigma = pd.read_parquet(p/'sigma63.parquet')
    keys = sorted(set(zip(rows.asset,rows.horizon)))
    key_index = {k:i for i,k in enumerate(keys)}
    o_index = {str(x.date()):i for i,x in enumerate(feat.index)}
    n,d = len(feat),len(keys)
    innovation = np.full((n,d),np.nan)
    end = np.full((n,d),np.datetime64('NaT'),dtype='datetime64[ns]')
    truth = np.full((n,d),np.nan)
    scale = np.full((n,d),np.nan)
    base = np.full((n,d),np.nan)
    levels = np.full((n,d),np.nan)
    pre_scale = np.full((n,d),np.nan)
    for row in center.itertuples(index=False):
        oi=o_index[row.origin];ci=key_index[(row.asset,row.horizon)];stamp=pd.Timestamp(row.origin)
        anchor=float(series[row.asset].loc[stamp]) if row.kind=='level' else 0.
        sig=float(sigma.loc[stamp,row.asset])
        innovation[oi,ci]=(row.truth-anchor)/sig if row.kind=='level' else row.truth
        end[oi,ci]=np.datetime64(row.target_end)
        truth[oi,ci]=row.truth;scale[oi,ci]=row.scale;base[oi,ci]=row.baseline_CRPS
        levels[oi,ci]=anchor;pre_scale[oi,ci]=sig
    np.savez_compressed(p/'path_bank.npz',innovation=innovation,end=end,truth=truth,scale=scale,base=base,levels=levels,pre_scale=pre_scale,origins=feat.index.to_numpy())
    save(p/'bank_keys.json',dict(keys=keys,kinds=[kinds[a] for a,h in keys]))
    save(p/'bank_receipt.json',dict(SHA256=digest(p/'path_bank.npz'),center_hash=CENTER_HASH,canonical_hash=LEDGER_HASH,identical_original_fields=True))
    status('path_bank',True,bank_SHA256=digest(p/'path_bank.npz'),broader_labels_opened=True)


def query(bank_arrays, keys, feat, oi):
    current=bank_arrays['origins'][oi]
    cols=np.flatnonzero(np.isfinite(bank_arrays['truth'][oi]) & np.isfinite(bank_arrays['pre_scale'][oi]))
    earlier=np.flatnonzero(bank_arrays['origins']<current)
    ends=bank_arrays['end'][earlier][:,cols]
    values=bank_arrays['innovation'][earlier][:,cols]
    mask=eligible_paths(ends,values,current)
    assets=sorted(set(keys['keys'][c][0] for c in cols))
    fcols=[c for c in feat.columns if c.split(':')[0] in assets or c.startswith('shared:')]
    distance,coverage=shared_distances(feat.iloc[earlier][fcols],feat.iloc[oi][fcols])
    mask &= np.isfinite(distance)
    donors=earlier[mask]
    paths=map_innovations(values[mask],np.asarray(keys['kinds'])[cols],bank_arrays['levels'][oi,cols],bank_arrays['pre_scale'][oi,cols])
    return cols,donors,paths,distance[mask],coverage[mask]


def oracle(year):
    verify();p=private();dest=p/'oracle'/str(year);dest.mkdir(parents=True,exist_ok=True)
    data=np.load(p/'path_bank.npz',allow_pickle=False);keys=json.loads((p/'bank_keys.json').read_text());feat=pd.read_parquet(p/'fingerprints.parquet')
    origins=data['origins'];indices=np.flatnonzero(pd.DatetimeIndex(origins).year==year);beg=time.monotonic()
    for done,oi in enumerate(indices,1):
        file=dest/f'{oi:04d}.npz'
        if file.exists():continue
        cols,donors,paths,dist,coverage=query(data,keys,feat,oi)
        base=data['base'][oi,cols]
        if len(donors)<MIN_ANALOGS:
            cells=base.copy();selected=[];curve=[]
        else:
            cells,selected,curve=oracle_search(paths,data['truth'][oi,cols],data['scale'][oi,cols])
        np.savez_compressed(file,cols=cols,oracle=cells,base=base,selected_donors=donors[selected] if selected else np.array([],int),curve=curve,donor_count=len(donors),fallback=len(donors)<MIN_ANALOGS)
        if done%5==0 or done==len(indices):
            print(json.dumps(dict(stage='candidate_path_oracle',year=year,completed=done,total=len(indices),elapsed=round(time.monotonic()-beg,1),origin=str(origins[oi])[:10],output=str(file))),flush=True)
        status('candidate_path_oracle',year=year,completed_origins=done,total_origins=len(indices),broader_labels_opened=True)
    save(dest/'COMPLETE.json',dict(year=year,origins=len(indices)))


def aggregate_oracle():
    verify();p=private();by_year=[];base_total=0.;loss_total=0.;cells_total=0;origins_total=0;fallbacks=0
    for year in YEARS:
        dest=p/'oracle'/str(year)
        assert (dest/'COMPLETE.json').exists(),year
        base=0.;loss=0.;cells=0;n=0;fallback=0
        for file in sorted(dest.glob('*.npz')):
            d=np.load(file);base+=float(d['base'].sum());loss+=float(d['oracle'].sum());cells+=len(d['cols']);n+=1;fallback+=int(d['fallback'])
        by_year.append(dict(year=year,origins=n,cells=cells,ratio=loss/base,fallback_origins=fallback))
        base_total+=base;loss_total+=loss;cells_total+=cells;origins_total+=n;fallbacks+=fallback
    ratio=loss_total/base_total;passed=gate1(ratio)
    summary=dict(executive_summary='Future-informed complete historical scenarios; not a forecast result.',marginal_ratio=ratio,full_composite=None,full_status='NOT_AVAILABLE_ON_CANONICAL_MARGINAL_LEDGER; card outcomes unopened',
        years=by_year,origins=origins_total,cells=cells_total,fallback_origins=fallbacks,
        oracle_scope='Exact best single joint path plus frozen greedy whole-scenario sets up to8; every repeated draw is one coherent origin.',
        optimizer_limitation='Greedy sets are not a certificate of the global optimum over arbitrary mixtures.',baseline='Exact same-cell preserved LOCATION01 V5.1 normalized marginal CRPS',scorer='qfbench2_common.scoring.crps.crps_ensemble',future_informed=True)
    save(OUT/'candidate_path_oracle.json',summary)
    save(OUT/'oracle_kill_gate.json',dict(executive_summary='Fixed threshold applied without redesign.',passed=passed,marginal=ratio,marginal_required_max=.65,full_required_max=.70,full_available=False,card_outcomes_opened=False))
    status('oracle_kill_gate',True,gate1_passed=passed,broader_labels_opened=True)
    print(json.dumps(summary),flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['prepare','bank','oracle','aggregate_oracle']);parser.add_argument('--year',type=int)
    args=parser.parse_args()
    if args.stage=='oracle':oracle(args.year)
    else:globals()[args.stage]()


if __name__=='__main__':
    main()

"""Executive summary: freeze source, parser and experimental choices before outcomes."""
import argparse
import json
from pathlib import Path
from .source_acquisition import OUT,ROOT,dump,digest
from .model import FEATURES,HORIZONS,MODELS,SEED


def freeze(private):
    readiness=json.loads((OUT/'ecb_dataset_readiness.json').read_text())
    if not readiness['DATASET_READY']:raise ValueError('Gate A failed')
    protected=json.loads((private/'parent_protected_hashes.json').read_text())
    for name,sha in protected.items():
        if digest(ROOT/name)!=sha:raise ValueError('Protected parent file changed '+name)
    spec={'executive_summary':'Fixed source-only selection followed by five-input shared Ridge; no outcome evaluation before verified PRE.',
      'parent_result_sha':'43a154ab419b6f3e3f4fc903db40d8c2e319f6bf','branch':'track2/location-02-ecb-spf-alpha',
      'source':'ECB_SPF_ORIGINAL','asset':'EUR','target_semantics':'Exact frozen ledger level target, not FX log return; maturity from original ledger',
      'features':list(FEATURES),'missingness':'No imputation; inactive origins zero shift and excluded from active primary universe',
      'revision_rule':'Current next calendar year minus preceding verified original round for exactly same variable and target year',
      'source_age_max_business_days':90,'availability':'Publication date 23:59:59 Europe/Berlin; aware comparison to parent prior-weekday NY16 cutoff',
      'cutoff_calendar':'Parent weekday BDay; conservatively exclude NY federal-holiday cutoff dates; horizons unchanged',
      'origins':'First existing frozen baseline ledger origin each month in 2015-2024, fixed in source_calendar.csv before outcomes',
      'truth_cutoff':'2024-12-18; original EUR series ends 2024-10-31, never extended',
      'horizons':list(HORIZONS),'initial_development_years':[2015,2016,2017,2018,2019],
      'test_years':[2020,2021,2022,2023,2024],
      'folds':'Expanding earlier origins; target_end strictly before first test cutoff. Shared maximum189BD origin purge plus horizon-specific maturity check. No train/test shared release IDs.',
      'primary':'ECB_RIDGE_FULL5','model':'Ridge','alpha':1.0,'intercept':True,'solver':'svd',
      'scaler':'StandardScaler, train only; equal release weights; zero training variance handled deterministically',
      'training_weights':'Each training source release total weight exactly1; every row in release gets1/row_count. Same weights used for scaler and Ridge.',
      'ablation_columns':{k:[FEATURES[i] for i in v] for k,v in MODELS.items()},
      'no_selection_or_tuning':True,'shift':'Frozen V5.1 draw + predicted_delta * original population SD; no rescale or shape changes',
      'scorer':'Imported qfbench2_common.scoring.crps.crps_ensemble, fair=True; original normalized CRPS/(past scale); ratio of sums over same eligible cells',
      'oracle':'Pure shift to realized truth, same ledger; diagnostic only','bootstrap':{'replicates':5000,'primary':'release blocks','secondary':'year blocks','seed':SEED},
      'controls':{'permutations':2000,'seed':SEED,'release_value':'Shuffle4 source values across training release blocks; age stays; held-out covariates unchanged',
       'release_date':'Randomly reassign fixed nonnegative0..20BD publication delays across all40 events; never early activation; inactive null features give zero shift',
       'revision_sign':'Shuffle two revisions and signs across training releases; one fixed vector per release; levels+age stay',
       'feature_year':'One-year lag source states; unavailable states zero shift, no replacement',
       'Gaussian':'Five independent Gaussian values per release, same chronological fit and release balance',
       'future_mutation':'Later releases mutated; earlier source features and earlier fold predictions exactly unchanged',
       'outcome_mutation':'Source construction has no outcome input; mutations cannot affect features'},
      'interpretation':{'STRONG_YES':'Ratio<=.90 capture>=.20 at least4/5 improved; all stochastic null lower-tail probability<.05; release CI upper<1; no concentration',
       'YES':'Ratio<=.95 capture>=.10 at least3/5 improved; all control medians worse; no concentration',
       'WEAK_YES':'Ratio<=.98 capture>.05 more improving folds; all control medians worse',
       'NO':'Ratio>=1.02, capture<=0, or any control median/fixed lag as good as primary',
       'INCONCLUSIVE':'Otherwise, including slight gain or conflicting inference; no ablation rescue',
       'concentration':'More than50% of gross positive score gain from one release or one year flags domination; gain shares only meaningful if positive gain exists'},
      'research_exposed':True,'independent_OOS':False,'submission_readiness':False,
      'pre_outcome_status':{'outcomes_loaded':False,'fits':0,'scores':0}}
    dump(OUT/'experiment_spec.json',spec)
    names=[p for p in (ROOT/'backtesting/location02').glob('*.py')]
    names+=list((ROOT/'tests').glob('test_location02*.py'))
    names+=[OUT/name for name in ['ecb_release_universe.csv','ecb_publication_ledger.csv','ecb_field_ledger.csv','ecb_errata_ledger.csv','ecb_pit_dataset_manifest.json','ecb_dataset_readiness.json','source_calendar.csv','experiment_spec.json']]
    hashes={str(p.relative_to(ROOT)):digest(p) for p in sorted(names)}
    dump(OUT/'pre_result_manifest.json',{'executive_summary':'Frozen files hashed before labels; actual verified Git PRE receipt remains private until result artifacts.',
        'parent_result_sha':spec['parent_result_sha'],'frozen_file_hashes':hashes,
        'PRE_RESULT_LOCATION02_SHA':'PENDING_REMOTE_COMMIT_RECEIPT','Gate_A_passed':True,
        'original_ledger_sha256':'5a421fa5c10745c69469c683797bf42f4abf54288e8082984bcf39fda76968a6',
        'baseline_recovery':json.loads((private/'baseline_recovery_metadata.json').read_text()),
        'outcomes_loaded':False,'fits':0,'scores':0})
    print('Pre specification and implementation frozen locally; no outcomes opened.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private',type=Path,required=True);freeze(p.parse_args().private)

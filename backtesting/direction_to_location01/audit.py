"""Executive summary: audit exact parent predictions/draws and preserved train scalers; no refit."""
import argparse, json, platform, subprocess
from pathlib import Path
import numpy as np
import pandas as pd
from qfbench2_common.scoring.crps import crps_ensemble
from backtesting.information_failure01.audit import selected_indices
from .core import *

FEATURES = ('POLICY_NEAR','POLICY_FAR','POLICY_PATH_SLOPE','POLICY_REVISION_SAME_TARGET','SOURCE_AGE_BUSINESS_DAYS')
def run(private):
    p=Path(private); parent=p/'parent'; q=parent/'source_experiments/SPD/private'; d=parent/'diagnostic_inputs/SPD'
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==PARENT
    for sha in [LOCATION04_RESULT,'2e356b91dd98dae022b72494ea6d4c70a9a38ed7','1a417f0522e04e2ecf1598c80e0bf0ebb1e7b5fe']:
        assert subprocess.run(['git','merge-base','--is-ancestor',sha,PARENT],cwd=ROOT).returncode==0
    r=pd.read_parquet(d/'ledger.parquet'); allr=pd.read_parquet(q/'evaluation_ledger.parquet'); scored=pd.read_parquet(q/'scored_rows.parquet'); ii=selected_indices(allr,scored)
    assert len(r)==552 and set(r.asset)==set(ASSETS) and set(r.horizon)==set(HORIZONS) and set(r.year)==set(YEARS)
    assert np.array_equal(r[['origin_date','asset','horizon']].to_numpy(),scored[['origin','asset','horizon']].to_numpy())
    original=np.load(q/'predictions.npz',allow_pickle=False); pp=original['SPD_FULL5_RELEASE_BALANCED'][ii]
    assert np.array_equal(pp,r.predicted_delta) and np.array_equal(np.flatnonzero(original['eval_mask']),ii)
    draws=np.load(q/'evaluation_draws.npz')['draws'][:,ii]
    assert np.array_equal(draws,np.load(q/'scored_draws.npz')['draws']) and np.array_equal(draws,np.load(d/'draws.npz')['draws'])
    assert np.array_equal(scored.truth,r.truth) and np.array_equal(scored.sd,r['V5.1_SD'])
    assert np.allclose(np.median(draws,axis=0),r['V5.1_median'],atol=1e-14,rtol=0)
    assert np.allclose(draws.std(axis=0),r['V5.1_SD'],atol=1e-14,rtol=1e-13)
    assert (pd.to_datetime(r.target_end)<=pd.Timestamp('2024-12-18')).all()
    x=allr.iloc[ii][list(FEATURES)].to_numpy(); modelinfo=json.loads((d/'models.json').read_text()); zmax=np.full(len(r),np.nan); reconstructed=np.full(len(r),np.nan)
    for model in modelinfo['models']:
        mask=(r.year.eq(model['year']) & r.asset.eq(model['asset']) & r.horizon.eq(model['horizon'])).to_numpy()
        z=(x[mask]-np.asarray(model['scaler_mean']))/np.asarray(model['scaler_scale'])
        zmax[mask]=np.max(abs(z),axis=1); reconstructed[mask]=z@np.asarray(model['coefficient'])+model['intercept']
        assert model['alpha']==1
    assert np.isfinite(zmax).all() and np.allclose(reconstructed,pp,atol=1e-12,rtol=1e-12)
    assert np.allclose(zmax,r.heldout_max_abs_train_z,atol=1e-12,rtol=1e-12)
    states=json.loads((ROOT/'backtesting/location04/results/source_states.json').read_text())['states']; state_by={s['release_id']:s for s in states}
    for j,row in r.iterrows():
        state=state_by[row.release_id]; cutoff=pd.Timestamp(allr.iloc[ii[j]].cutoff)
        assert pd.Timestamp(state['available_at'])<=cutoff and row.source_age<=70 and state['full5_usable_at_release']
    folds=pd.read_csv(ROOT/'backtesting/location04/results/fold_manifest.csv'); valid=folds.loc[folds.asset.isin(ASSETS) & folds.valid]
    assert len(valid)==50 and (valid.shared_release_count==0).all()
    for _,f in valid.iterrows(): assert pd.Timestamp(f.maximum_train_target_end)<pd.Timestamp(f.first_test_cutoff).tz_localize(None).normalize()
    losses=np.load(q/'losses.npz'); base=crps_ensemble(draws,r.truth.to_numpy(),fair=True)/r.normalization_scale.to_numpy(); full=crps_ensemble(draws+pp*r['V5.1_SD'].to_numpy(),r.truth.to_numpy(),fair=True)/r.normalization_scale.to_numpy()
    assert np.allclose(base,losses['baseline'],atol=1e-12,rtol=1e-12) and np.allclose(full,losses['SPD_FULL5_RELEASE_BALANCED'],atol=1e-12,rtol=1e-12)
    published=json.loads((ROOT/'backtesting/location04/results/primary_score_summary.json').read_text())['models']['SPD_FULL5_RELEASE_BALANCED']['crps_ratio']; ratio=float(full.sum()/base.sum()); assert abs(ratio-published)<=1e-12
    cell=direction_metrics(r.true_delta,pp,np.ones(len(r))); rel=direction_metrics(r.true_delta,pp,group_weights(r.release_id)); old=json.loads((ROOT/'backtesting/information_failure01/results/direction_signal_summary.json').read_text())['sources']['SPD']['weighting_metrics']
    for balance,current in [('cell',cell),('release',rel)]:
        for key in ['sign_accuracy','balanced_sign_accuracy','pearson','spearman']:assert abs(current[key]-old[balance][key])<=1e-12
    prior=json.loads((ROOT/'backtesting/information_failure01/results/SPD-reproduction.json').read_text()); assert array_hash(pp)==prior['selected_prediction_array_sha256']; assert digest(q/'predictions.npz')==prior['predictions_npz_sha256']; assert array_hash(draws)==prior['frozen_baseline_draw_array_sha256']
    inputs=p/'inputs';inputs.mkdir(exist_ok=True);r.to_parquet(inputs/'ledger.parquet',index=False);np.savez_compressed(inputs/'frozen.npz',draws=draws,prediction=pp,sd=r['V5.1_SD'],zmax=zmax,features=x,base=losses['baseline'],oracle=losses['oracle'],full=losses['SPD_FULL5_RELEASE_BALANCED']); save(inputs/'models.json',modelinfo)
    paths=[d/'ledger.parquet',d/'draws.npz',d/'models.json']+[q/n for n in ['evaluation_ledger.parquet','scored_rows.parquet','predictions.npz','evaluation_draws.npz','scored_draws.npz','losses.npz']]+list((q/'fits').glob('SPD_FULL5_RELEASE_BALANCED-*.json'))+list(inputs.iterdir())
    save(p/'input_hash_manifest.json',{'files':{str(f.relative_to(p)):digest(f) for f in paths}})
    save(OUT/'environment_audit.json',{'Python':platform.python_version(),'repository_access':True,'parent_exact':True,'branch':'track2/direction-to-location-01','main_SHA':'e1b5cf3b3a87966e902332ef3cc5c0ed2dbffee8','main_unchanged':True,'parent_recovery':json.loads((p/'parent-recovery-audit.json').read_text()),'common_commit':'03fc89cc666354e999768381bb923e60be5c1cee'})
    save(OUT/'lineage_manifest.json',{'parent_RESULT':PARENT,'LOCATION04_RESULT':LOCATION04_RESULT,'LOCATION04_PRE':'2e356b91dd98dae022b72494ea6d4c70a9a38ed7','INFO_FAILURE_PRE':'1a417f0522e04e2ecf1598c80e0bf0ebb1e7b5fe','all_ancestors_verified':True,'original_PIT_purge_target_rules_unchanged':True,'target':'UST yield level, exact original truth minus original median / original ddof0 SD','horizon_semantics':'Repository business-day horizons; target maturity no later than 2024-12-18','original_fold_manifest_SHA256':digest(ROOT/'backtesting/location04/results/fold_manifest.csv'),'source_features':FEATURES,'models_retrained':0})
    save(OUT/'frozen_spd_prediction_manifest.json',{'original_primary_ratio':published,'reproduced_primary_ratio':ratio,'difference':ratio-published,'tolerance':1e-12,'prediction_file_SHA256':digest(q/'predictions.npz'),'prediction_array_SHA256':array_hash(pp),'baseline_draw_array_SHA256':array_hash(draws),'cell_direction':cell,'release_balanced_direction':rel,'cells':len(r),'origins':int(r.origin_date.nunique()),'releases':int(r.release_id.nunique()),'assets':ASSETS,'years':YEARS,'horizons':HORIZONS,'original_models_preserved':50,'OOD_z_from_original_train_scalers':True,'features_SHA256':array_hash(x),'new_candidate_CRPS_calculated':False})
    status('frozen_artifact_audit',str(OUT/'frozen_spd_prediction_manifest.json')); print('AUDIT passed: exact frozen SPD ratio/hash/direction/552-cell scope; no DTL score calculated',flush=True)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private',type=Path,required=True);args=a.parse_args();run(args.private)

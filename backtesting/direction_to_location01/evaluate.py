"""Executive summary: score the precommitted primary, then secondary diagnostics and fixed controls."""
import argparse, copy, json, time
from pathlib import Path
import numpy as np
import pandas as pd
from qfbench2_common.scoring.crps import crps_ensemble
from backtesting.location04.source_dataset import asof_features, cutoff, FEATURES
from .core import *
from .controls import ControlPlan, losses_for_sign, sample_blocks

MODELS=('V5.1',PRIMARY,'DTL_005','DTL_020','OOD3_DIAGNOSTIC','PERFECT_LOCATION_ORACLE')
def inputs(private):
    p=Path(private);verify_pre(p);r=pd.read_parquet(p/'inputs/ledger.parquet');f=np.load(p/'inputs/frozen.npz',allow_pickle=False)
    return p,r,f

def loss(draws,rows,shifts):
    return crps_ensemble(translate(draws,shifts),rows.truth.to_numpy(),fair=True)/rows.normalization_scale.to_numpy()

def geometry(draws,shift):
    candidate=translate(draws,shift); order=np.argsort(draws,axis=0,kind='stable');b=np.take_along_axis(draws,order,axis=0);c=np.take_along_axis(candidate,order,axis=0);diff=np.diff(c,axis=0)
    scale=max(1.,float(np.max(abs(draws))));err=float(np.max(abs((candidate-np.median(candidate,axis=0))-(draws-np.median(draws,axis=0)))))
    assert (diff>=0).all() and np.allclose(candidate.std(axis=0),draws.std(axis=0),atol=1e-14,rtol=1e-13)
    assert err<=32*np.finfo(float).eps*scale
    return dict(pure_location=True,SD_unchanged=True,weak_ordering_unchanged=True,centered_geometry_max_abs_error=err,new_rounding_ties=int(((np.diff(b,axis=0)>0)&(diff==0)).sum()),intentional_jitter=False,scale_tail_copula_modified=False)

def primary(private):
    p,r,f=inputs(private);s=shift_vector(f['prediction'],f['sd']);candidate=loss(f['draws'],r,s);oracle=loss(f['draws'],r,r.truth.to_numpy()-np.median(f['draws'],axis=0));assert np.allclose(oracle,f['oracle'],atol=1e-12,rtol=1e-12)
    summary={balance:score_summary(r,f['base'],candidate,oracle,s,balance) for balance in ['cell','release']};old=json.loads((OUT/'frozen_spd_prediction_manifest.json').read_text())
    for balance, oldkey in [('cell','cell_direction'),('release','release_balanced_direction')]:
        for key in ['sign_accuracy','balanced_sign_accuracy','spearman','pearson']:assert abs(summary[balance]['frozen_source_direction'][key]-old[oldkey][key])<=1e-12
    np.savez_compressed(p/'primary.npz',loss=candidate,shift=s,oracle=oracle)
    save(OUT/'primary_summary.json',{'primary_model':PRIMARY,'primary_amplitude':PRIMARY_AMPLITUDE,'models':{'V5.1':score_summary(r,f['base'],f['base'],oracle,np.zeros(len(r))),PRIMARY:summary['cell']},'release_balanced_primary':summary['release'],'geometry':geometry(f['draws'],s),'direction_metrics_match_frozen_source':True,'READY_FOR_SUBMISSION':False})
    save(OUT/'oracle_summary.json',{'R_ORACLE':float(oracle.sum()/f['base'].sum()),'reconstructed_exact_same_ledger':True,'max_cell_loss_difference':float(np.max(abs(oracle-f['oracle']))),'cells':len(r),'oracle_is_descriptive_not_predictable':True})
    for field,name in [('asset','asset'),('horizon','horizon'),('year','year'),('release_id','release')]:
        out=[]
        for value,g in r.groupby(field):
            ii=g.index.to_numpy()
            for balance in ['cell','release']:out.append(dict(group=value,model=PRIMARY,**score_summary(g,f['base'][ii],candidate[ii],oracle[ii],s[ii],balance)))
        from backtesting.information_failure01.common import csv
        csv(OUT/(name+'_summary.csv'),out)
    status('primary',str(OUT/'primary_summary.json'));print('PRIMARY scored',len(r),'cells: fixed0.10 only',flush=True)

def secondary(private):
    p,r,f=inputs(private);primary_file=np.load(p/'primary.npz');losses={'V5.1':f['base'],PRIMARY:primary_file['loss'],'PERFECT_LOCATION_ORACLE':primary_file['oracle']};shifts={'V5.1':np.zeros(len(r)),PRIMARY:primary_file['shift'],'PERFECT_LOCATION_ORACLE':r.truth.to_numpy()-np.median(f['draws'],axis=0)};summaries={};geom={}
    for name,amplitude in SECONDARY.items():
        s=shift_vector(f['prediction'],f['sd'],amplitude);v=loss(f['draws'],r,s);losses[name]=v;shifts[name]=s;summaries[name]={'secondary_only':True,**score_summary(r,f['base'],v,primary_file['oracle'],s)};geom[name]=geometry(f['draws'],s)
    s=shift_vector(f['prediction'],f['sd'],max_train_z=f['zmax']);v=loss(f['draws'],r,s);losses['OOD3_DIAGNOSTIC']=v;shifts['OOD3_DIAGNOSTIC']=s;summaries['OOD3_DIAGNOSTIC']={'secondary_only':True,**score_summary(r,f['base'],v,primary_file['oracle'],s)};geom['OOD3_DIAGNOSTIC']=geometry(f['draws'],s)
    names=list(MODELS);np.savez_compressed(p/'all_scores.npz',names=names,losses=np.array([losses[n] for n in names]),shifts=np.array([shifts[n] for n in names]))
    # Only three possible signed primary-sized shifts: cache exact common-toolkit losses, not new scoring math.
    table=np.array([loss(f['draws'],r,sign*PRIMARY_AMPLITUDE*f['sd']) for sign in [-1,0,1]]);np.savez_compressed(p/'null_loss_table.npz',losses=table)
    save(OUT/'secondary_sensitivity.json',{'models':summaries,'geometry':geom,'primary_not_replaced':True,'optimized_amplitude':None})
    guard=f['zmax']>OOD_THRESHOLD;byyear=[]
    for y,g in r.groupby('year'):
        ii=g.index.to_numpy();byyear.append(dict(year=int(y),OOD_fraction=float(guard[ii].mean()),**score_summary(g,f['base'][ii],v[ii],primary_file['oracle'][ii],s[ii])))
    save(OUT/'ood3_diagnostic.json',{'threshold':OOD_THRESHOLD,'zeroed_cells':int(guard.sum()),'zeroed_fraction':float(guard.mean()),'preserved_original_TRAIN_scalers':True,'all_2023_rows_retained':True,'years':byyear,'diagnostic_only':True,'primary_not_replaced':True})
    status('secondary',str(OUT/'secondary_sensitivity.json'));print('SECONDARY scored exactly0.05/0.20/OOD3; primary unchanged',flush=True)

def plan(private,rows):
    p=Path(private);states=json.loads((ROOT/'backtesting/location04/results/source_states.json').read_text())['states']
    return ControlPlan(rows,states,[cutoff(o) for o in rows.origin_date])

def control_chunk(private,kind,start,stop):
    p,r,f=inputs(private);folder=p/'controls';folder.mkdir(exist_ok=True);path=folder/f'{kind}-{start:04d}-{stop:04d}.npz'
    if path.exists():print('REUSE',path,flush=True);return
    prepared=plan(p,r);table=np.load(p/'null_loss_table.npz')['losses'];wr=group_weights(r.release_id);results=[];coverage=[];fractions=[]
    for rep in range(start,stop):
        sign,n=prepared.sample(kind,rep);v=losses_for_sign(table,sign);results.append([v.sum()/f['base'].sum(),np.dot(wr,v)/np.dot(wr,f['base'])]);coverage.append(n/len(r));fractions.append(float(np.mean(sign>0)))
    np.savez_compressed(path,ratios=results,coverage=coverage,positive_fractions=fractions);print(f'CONTROL {kind} completed={stop}/{CONTROL_REPLICATES} output={path}',flush=True)

def mutation_tests(private):
    p,r,f=inputs(private);original=shift_vector(f['prediction'],f['sd']);states=json.loads((ROOT/'backtesting/location04/results/source_states.json').read_text())['states'];checks=0
    for origin in sorted(r.origin_date.unique()):
        c=cutoff(origin);mutated=copy.deepcopy(states)
        for s in mutated:
            if pd.Timestamp(s['available_at'])>c:
                for key in FEATURES:s[key]=987654.321
        future=copy.deepcopy(states[-1]);future.update(available_at='2099-01-01T23:59:59-05:00',publication_date='2099-01-01',release_id='FUTURE_MUTATION_ONLY');mutated.append(future)
        before=asof_features(states,origin);after=asof_features(mutated,origin);assert before is not None and after is not None
        assert np.array_equal(np.asarray([before[k] for k in FEATURES]),np.asarray([after[k] for k in FEATURES]));assert before['release_id']==after['release_id'];checks+=1
    altered=r.copy();altered['truth']=999999.;altered['true_delta']=-999999.;altered['baseline_cell_CRPS']=0.;altered['candidate_cell_CRPS']=999999.
    for name,amp in [(PRIMARY,PRIMARY_AMPLITUDE),*SECONDARY.items()]:
        before=shift_vector(r.predicted_delta,r['V5.1_SD'],amp);after=shift_vector(altered.predicted_delta,altered['V5.1_SD'],amp);assert np.array_equal(before,after);assert np.array_equal(translate(f['draws'],before),translate(f['draws'],after))
    before=shift_vector(r.predicted_delta,r['V5.1_SD'],max_train_z=f['zmax']);after=shift_vector(altered.predicted_delta,altered['V5.1_SD'],max_train_z=f['zmax']);assert np.array_equal(before,after)
    assert np.array_equal(original,shift_vector(f['prediction'],f['sd']))
    return dict(FUTURE_MUTATION={'passed':True,'origins_checked':checks,'features_bitwise_invariant':True,'frozen_shifts_bitwise_invariant':True},OUTCOME_MUTATION={'passed':True,'all_primary_and_secondary_construction_bitwise_invariant':True,'no_refit_claim':True})

def control_summary(private):
    p,r,f=inputs(private);primary_ratio=float(np.load(p/'primary.npz')['loss'].sum()/f['base'].sum());out={}
    for kind in CONTROLS:
        blocks=[np.load(x) for x in sorted((p/'controls').glob(kind+'-*.npz'))];a=np.concatenate([x['ratios'] for x in blocks]);cov=np.concatenate([x['coverage'] for x in blocks]);assert len(a)==CONTROL_REPLICATES;n=int(np.sum(a[:,0]<=primary_ratio+1e-12))
        out[kind]=dict(replicates=len(a),median_ratio=float(np.median(a[:,0])),ratio_95_range=np.quantile(a[:,0],[.025,.975]).tolist(),mean_ratio=float(np.mean(a[:,0])),fraction_at_least_as_good=n/len(a),add_one_p=(n+1)/(len(a)+1),release_balanced_median_ratio=float(np.median(a[:,1])),mean_direction_coverage=float(cov.mean()),min_direction_coverage=float(cov.min()),primary_552_cell_denominator_unchanged=True,positive_fraction_range=[float(np.min(np.concatenate([x['positive_fractions'] for x in blocks]))),float(np.max(np.concatenate([x['positive_fractions'] for x in blocks])))])
    prepared=plan(p,r);sign,matched=prepared.prior_year();table=np.load(p/'null_loss_table.npz')['losses'];v=losses_for_sign(table,sign);out['ONE_YEAR_SHIFT']=dict(crps_ratio=float(v.sum()/f['base'].sum()),coverage_cells=len(matched),coverage_fraction=len(matched)/len(r),unmatched_zero_shift=True,full_universe_used=True);np.savez_compressed(p/'one_year_control.npz',direction=sign,loss=v,matched=matched)
    save(OUT/'negative_controls.json',{'controls':out,'mutations':mutation_tests(p),'seed':SEED,'amplitude':PRIMARY_AMPLITUDE,'models_refit':0,'date_null_is_safe_delayed_mapping_not_literal_unrestricted_date_permutation':True,'release_shuffle_is_exposed_nonPIT_null_not_deployable':True});status('controls',str(OUT/'negative_controls.json'));print('CONTROLS complete:6000 stochastic nulls, prior-year and both mutation invariances',flush=True)

def bootstrap_chunk(private,block,start,stop):
    p,r,f=inputs(private);folder=p/'bootstrap';folder.mkdir(exist_ok=True);path=folder/f'{block}-{start:04d}-{stop:04d}.npz'
    if path.exists():print('REUSE',path,flush=True);return
    data=np.load(p/'all_scores.npz');base=f['base'];oracle=data['losses'][5];ratios=[];delta=[];capture=[]
    groups=r.release_id if block=='release' else r.year
    for rep in range(start,stop):
        rng=np.random.default_rng(SEED+1000000+(10000 if block=='year' else 0)+rep);w,counts,ids=sample_blocks(groups,rng);den=np.dot(w,base);ratio=data['losses']@w/den;orr=np.dot(w,oracle)/den;ratios.append(ratio);delta.append((data['losses']-base)@w/w.sum());capture.append((1-ratio)/(1-orr))
    np.savez_compressed(path,ratios=ratios,mean_delta=delta,capture=capture);print(f'BOOTSTRAP {block} completed={stop}/{BOOTSTRAP_REPLICATES} output={path}',flush=True)

def bootstrap_summary(private):
    p,r,f=inputs(private);data=np.load(p/'all_scores.npz');out={}
    for block in ['release','year']:
        files=[np.load(x) for x in sorted((p/'bootstrap').glob(block+'-*.npz'))];a=np.concatenate([x['ratios'] for x in files]);d=np.concatenate([x['mean_delta'] for x in files]);c=np.concatenate([x['capture'] for x in files]);assert len(a)==BOOTSTRAP_REPLICATES;models={}
        for j,name in enumerate(data['names']):models[str(name)]=dict(crps_ratio_95ci=np.quantile(a[:,j],[.025,.975]).tolist(),delta_ratio_vs_V51_95ci=np.quantile(a[:,j]-1,[.025,.975]).tolist(),mean_normalized_CRPS_delta_95ci=np.quantile(d[:,j],[.025,.975]).tolist(),oracle_capture_95ci=np.quantile(c[:,j],[.025,.975]).tolist())
        out[block]=dict(replicates=len(a),blocks=int(r.release_id.nunique() if block=='release' else r.year.nunique()),models=models,paired=True,no_IID_cells=True,frozen_predictions_no_refit=True)
    save(OUT/'bootstrap_summary.json',{'blocks':out,'seed':SEED,'exposed_research_not_independent_OOS':True});status('bootstrap',str(OUT/'bootstrap_summary.json'));print('BOOTSTRAP summaries complete5000+5000',flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private',type=Path,required=True);a.add_argument('--stage',choices=['primary','secondary','control_chunk','control_summary','bootstrap_chunk','bootstrap_summary'],required=True);a.add_argument('--kind',choices=CONTROLS,default=CONTROLS[0]);a.add_argument('--block',choices=['release','year'],default='release');a.add_argument('--start',type=int,default=0);a.add_argument('--stop',type=int,default=500);v=a.parse_args()
    if v.stage=='control_chunk':control_chunk(v.private,v.kind,v.start,v.stop)
    elif v.stage=='bootstrap_chunk':bootstrap_chunk(v.private,v.block,v.start,v.stop)
    else:globals()[v.stage](v.private)

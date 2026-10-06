"""Executive summary: predeclared descriptive gates choose one future hypothesis, never a candidate."""
import math
from .common import POSTHOC

def direction_label(metrics):
 r=metrics['balanced']['release'];years=[x for x in metrics['years'] if x['balance']=='release'];n=len(years)
 pos=sum(x['sign_accuracy']>.5 and x['spearman'] is not None and x['spearman']>0 for x in years)
 if r['sign_accuracy']>=.60 and (r['spearman'] or 0)>=.20 and pos>=math.ceil(.8*n):label='STRONG'
 elif r['sign_accuracy']>=.55 and (r['spearman'] or 0)>=.10 and pos>=math.ceil(.6*n):label='MODERATE'
 elif r['sign_accuracy']>.5 or (r['spearman'] or 0)>0:label='WEAK'
 else:label='NONE'
 return dict(label=label,positive_folds=pos,evaluable_folds=n,positive_fraction=pos/n,diagnostic_only=True)

def source_gates(metrics,curves,geometry,rows):
 r=metrics['balanced']['release'];d=direction_label(metrics);correct=next(v for v in metrics['partitions'] if v['dimension']=='all' and v['balance']=='cell' and v['partition']=='SIGN_CORRECT')
 witnesses=[x for x in curves['curve'] if x['kind']=='direction_only' and x['crps_ratio']<1 and x['robust_to_one_year_and_release']]
 a=r['sign_accuracy']>=.55 and (r['spearman'] or 0)>=.10 and d['positive_fraction']>=.6 and correct['crps_ratio'] is not None and correct['crps_ratio']<=.98 and bool(witnesses)
 age={x['age_bin']:x for x in metrics['ages'] if x['balance']=='release'};fresh=age['0-20'];stale=age['61-90']
 decay=fresh['releases']>=5 and stale['releases']>=5 and fresh['sign_accuracy']-stale['sign_accuracy']>=.05 and (fresh['spearman'] or 0)-(stale['spearman'] or 0)>=.10
 short=rows.horizon.isin([5,21]);long=rows.horizon.isin([126,189]);sr=float(rows.loc[short,'candidate_cell_CRPS'].sum()/rows.loc[short,'baseline_cell_CRPS'].sum());lr=float(rows.loc[long,'candidate_cell_CRPS'].sum()/rows.loc[long,'baseline_cell_CRPS'].sum());horizon=sr<1 and lr>=1.05 and lr-sr>=.05
 q=geometry['by_quintile'];low=q[0];high=q[-1];geom=(low['gross_positive_damage_share'] or 0)>=.5 and low['mean_abs_true_delta']>=2*high['mean_abs_true_delta'] and low['mean_abs_pred_delta']>=2*high['mean_abs_pred_delta'] and (geometry['release_balanced_raw']['spearman'] or 0)-(geometry['release_balanced_standardized']['spearman'] or 0)>=.10
 return dict(A=bool(a),B=bool(decay or horizon),C=bool(geom),D=False,A_fixed_sign_witness_constants=[x['value'] for x in witnesses],direction=d,original_sign_correct_ratio=correct['crps_ratio'],age_decay_criterion=bool(decay),horizon_criterion=bool(horizon),short_ratio=sr,long_ratio=lr,source_age_gate_is_not_a_candidate=True)

def choose_axis(gates,curves):
 if any(g['A'] for g in gates.values()):axis='DIRECTION-TO-LOCATION-01';reason='At least one source satisfies all frozen release direction, fold, original sign-correct gain and nonconcentrated small-shift diagnostic gates.'
 elif sum(g['B'] for g in gates.values())>=2:axis='LOW-FREQUENCY-ALIGNMENT-01';reason='The predeclared age/horizon pattern appears in at least two sources.'
 elif sum(g['C'] for g in gates.values())>=2:axis='TARGET-GEOMETRY-01';reason='The predeclared low-SD and raw-vs-standardized stability pattern appears across sources.'
 elif any(g['D'] for g in gates.values()):axis='REGIME-STABILITY-01';reason='Preserved pre-outcome regimes establish stable within-regime but reversing between-regime relationships.'
 else:axis='NEW-INFORMATION-SEARCH-02';reason='The existing sources fail at least one robust direction-to-location gate; age/geometry explanations do not recur strongly enough across sources. Do not tune their exposed diagnostic minima. Three sources do not establish that every different information family is exhausted.'
 return dict(next_axis=axis,exactly_one_axis=True,reason=reason,source_gates=gates,next_experiment_executed=False,diagnostic_label=POSTHOC,selection_uses_exposed_outcomes=True,confirmatory_candidate=None)

def attribution(metrics,curves,gates):
 r=metrics['balanced']['release'];cal=r['calibration']['slope'];p=next(v for v in metrics['partitions'] if v['dimension']=='all' and v['balance']=='cell' and v['partition']=='SIGN_CORRECT');small=min(v['crps_ratio'] for v in curves['curve'] if v['kind']=='shrinkage' and v['value']>0);fixed=min(v['crps_ratio'] for v in curves['curve'] if v['kind']=='direction_only');slopes=[v['calibration_slope'] for v in metrics['years'] if v['balance']=='release' and v['calibration_slope'] is not None];contributors=[]
 if (r['spearman'] or 0)>0 and cal is not None and 0<cal<.5 and (p['harmed_fraction'] or 0)>=.25 and small<1:mode='F2_MAGNITUDE_OVERSHOOT'
 elif gates['direction']['label'] in ['STRONG','MODERATE'] and fixed<1:mode='F1_DIRECTION_ONLY_NOT_MAGNITUDE'
 elif metrics['balanced']['cell']['sign_accuracy']>.5 and r['sign_accuracy']<=.5 and (r['spearman'] or 0)<=0:mode='F7_REPEATED_RELEASE_ARTIFACT'
 elif gates['horizon_criterion']:mode='F3_HORIZON_MISMATCH'
 elif gates['age_decay_criterion']:mode='F4_STALE_INFORMATION'
 elif gates['C']:mode='F6_TARGET_NORMALIZATION_GEOMETRY'
 elif sum(s<0 for s in slopes)>=2 and sum(s>0 for s in slopes)>=2:mode='F5_REGIME_INSTABILITY'
 elif r['sign_accuracy']<=.5 and (r['spearman'] or 0)<=0 and min(small,fixed)>=1:mode='F0_NO_INFORMATION'
 else:mode='F8_MIXED / INCONCLUSIVE'
 if gates['horizon_criterion']:contributors.append('Horizon mismatch criterion')
 if gates['age_decay_criterion']:contributors.append('Source-age decay criterion')
 if cal is not None and 0<cal<.5:contributors.append('Attenuated post-hoc release-balanced calibration slope')
 if sum(s<0 for s in slopes) and sum(s>0 for s in slopes):contributors.append('Annual calibration-sign instability; not an identified pre-outcome regime')
 return dict(primary_failure_mode=mode,secondary_contributors=contributors,quantitative_evidence=dict(release_sign_accuracy=r['sign_accuracy'],release_spearman=r['spearman'],release_calibration_slope=cal,original_sign_correct_ratio=p['crps_ratio'],sign_correct_harmed_fraction=p['harmed_fraction'],best_nonzero_shrinkage_ratio=small,best_fixed_sign_ratio=fixed,fold_calibration_slopes=slopes),label=POSTHOC,causal_claim=False)

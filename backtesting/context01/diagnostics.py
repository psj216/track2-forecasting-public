"""## Executive summary (read this first)
Aggregate fixed card components and center-error skill; retain negative captures and all families.
"""
import numpy as np
from scipy.stats import spearmanr
from qfbench2_track_forecasting.ceiling01.scorer_adapter import aggregate
def capture(ratio,perfect):return None if perfect>=1 or abs(1-perfect)<1e-12 else float((1-ratio)/(1-perfect))
def skill(y,p):
 y=np.asarray(y,float);p=np.asarray(p,float);mse=float(np.mean((y-p)**2));v=float(np.var(y));variable=np.std(p)>1e-12;slope=float(np.cov(y,p,ddof=0)[0,1]/np.var(p))if variable else None
 return dict(delta_mse=mse,delta_r2=None if v<1e-12 else 1-mse/v,pearson=float(np.corrcoef(y,p)[0,1])if variable else None,spearman=float(spearmanr(y,p).statistic)if variable else None,sign_accuracy=float(np.mean(np.sign(y)==np.sign(p))),calibration_slope=slope,calibration_intercept=float(np.mean(y)-(0 if slope is None else slope*np.mean(p))),mean_abs_shift_over_sd=float(np.mean(np.abs(p))),sign_convention='zero prediction only matches exactly zero truth')
def summarize(records,model):
 if not records:return dict(status='NOT_APPLICABLE',cards=0)
 r=[c['models'][model]['ratio']for c in records];oracle=[c['oracle']['ratio']for c in records];ratio=aggregate(r);perfect=aggregate(oracle);out=dict(cards=len(records),cells=sum(c['cells']for c in records),geometric_composite_ratio=ratio,arithmetic_composite_ratio=float(np.mean(r)),perfect_residual_location_ratio=perfect,oracle_capture_fraction=capture(ratio,perfect),card_wins=int(sum(v<1-1e-12 for v in r)),single_wins=int(sum(c['single']and c['models'][model]['ratio']<1-1e-12 for c in records)),multi_wins=int(sum(not c['single']and c['models'][model]['ratio']<1-1e-12 for c in records)))
 for component in ['marginal','joint','tail']:
  applicable=[c for c in records if c['baseline'][component]>1e-12];out[component+'_ratio']=aggregate([c['models'][model][component]/c['baseline'][component]for c in applicable]);out[component+'_baseline_mean']=float(np.mean([c['baseline'][component]for c in records]));out[component+'_candidate_mean']=float(np.mean([c['models'][model][component]for c in records]))
 return out
def success(allmetric,single,multi,foldratios,clear):
 r=allmetric['geometric_composite_ratio'];c=allmetric['oracle_capture_fraction'];minimum=r<=.97 and single['geometric_composite_ratio']<1 and multi['geometric_composite_ratio']<=1 and sum(v<1 for v in foldratios)>=3 and c is not None and c>.05 and clear
 if not minimum:return 'NO'
 if r<=.80 and c>=.35:return 'MOONSHOT'
 if r<=.90 and c>=.20 and sum(v<1 for v in foldratios)==4:return 'STRONG_YES'
 if r<=.95 and c>=.10 and multi['geometric_composite_ratio']<1:return 'YES'
 return 'WEAK_YES'

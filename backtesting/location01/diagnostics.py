"""## Executive summary (read this first)

Report prediction skill and unchanged precommitted success gates.
"""
import numpy as np
from scipy.stats import spearmanr

def capture(ratio,oracle_ratio):
    return float((1-ratio)/(1-oracle_ratio))

def metrics(y,pred,baseline,candidate,oracle):
    ratio=float(candidate.sum()/baseline.sum()); perfect=float(oracle.sum()/baseline.sum())
    mse=float(np.mean((y-pred)**2)); variance=float(np.var(y))
    variable=float(np.std(pred))>1e-12
    slope=float(np.cov(y,pred,ddof=0)[0,1]/np.var(pred)) if variable else None
    return {'cells':len(y),'normalized_crps':float(np.mean(candidate)),
        'baseline_normalized_crps':float(np.mean(baseline)),'ratio':ratio,
        'perfect_location_ratio':perfect,'oracle_capture_fraction':capture(ratio,perfect),
        'delta_mse':mse,'delta_r2':float(1-mse/variance),
        'pearson':float(np.corrcoef(y,pred)[0,1]) if variable else None,
        'spearman':float(spearmanr(y,pred).statistic) if variable else None,
        'sign_accuracy':float(np.mean(np.sign(y)==np.sign(pred))),
        'sign_accuracy_convention':'zero prediction only matches exactly zero truth',
        'mean_abs_shift_over_sd':float(np.mean(np.abs(pred))),
        'calibration_intercept':float(np.mean(y)-(0 if slope is None else slope*np.mean(pred))),
        'calibration_slope':slope}

def success(metric,fold_ratios,controls_clear):
    if not (metric['ratio']<=.97 and sum(v<1 for v in fold_ratios)>=3 and
            controls_clear and metric['oracle_capture_fraction']>.05):
        return 'NO'
    r,c=metric['ratio'],metric['oracle_capture_fraction']
    if r<=.80 and c>=.35:return 'MOONSHOT'
    if r<=.90 and c>=.20:return 'STRONG_YES'
    if r<=.95 and c>=.10:return 'YES'
    return 'WEAK_YES'

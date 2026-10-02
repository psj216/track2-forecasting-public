"""## Executive summary (read this first)

A translation may round neighbors to ties. Accept such machine-level ties,
while rejecting nonuniform shifts, scale changes and material order reversals.
The fixed tolerances depend on float64 precision and input magnitude, not scores.
"""
import numpy as np

MULTIPLIER=32
EPS=np.finfo(np.float64).eps

def translation_audit(before,after):
    out={'passed':False,'failures':[]}
    try:
        before=np.asarray(before,dtype=np.float64);after=np.asarray(after,dtype=np.float64)
    except (TypeError,ValueError):
        out['failures']=['not_numeric'];return out
    if before.shape!=after.shape or before.ndim<1 or before.size==0:
        out['failures']=['shape_or_empty'];return out
    if not np.isfinite(before).all() or not np.isfinite(after).all():
        out['failures']=['nonfinite'];return out
    b=before.reshape(len(before),-1);a=after.reshape(len(after),-1);n=len(b)
    with np.errstate(over='ignore',invalid='ignore'):
        delta=a-b;center_shift=np.median(delta,axis=0)
        scale=np.maximum.reduce([np.ones(b.shape[1]),np.max(np.abs(b),axis=0),
                                  np.max(np.abs(a),axis=0),np.abs(center_shift)])
        tolerance=MULTIPLIER*EPS*scale
        shift_residual=np.max(np.abs(delta-center_shift),axis=0)
        bc=b-np.median(b,axis=0);ac=a-np.median(a,axis=0)
        centered_residual=np.max(np.abs(ac-bc),axis=0)
        order=np.argsort(b,axis=0,kind='stable')
        base_gap=np.diff(np.take_along_axis(b,order,axis=0),axis=0)
        candidate_gap=np.diff(np.take_along_axis(a,order,axis=0),axis=0)
        reversals=(base_gap>tolerance)&(candidate_gap < -tolerance)
        vb=np.var(bc,axis=0,ddof=0);va=np.var(ac,axis=0,ddof=0)
        sb=np.mean(bc*bc,axis=0);sa=np.mean(ac*ac,axis=0)
        spread=np.maximum.reduce([np.ones(b.shape[1]),np.max(np.abs(bc),axis=0),np.max(np.abs(ac),axis=0)])
        gamma_n=n*EPS/(1-n*EPS)
        moment_scale=np.maximum.reduce([np.ones(b.shape[1]),vb,va,sb,sa])
        # Squared centered differences vary by <= 2*tau*R+tau**2.
        # Four*tau*R bounds centering and variance effects; 8*gamma_n
        # covers subtract/square/mean reduction roundoff without score tuning.
        moment_tolerance=4*tolerance*spread+tolerance*tolerance+8*gamma_n*moment_scale
    arrays=(center_shift,tolerance,shift_residual,centered_residual,vb,va,sb,sa,moment_tolerance)
    if n*EPS>=1 or any(not np.isfinite(v).all() for v in arrays):
        out['failures']=['nonfinite_arithmetic'];return out
    checks={'uniform_shift':bool(np.all(shift_residual<=tolerance)),
            'centered_geometry':bool(np.all(centered_residual<=tolerance)),
            'no_strict_order_reversal':bool(not reversals.any()),
            'variance':bool(np.all(np.abs(va-vb)<=moment_tolerance)),
            'centered_second_moment':bool(np.all(np.abs(sa-sb)<=moment_tolerance))}
    out.update(passed=bool(all(checks.values())),checks=checks,
               failures=[k for k,v in checks.items() if not v],
               shift_tolerance=tolerance.tolist(),order_tolerance=tolerance.tolist(),
               centered_tolerance=tolerance.tolist(),moment_tolerance=moment_tolerance.tolist(),
               max_shift_residual=float(np.max(shift_residual)),
               max_centered_residual=float(np.max(centered_residual)),
               max_variance_residual=float(np.max(np.abs(va-vb))),
               max_second_moment_residual=float(np.max(np.abs(sa-sb))),
               strict_reversal_count=int(np.count_nonzero(reversals)),
               rounded_tie_count=int(np.count_nonzero((base_gap>0)&(candidate_gap==0))),
               multiplier=MULTIPLIER,epsilon=float(EPS))
    return out

def numerical_geometry_guard(before,after):
    return translation_audit(before,after)['passed']

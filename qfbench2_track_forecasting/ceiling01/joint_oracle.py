"""## Executive summary (read this first)

Optimize only finite draw permutations for the variogram, with three fixed starts.
This is a feasible hindsight construction, not a certified global joint optimum.
The existing toolkit independently rescores the final forecast.
"""

import numpy as np
from qfbench2_common.scoring.crps import variogram_score


def apply(samples, truth, proposals=12000, seed=1901):
    original = np.asarray(samples, dtype=float)
    x = original.reshape(len(original), -1)
    y = np.asarray(truth, dtype=float).reshape(-1)
    n, d = x.shape
    if d == 1:
        return original.copy(), {"status": "NO_JOINT", "accepted": 0}
    sorted_x = np.sort(x, axis=0)
    guided = sorted_x.copy()
    for j in range(d):
        if y[j] < np.median(x[:, j]):
            guided[:, j] = guided[::-1, j]
    starts = [x.copy(), sorted_x.copy(), guided]
    best, best_loss, accepted_total = x.copy(), float(variogram_score(x, y)), 0
    target = np.sqrt(np.abs(y[:, None] - y[None, :]))
    rng = np.random.default_rng(seed)
    for start in starts:
        cur = start.copy()
        means = np.mean(np.sqrt(np.abs(cur[:, :, None] - cur[:, None, :])), axis=0)
        for _ in range(proposals):
            j = int(rng.integers(d))
            r, s = rng.integers(n, size=2)
            if r == s:
                continue
            old = np.sqrt(np.abs(cur[r, j]-cur[r])) + np.sqrt(np.abs(cur[s, j]-cur[s]))
            new = np.sqrt(np.abs(cur[s, j]-cur[r])) + np.sqrt(np.abs(cur[r, j]-cur[s]))
            changed = means[j] + (new-old)/n
            changed[j] = 0.
            gain = np.sum((target[j]-changed)**2 - (target[j]-means[j])**2)
            if gain < -1e-18:
                cur[r, j], cur[s, j] = cur[s, j], cur[r, j]
                means[j] = changed
                means[:, j] = changed
                accepted_total += 1
        loss = float(variogram_score(cur, y))
        if loss < best_loss:
            best, best_loss = cur.copy(), loss
    if not np.array_equal(np.sort(best, axis=0), sorted_x):
        raise AssertionError("Joint permutation changed marginal draws")
    return best.reshape(original.shape), {"status": "FEASIBLE_ORACLE_NOT_GLOBAL_OPTIMUM",
                                          "accepted": accepted_total,
                                          "proposals_per_start": proposals, "starts": 3}

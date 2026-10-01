"""## Executive summary (read this first)

Invert component replacements using the same card geometric aggregation.
Targets are V5.1-relative research ratios, never official Development scores.
"""

from itertools import combinations
from qfbench2_track_forecasting.ceiling01.scorer_adapter import aggregate, composite_from_components


def replace_gain(references, cells, selected, gain):
    return aggregate([composite_from_components(
        {k: (v*(1-gain) if k in selected else v) for k, v in ref.items()}, ref, n)
        for ref, n in zip(references, cells)])


def feasibility(references, cells, observed):
    result = {}
    for target in (.8, .7, .6, .5):
        combos = {}
        for size in (1, 2, 3):
            for selected in combinations(("marginal", "joint", "tail"), size):
                floor = replace_gain(references, cells, selected, 1.)
                required = None
                if floor <= target:
                    lo, hi = 0., 1.
                    for _ in range(55):
                        mid = (lo+hi)/2
                        if replace_gain(references, cells, selected, mid) <= target:
                            hi = mid
                        else:
                            lo = mid
                    required = hi
                combos["+".join(selected)] = {"zero_loss_floor": floor,
                    "possible": required is not None, "required_uniform_fractional_loss_reduction": required}
        result[str(target)] = {"mathematically_possible": True,
            "scope": "RESEARCH_PROXY_ONLY baseline-relative ratio; not official target score",
            "component_combinations": combos,
            "observed_oracle_reaching_target": [k for k,v in observed.items() if v <= target],
            "all_zero_exact_mathematical_score": 0., "floored_research_score": 1e-12}
    return result

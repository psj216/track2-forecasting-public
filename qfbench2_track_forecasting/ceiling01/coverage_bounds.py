"""## Executive summary (read this first)

Describe support of the frozen V13-R2 gate separately from V5.1's coverage.
V5.1 covers all selected cases; gate fallback is not evidence of V5.1 failure.
"""

from qfbench2_track_forecasting.v13.support_gate import supported


def classify(artifact, assets, target_type, frequency):
    yes, reason = supported(artifact, assets, target_type, frequency)
    individual = [supported(artifact, [a], target_type, frequency)[0] for a in assets]
    return {"v51": "fully_modeled", "v13": "fully_modeled" if yes else "exact_v51_fallback",
            "partial_asset_support": bool(any(individual) and not all(individual)),
            "reason": reason, "single_cell": None}

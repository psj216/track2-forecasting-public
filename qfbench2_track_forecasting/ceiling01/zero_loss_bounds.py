"""## Executive summary (read this first)

Set named components to zero and call the same research composite arithmetic.
These substitutions need not correspond to any simultaneously feasible forecast.
"""

from .scorer_adapter import composite_from_components


def replace(reference, cells, zero):
    values = {k: (0. if k in zero else v) for k, v in reference.items()}
    return composite_from_components(values, reference, cells)

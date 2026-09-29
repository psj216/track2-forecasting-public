"""V5.1 whole-draw empirical percentile copula, including stable ties."""

from .rank_copula import percentile_ranks


def rank_worlds(v51_samples):
    return percentile_ranks(v51_samples)

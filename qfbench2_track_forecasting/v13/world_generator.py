"""Assign frozen marginal values to a whole-draw rank matrix."""

from .rank_copula import assign_marginals


def generate(marginal_values, rank_worlds):
    return assign_marginals(marginal_values, rank_worlds)

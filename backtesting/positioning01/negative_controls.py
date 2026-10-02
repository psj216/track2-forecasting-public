"""## Executive summary (read this first)
Freeze past-only report controls and explicitly flag non-identifiable label permutations.
"""
import numpy as np
CONTROLS=('FA','FB','LA','LB','CA','CB')
def donor_index(index,kind,seed=1907):
    if index<1:return None
    return index-1 if kind=='B' else int(np.random.default_rng(seed+index).integers(0,index))
def rotate(values):return list(values[1:])+list(values[:1])

"""## Executive summary (read this first)
Reuse inherited chronological Ridge selection and fixed nonlinear fit without any search.
"""
from ..expectation01.model import ExpectationModel as QuantityModel,choose_alpha
from ..location01.model import ALPHAS,FOLDS,purged_mask,inner_splits,HGB_PARAMS

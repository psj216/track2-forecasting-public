"""## Executive summary (read this first)

Response fitting excludes labels that mature on or after the forecast date.
"""
from qfbench2_track_forecasting.surprise01.response_model import fit_cells
from backtesting.surprise01.validation_eval import prepared_coefficients, coefficients
import pandas as pd


def test_training_maturity():
    prior = dict(event_type='CPI', asset='UST_2Y', horizon=5,
                 origin='2019-01-01', target_end='2019-01-08', surprise=1., q=.2,
                 log_scale_response=.1)
    rows = [prior.copy() for _ in range(24)]
    unsafe = dict(prior, target_end='2020-01-01', q=1e9, log_scale_response=1e9)
    assert fit_cells(rows + [unsafe], '2020-01-01') == fit_cells(rows, '2020-01-01')
    index = prepared_coefficients(pd.DataFrame(rows + [unsafe]))
    b, g, n = coefficients(index, 'CPI', 'UST_2Y', 5, '2020-01-01')
    assert n == 24 and abs(b - .2/1.1) < 1e-12 and abs(g - .1/1.1) < 1e-12

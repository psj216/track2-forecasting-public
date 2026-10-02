"""## Executive summary (read this first)

Use a deterministic one-hot vocabulary, independent of outcomes.
"""
from qfbench2_track_forecasting.thesis01.asset_semantics import family
from .oracle_target import HORIZONS

GROUPS = ('FX', 'Rates', 'Factor/Equity')
ROUTES = {'FX': 'T2-F2', 'Rates': 'T2-F1', 'Factor/Equity': 'T2-F4'}

def metadata(asset, kind, horizon, assets):
    group = family(asset, kind)
    out = {f'M_asset_{a}': float(a == asset) for a in assets}
    out.update({f'M_group_{g}': float(g == group) for g in GROUPS})
    out.update({f'M_horizon_{h}': float(h == horizon) for h in HORIZONS})
    out.update({f'M_kind_{k}': float(k == kind) for k in ('level', 'return', 'log_return')})
    out.update({f'M_route_{r}': float(r == ROUTES[group]) for r in ROUTES.values()})
    return out

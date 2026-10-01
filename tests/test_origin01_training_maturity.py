"""## Executive summary (read this first)

The training builder always truncates source series at the 2023 cutoff and
rejects labels whose end crosses it.
"""

import inspect
from backtesting.origin01.build_training import build


def test_training_enforces_maturity():
    code = inspect.getsource(build)
    assert "loc[:pd.Timestamp(TRAINING_CUTOFF)]" in code
    assert "result[1] > cutoff" in code

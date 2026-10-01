"""## Executive summary (read this first)

Historical training labels and the saved coefficient artifact mature by 2023.
"""

from pathlib import Path
import numpy as np
from backtesting.origin01.fit_propagation import train


def test_artifact_cutoff(tmp_path):
    source = np.ones((40, 2))
    q = np.ones((40, 2, 1))
    path = tmp_path / "train.npz"; out = tmp_path / "model.npz"
    np.savez(path, source=source, q=q, gate=np.ones((40, 2), bool),
             assets=np.array(["a", "b"]), horizons=np.array([5]))
    train(path, out)
    assert np.load(out)["max_target_end"] == np.datetime64("2023-12-31")

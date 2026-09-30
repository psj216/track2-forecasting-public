"""Offline V12 runtime. No fit, label, or post-as-of read occurs here."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

from .artifacts import load
from .joint_features import features
from .world_generator import worlds


class JointEngine:
    def __init__(self, artifact_path: str | Path):
        self.artifact = load(artifact_path)

    def forecast(self, panel: pd.DataFrame, assets: list[str], horizons: list[int],
                 asof: str, draws: int = 500, seed: int = 0,
                 target_type: str = "level") -> tuple[np.ndarray, dict]:
        known = self.artifact["assets"]
        if any(a not in known for a in assets):
            raise ValueError("Untrained decoder asset; use explicit fallback")
        if target_type not in {"level", "log_return"}:
            raise ValueError("Unsupported target type")
        x, g, coverage = features(panel, known, asof,
                                  self.artifact["decoder_target_types"])
        indices = [known.index(a) for a in assets]
        delta = worlds(self.artifact, x, g, coverage, indices, horizons, draws, seed)
        past = panel.loc[pd.to_datetime(panel.date) <= pd.Timestamp(asof)]
        anchors = []
        for a in assets:
            rows = past.loc[past.asset == a].sort_values("date")
            if rows.empty:
                raise ValueError(f"Missing as-of prefix for {a}")
            anchors.append(float(rows.value.iloc[-1]))
        anchors = np.asarray(anchors)[None, None, :]
        if target_type == "level":
            delta += anchors
        # The factor panels use cumulative log-return values; their forecast
        # target is the displacement, not a log of the (possibly negative) index.
        return delta, {"engine": "V12-RECONSTRUCTED", "unsupported_assets":
                       [a for a in assets if a in self.artifact["unsupported_assets"]]}

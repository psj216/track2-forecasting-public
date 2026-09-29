"""A/B/C reconstructed dependence engines with whole-card baseline fallback."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

from qfbench2_track_forecasting.v12.artifacts import load
from qfbench2_track_forecasting.v12.joint_features import features
from .copula_mixture import mix
from .historical_copula_bank import HistoricalBank
from .marginal_adapter import conditional_marginals
from .rank_copula import assign_marginals, percentile_ranks
from .state_retrieval import state_vector
from .support_gate import supported
from .v51_copula import rank_worlds


class CopulaEngine:
    def __init__(self, artifact_path: str | Path, bank_path: str | Path | None = None):
        self.artifact = load(artifact_path)
        self.bank = HistoricalBank(bank_path) if bank_path else None

    def forecast(self, v51_samples: np.ndarray, panel: pd.DataFrame, assets: list[str],
                 horizons: list[int], asof: str, target_type: str = "level",
                 target_frequency: str = "daily", seed: int = 0) -> tuple[dict[str, np.ndarray], dict]:
        v51 = np.asarray(v51_samples, dtype=float)
        if v51.ndim != 3 or v51.shape[1:] != (len(horizons), len(assets)) or not np.isfinite(v51).all():
            raise ValueError("V5.1 baseline tensor shape or finiteness mismatch")
        yes, reason = supported(self.artifact, assets, target_type, target_frequency)
        if not yes:
            return {name: v51.copy() for name in "ABC"}, {"fallback": "whole_card_v51", "reason": reason}
        n = len(v51)
        marginal = conditional_marginals(self.artifact, panel, assets, horizons, asof,
                                         n, seed, target_type)
        v51_rank = rank_worlds(v51)
        bank_rank = None
        if self.bank is not None:
            x, _, coverage = features(panel, self.artifact["assets"], asof)
            bank_scores = self.bank.rank_worlds(state_vector(x, coverage), asof,
                                                 assets, horizons, n, seed + 2)
            if bank_scores is not None:
                # Repeated prototype draws have ties; a stable finite rank
                # permutation is required for exact marginal preservation.
                bank_rank = percentile_ranks(bank_scores)
        if bank_rank is None:
            bank_rank = v51_rank
        ranks = {"A": v51_rank, "B": bank_rank,
                 "C": percentile_ranks(mix(v51_rank, bank_rank, seed + 3))}
        output = {name: assign_marginals(marginal, rank)
                  for name, rank in ranks.items()}
        return output, {"fallback": None, "bank_used": self.bank is not None and
                        bank_rank is not v51_rank, "marginal_source": "reconstructed_v12"}

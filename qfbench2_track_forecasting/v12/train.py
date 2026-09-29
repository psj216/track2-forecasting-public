"""Offline reconstruction from public panels; revised history is not PIT certified."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

from .joint_dataset import HORIZONS, JointDataset, make_dataset
from .latent_state import fit_classifier, fit_factors, psd
from .residual_model import estimate_df
from .state_transition import state_features


def fit(data: JointDataset, cutoff: str = "2008-12-31") -> dict:
    valid = data.fit_mask(cutoff)
    h21 = HORIZONS.index(21)
    eligible = valid[:, h21].sum(axis=1) >= 3
    if eligible.sum() < 25:
        raise ValueError("Insufficient cutoff-safe synchronized training origins")
    y21 = data.y[eligible, h21]
    m21 = valid[eligible, h21]
    mean, loading, scores, explained = fit_factors(y21, m21)
    # An ordinal state learned from the future first PCA axis, never a runtime input.
    boundaries = np.quantile(scores[:, 0], [0.1, 0.3, 0.7, 0.9])
    labels = np.searchsorted(boundaries, scores[:, 0])
    state_inputs = np.array([state_features(data.x[i], data.g[i],
                                    data.x[i, :, 18] >= 21 / 252, 21)
                             for i in np.flatnonzero(eligible)])
    center = np.mean(state_inputs, axis=0)
    scale = np.maximum(np.std(state_inputs, axis=0), 1e-4)
    center[0] = 0.; scale[0] = 1.
    z = np.clip((state_inputs - center) / scale, -8, 8); z[:, 0] = 1.
    logits = fit_classifier(z, labels)
    states_cov, state_location = [], []
    for state in range(5):
        subset = scores[labels == state]
        loc = np.mean(subset, axis=0) if len(subset) else np.zeros(5)
        cov = np.cov(subset.T) if len(subset) > 5 else np.eye(5)
        shrink = 0.25 if state in (0, 4) else 0.15
        cov = psd((1-shrink)*cov + shrink*np.diag(np.maximum(np.diag(cov), 1e-6)))
        states_cov.append(cov.tolist()); state_location.append(loc.tolist())
    residual = np.where(m21, y21 - scores @ loading.T - mean, 0.)
    residual_sd = np.sqrt(np.sum(residual ** 2, axis=0) / np.maximum(m21.sum(axis=0), 1))
    residual_sd = np.maximum(residual_sd, np.median(residual_sd[residual_sd > 0]) if np.any(residual_sd > 0) else 0.01)
    # Ridge pooled across assets. The long expert is deliberately generic.
    design, response = [], []
    for i in np.flatnonzero(eligible):
        for j, horizon in enumerate(HORIZONS):
            if horizon < 126:
                continue
            for a in np.flatnonzero(valid[i, j]):
                design.append([1., data.x[i, a, 9], data.x[i, a, 7], data.x[i, a, 17]])
                response.append(data.y[i, j, a] - mean[a] * np.sqrt(horizon / 21))
    coef = np.linalg.solve(np.asarray(design).T @ design + 100 * np.eye(4),
                           np.asarray(design).T @ response) if design else np.zeros(4)
    counts = valid.sum(axis=(0, 1)).astype(int)
    # The old negative OOF slope clipped to zero; the archived coefficient is not recoverable.
    return dict(schema="v12-reconstructed-1", origin="public revised panels; NOT original artifact",
                fit_cutoff=cutoff, assets=data.assets, horizons=list(HORIZONS),
                fit_origins=int(eligible.sum()), observed_origin_count=len(data.dates),
                fit_target_cells=int(valid.sum()), fit_cells_by_asset=counts.tolist(),
                pca_explained=explained, feature_center=center.tolist(), feature_scale=scale.tolist(),
                state_logits=logits.tolist(), state_prior=np.bincount(labels, minlength=5).astype(float).__truediv__(len(labels)).tolist(),
                state_location=state_location, state_covariance=states_cov,
                decoder_loadings=loading.tolist(), decoder_mean=mean.tolist(),
                residual_sd=residual_sd.tolist(), student_df=estimate_df(residual).real,
                long_expert=coef.tolist(), location_reliability=0.,
                coverage_floor=float(np.quantile(state_inputs[:, -2], 0.1)),
                unsupported_assets=[a for a,c in zip(data.assets,counts) if c == 0])


def load_public_panels(root: Path) -> tuple[pd.DataFrame, dict[str, str]]:
    """Deduplicate identical public prefixes; no future card outcome is read."""
    frames, first_target = [], {}
    for unit in sorted(root.glob("*/")):
        spec = unit / "forecast_spec.json"
        if spec.exists():
            doc = json.loads(spec.read_text())
            # as_of is in card.toml, and eligibility is conservative if absent.
            import tomllib
            card = unit / "card.toml"
            if card.exists():
                meta = tomllib.loads(card.read_text())
                asof = str(meta.get("provenance", {}).get("data_cutoff", "2100-01-01"))
                for asset in doc.get("targets", {}).get("asset_ids", []):
                    first_target[asset] = min(first_target.get(asset, "2100-01-01"), asof)
        for path in unit.glob("*.parquet"):
            if "monthly" not in path.name and "macro" not in path.name:
                frame = pd.read_parquet(path)
                if {"date", "asset", "value"} <= set(frame):
                    frames.append(frame[["date", "asset", "value"]])
    if not frames:
        raise ValueError("No public panel files found")
    panel = pd.concat(frames, ignore_index=True).drop_duplicates(["date", "asset"], keep="first")
    panel["date"] = pd.to_datetime(panel.date)
    return panel, first_target


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--units", type=Path, default=Path("units"))
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    panel, first = load_public_panels(args.units)
    assets = sorted(a for a in panel.asset.unique() if first.get(a, "2100-01-01") != "2100-01-01")
    dataset = make_dataset(panel, assets, eligibility=first)
    artifact = fit(dataset)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k:artifact[k] for k in ("fit_origins", "observed_origin_count", "fit_target_cells", "unsupported_assets")}))


if __name__ == "__main__":
    main()

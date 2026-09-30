"""Build a new private rank bank from currently public, revised panel history."""

import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

from qfbench2_track_forecasting.v12.joint_dataset import make_dataset
from qfbench2_track_forecasting.v12.train import load_public_panels
from qfbench2_track_forecasting.v13.state_retrieval import state_vector


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--units", type=Path, default=Path("units"))
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    a = p.parse_args()
    if a.out.is_relative_to(Path.cwd()) or a.out.resolve().is_relative_to(Path.cwd()):
        raise SystemExit("Private outcome bank must be written outside the Git repository")
    artifact = json.loads(a.artifact.read_text())
    panel, eligibility = load_public_panels(a.units)
    dataset = make_dataset(panel, artifact["assets"], eligibility=eligibility,
                           target_types=artifact["decoder_target_types"])
    mask = dataset.fit_mask(artifact["fit_cutoff"])
    selected = mask.any(axis=(1, 2))
    state = np.array([state_vector(x, x[:, 18] >= 21 / 252)
                      for x in dataset.x[selected]])
    a.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(a.out, dates=np.array(dataset.dates, dtype="datetime64[ns]")[selected],
                        target_end=dataset.target_end[selected], values=dataset.y[selected],
                        mask=mask[selected], state=state, assets=np.array(dataset.assets),
                        horizons=np.array(artifact["horizons"]))
    digest = hashlib.sha256(a.out.read_bytes()).hexdigest()
    manifest = {"reconstruction": True, "private_bank_sha256": digest,
                "v12_artifact_sha256": hashlib.sha256(a.artifact.read_bytes()).hexdigest(),
                "origin_count": int(selected.sum()), "fit_target_cells": int(mask[selected].sum()),
                "assets": len(dataset.assets), "horizons": len(artifact["horizons"]),
                "point_in_time_vintage_verified": False,
                "archived_bank_available": False}
    a.manifest.parent.mkdir(parents=True, exist_ok=True)
    a.manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()

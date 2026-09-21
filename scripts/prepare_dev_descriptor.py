"""## Executive summary (read this first)

Prepare a Development-only descriptor draft for an already-published image digest.
The official v2.4.3 pack CLI derives the team identity and seals the final descriptor.
This script never receives a Team Key and does not claim to verify registry availability.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from qfbench2_common.contracts.descriptor import SubmissionDescriptor, seal_descriptor_digest

HOUSE_MODEL = {
    "name": "nvidia/nemotron-3-super-120b-a12b",
    "version": "rl-030326-fp8",
    "revision": "rl-030326-fp8",
    "training_cutoff": "unpublished",
    "access": "api",
}


def prepare_descriptor(registry: str, repository: str, digest: str) -> dict[str, Any]:
    body = {
        "schema_version": "1.0.0",
        "interface_version": "2.0",
        "competition_id": "agenthon2026-forecasting-dev",
        "track": "forecasting",
        "phase": "dev",
        "category": "api",
        "image": {"registry": registry, "repository": repository, "digest": digest},
        "image_access": "public",
        "models": [dict(HOUSE_MODEL)],
        "license": "MIT",
    }
    # Validate image and fixed fields with the canonical parser. This temporary identity
    # is never written: pack refuses an incorrect predeclared team_id, so omit it in drafts.
    checked = dict(body, team_id="team-validation-only")
    SubmissionDescriptor.from_mapping(seal_descriptor_digest(checked))
    return body


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default="docker.io")
    parser.add_argument("--repository", required=True, help="your public namespace/repository")
    parser.add_argument("--digest", required=True, help="published sha256 digest, never a tag")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    body = prepare_descriptor(args.registry, args.repository, args.digest)
    with args.out.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(body, indent=2, sort_keys=True) + "\n")
    print(f"Wrote draft {args.out}; not uploadable until qfbench2 submission pack succeeds.")


if __name__ == "__main__":
    main()

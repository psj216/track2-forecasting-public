"""Executive summary: fail closed when delivery observations or manual-run readiness are missing."""

from pathlib import Path
import hashlib

SOURCE = "47194f28d5188b87cdca1d591d86b9eeda86f7cf"
DIGEST = "sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874"
IMAGE = "docker.io/jotj216/track2-f4-approved@" + DIGEST
COMMON_SHA = "dfa92d242908bba4a448218b9c10ae391238d10d"
PARENT = "9ba448111c2988d56066bd0d6ba0e57c6120e88b"
WORKFLOW = ".github/workflows/v51-safe-delivery09-recovery.yml"
REQUIRED_GATES = (
    "exact_image", "source_identity", "architecture", "runtime", "schema",
    "route_invariants", "determinism", "security", "resources", "descriptor",
)


def readiness(observations: dict) -> bool:
    """A missing observation is a failed readiness gate, never an inferred success."""
    return all(observations.get(gate) is True for gate in REQUIRED_GATES)


def verified_blob(path: Path, expected: str) -> bool:
    """Compare exact Git blob identity without executing a forecast or loading truth."""
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest() == expected


def manual_registration(default_paths: list[str]) -> dict:
    """Default-branch presence is required by GitHub's workflow_dispatch contract."""
    available = WORKFLOW in default_paths
    return {"default_branch_workflow_present": available,
            "registration_ready": available,
            "reason": None if available else "MANUAL_WORKFLOW_ABSENT_FROM_DEFAULT_BRANCH"}

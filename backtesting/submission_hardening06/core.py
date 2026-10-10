"""Executive summary: enforce evidence-only delivery gates without forecasting or submission."""
from hashlib import sha256
from pathlib import PurePosixPath

PARENT = "8d06fcff48b9cc838d502f4c7b08fa2618015112"
PARENT_PRE = "a80d1b431e4b9ff53d9abfd653b681b64fa006fa"
MAIN = "e1b5cf3b3a87966e902332ef3cc5c0ed2dbffee8"
BRANCH = "track2/submission-hardening-06"
COMMON = "2.4.2"
GATES = (
    "receipt_linked", "unique_historical_identity", "source_lineage",
    "runtime_dependencies_frozen", "deterministic_runtime", "output_equivalence",
    "schema_and_resources", "security", "descriptor_package",
)


def digest(data):
    return sha256(data).hexdigest()


def verify_protection(root, files):
    changed = [name for name, expected in files.items()
               if not (root / name).is_file() or digest((root / name).read_bytes()) != expected]
    if changed:
        raise ValueError(f"Protected files changed: {changed}")


def rebuild_allowed(evidence):
    return all(evidence.get(k) is True for k in (
        "unique_historical_identity", "source_lineage", "runtime_dependencies_frozen",
        "entrypoint_config_known", "runtime_contract_known", "source_unchanged",
    ))


def readiness(evidence):
    missing = [k for k in GATES if evidence.get(k) is not True]
    if not missing:
        return "READY_EXACT_REFERENCE" if evidence.get("original_image") is True else "READY_REBUILT_EQUIVALENT"
    if any(k in missing for k in ("receipt_linked", "unique_historical_identity", "source_lineage",
                                  "runtime_dependencies_frozen")):
        return "NOT_READY_MISSING_PROVENANCE"
    if evidence.get("policy_blocked") is True:
        return "NOT_READY_POLICY_OR_DEADLINE_BLOCKED"
    if evidence.get("numeric_mismatch") is True:
        return "NOT_READY_OUTPUT_MISMATCH"
    if evidence.get("nondeterministic") is True:
        return "NOT_READY_NONDETERMINISTIC"
    if evidence.get("runtime_failure") is True:
        return "NOT_READY_RUNTIME_FAILURE"
    return "INCONCLUSIVE"


def repeated_output_equivalent(runs):
    """Require at least three independently measured, complete output manifests."""
    return (len(runs) >= 3 and len({r.get("execution_id") for r in runs}) == len(runs)
            and all(r.get("measured") is True and r.get("exit_code") == 0 for r in runs)
            and all(r.get("files") for r in runs)
            and all(r["files"] == runs[0]["files"] for r in runs))


def runtime_gates_verified(r):
    required = ("measured", "finite", "schema", "shape", "domain", "joint_geometry",
                "absolute_output_mount", "offline", "non_root", "read_only", "as_of")
    return (all(r.get(k) is True for k in required)
            and isinstance(r.get("draws"), int) and r["draws"] >= max(200, r.get("card_min_draws", 200)))


def package_names_safe(names):
    forbidden = {".env", "team-key", "credentials", "answer_key", "realized.parquet"}
    return all(not PurePosixPath(n).is_absolute() and ".." not in PurePosixPath(n).parts
               and not any(part in forbidden for part in PurePosixPath(n).parts) for n in names)

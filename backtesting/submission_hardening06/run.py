"""Executive summary: verify inherited bytes and inventory this evidence-only audit."""
import json
from pathlib import Path

from .core import digest, verify_protection

ROOT = Path(__file__).resolve().parents[2]
RESULTS = Path(__file__).resolve().parent / "results"


def refresh_manifest():
    protected = json.loads((RESULTS / "protected_source_manifest.json").read_text())
    verify_protection(ROOT, protected["all_parent_files"])
    paths = sorted([*RESULTS.rglob("*"), RESULTS.parent / "STATUS.json",
                    ROOT / "SUBMISSION-HARDENING-06-report.md",
                    RESULTS.parent / "core.py", RESULTS.parent / "run.py",
                    ROOT / "tests/test_submission_hardening06.py"])
    files = {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in paths
             if p.is_file() and p.name != "artifact_manifest.json" and "__pycache__" not in p.parts}
    manifest = {"executive_summary": "SHA-256 inventory of non-secret hardening materials.",
                "files": files, "count": len(files), "self_hash_excluded": True,
                "protected_parent_files_unchanged": True}
    (RESULTS / "artifact_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    print(json.dumps({"stage": "manifest", "files": refresh_manifest()["count"]}))

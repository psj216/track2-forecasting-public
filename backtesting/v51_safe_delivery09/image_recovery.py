"""Executive summary: recover only the exact public preparation image; do not run forecasts."""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

DIGEST = "sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874"
IMAGE = "docker.io/jotj216/track2-f4-approved@" + DIGEST
SOURCE = "47194f28d5188b87cdca1d591d86b9eeda86f7cf"


def recover(out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    result = {"executive_summary": "Current anonymous exact-digest pull only; no historical official identity claim.",
              "image_reference": IMAGE, "required_digest": DIGEST,
              "source_SHA": SOURCE, "EXACT_PREPARATION_IMAGE_RECOVERED": False,
              "forecast_runs": 0, "scores_computed": 0, "submissions": 0}
    if not shutil.which("docker"):
        result.update(status="DOCKER_EXECUTABLE_UNAVAILABLE", exit_code=127)
    else:
        with tempfile.TemporaryDirectory(prefix="anonymous-docker-") as config:
            print("stage=exact_pull completed=0/1 image=" + IMAGE, flush=True)
            try:
                proc = subprocess.run(["docker", "--config", config, "pull", "--platform", "linux/amd64", IMAGE],
                                      capture_output=True, text=True, timeout=360)
                (out / "exact_pull.log").write_text(proc.stdout + proc.stderr)
                result.update(exit_code=proc.returncode, status="EXACT_PULL_FAILED")
                if proc.returncode == 0:
                    inspect = json.loads(subprocess.check_output(["docker", "image", "inspect", IMAGE], text=True, timeout=30))[0]
                    assert any(r.endswith("@" + DIGEST) for r in inspect["RepoDigests"]), "Digest mismatch"
                    assert inspect["Architecture"] == "amd64" and inspect["Os"] == "linux", "Architecture mismatch"
                    cfg = inspect["Config"]
                    env = dict(e.split("=", 1) for e in cfg.get("Env", []) if "=" in e)
                    assert env.get("FORECAST_MODE") == "text-first-v5.1", "Mode mismatch"
                    allowed = {"PATH", "LANG", "PYTHON_VERSION", "PYTHON_SHA256", "PYTHONDONTWRITEBYTECODE", "PYTHONUNBUFFERED", "PIP_NO_CACHE_DIR", "FORECAST_MODE", "PYTHONPATH", "GPG_KEY"}
                    result.update(status="EXACT_IMAGE_RECOVERED", EXACT_PREPARATION_IMAGE_RECOVERED=True,
                                  RepoDigests=inspect["RepoDigests"], image_ID=inspect["Id"],
                                  architecture=inspect["Architecture"], OS=inspect["Os"], created=inspect["Created"],
                                  layers=inspect["RootFS"]["Layers"], labels=cfg.get("Labels"),
                                  entrypoint=cfg.get("Entrypoint"), CMD=cfg.get("Cmd"),
                                  user=cfg.get("User"), working_directory=cfg.get("WorkingDir"),
                                  environment={k: v if k in allowed else "REDACTED_PENDING_SECURITY_AUDIT" for k, v in env.items()},
                                  unknown_environment_keys=sorted(set(env) - allowed),
                                  historical_official_identity=False)
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, AssertionError, ValueError, KeyError) as exc:
                result.update(status="EXACT_IMAGE_RECOVERY_ERROR", error=str(exc))
    (out / "recovered_image_manifest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("stage=exact_pull completed=1/1 status=" + result["status"], flush=True)
    return 0 if result["EXACT_PREPARATION_IMAGE_RECOVERED"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    raise SystemExit(recover(parser.parse_args().out))

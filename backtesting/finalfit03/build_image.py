"""## Executive summary (read this first)
Build and preserve a standalone local image; never authenticate or push to a registry.
"""

import hashlib
import json
import os
import pathlib
import subprocess
import time
import traceback

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(os.environ["RUNNER_TEMP"]) / "ff03-build"
OUT.mkdir(exist_ok=True)
BASE = (
    "docker.io/jotj216/track2-f4-approved@sha256:0b9b08d8a6b59eca262d7"
    "7778d2b2a9b33bb938ab68c4db8f71538302f3bf874"
)
TAG = "finalfit03-local:" + os.environ["GITHUB_SHA"]
receipt = dict(
    executive_summary="Standalone local candidate image build; no registry push.",
    source_sha=os.environ["GITHUB_SHA"],
    base_image=BASE,
    local_tag=TAG,
    registry_push=False,
    completed=False,
    steps=[],
)


def save():
    (OUT / "build-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")


def run(args, name, timeout=180):
    start = time.monotonic()
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    (OUT / (name + ".log")).write_text(p.stdout + p.stderr)
    receipt["steps"].append(
        dict(name=name, command=args, exit_code=p.returncode, wall_seconds=time.monotonic() - start)
    )
    save()
    print(name, p.returncode, flush=True)
    if p.returncode:
        raise RuntimeError(name + " failed")
    return p.stdout


try:
    config = OUT / "anonymous"
    config.mkdir(exist_ok=True)
    os.environ["DOCKER_CONFIG"] = str(config)
    run(["docker", "pull", "--platform=linux/amd64", BASE], "anonymous-pull")
    run(
        [
            "docker",
            "build",
            "--platform=linux/amd64",
            "--build-arg",
            "SOURCE_SHA=" + os.environ["GITHUB_SHA"],
            "-t",
            TAG,
            "-f",
            str(ROOT / "backtesting/finalfit03/Dockerfile"),
            str(ROOT / "backtesting/finalfit03"),
        ],
        "standalone-build",
        300,
    )
    o = json.loads(run(["docker", "image", "inspect", TAG], "image-inspect"))[0]
    assert (o["Os"], o["Architecture"]) == ("linux", "amd64") and not o["Config"].get("Volumes")
    assert o["Config"]["Labels"]["qfbench2.interface_version"] == "2.0"
    assert o["Config"]["User"] == "1000"
    receipt["image_id"] = o["Id"]
    receipt["oci"] = o
    receipt["registry_digest"] = None
    code = (
        "import json,pathlib,hashlib,importlib.metadata as m; p=pathlib.Pa"
        "th('/opt/qfbench2_track_forecasting'); q=pathlib.Path('/opt/final"
        "fit03'); print(json.dumps({'production':{str(f.relative_to(p)):ha"
        "shlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*.py')"
        "},'wrapper':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() fo"
        "r f in q.glob('*.py')},'dependencies':{d.metadata['Name']:d.versi"
        "on for d in m.distributions()}}))"
    )
    identity = json.loads(
        run(
            [
                "docker",
                "run",
                "--rm",
                "--network=none",
                "--read-only",
                "--tmpfs",
                "/tmp",
                TAG,
                "python3",
                "-c",
                code,
            ],
            "internal-code-and-dependencies",
        )
    )
    frozen = ROOT / "frozen-safe/qfbench2_track_forecasting"
    assert identity["production"] == {
        str(f.relative_to(frozen)): hashlib.sha256(f.read_bytes()).hexdigest()
        for f in frozen.rglob("*.py")
    }
    for name, digest in identity["wrapper"].items():
        assert (
            digest
            == hashlib.sha256((ROOT / "backtesting/finalfit03" / name).read_bytes()).hexdigest()
        )
    receipt["identity"] = identity
    receipt["production_source_match"] = True
    run(
        [
            "docker",
            "run",
            "--rm",
            "--network=none",
            "--read-only",
            "--tmpfs",
            "/tmp",
            TAG,
            "forecast",
            "--help",
        ],
        "official-command-interface",
    )
    run(
        ["docker", "save", "--output", str(OUT / "candidate-image.tar"), TAG], "preserve-image", 180
    )
    run(["gzip", "-1", str(OUT / "candidate-image.tar")], "compress-image", 180)
    archive = OUT / "candidate-image.tar.gz"
    h = hashlib.sha256()
    with archive.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    receipt["archive_sha256"] = h.hexdigest()
    receipt["archive_bytes"] = archive.stat().st_size
    receipt["completed"] = True
except Exception:
    receipt["error"] = traceback.format_exc()
finally:
    save()
raise SystemExit(0 if receipt["completed"] else 1)

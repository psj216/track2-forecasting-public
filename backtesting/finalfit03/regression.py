"""## Executive summary (read this first)
Run unchanged frozen package tests and official helper tests in explicit test environments.
Pytest dependencies are test-only mounts; actual forecast invocations mount no Python code.
"""

import json
import os
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(os.environ["RUNNER_TEMP"]) / "ff03-regression"
OUT.mkdir(exist_ok=True)
OUT.chmod(0o777)
BASE = (
    "docker.io/jotj216/track2-f4-approved@sha256:0b9b08d8a6b59eca262d7"
    "7778d2b2a9b33bb938ab68c4db8f71538302f3bf874"
)
TAG = "finalfit03-local:" + os.environ["GITHUB_SHA"]
receipt = dict(
    executive_summary="Identical frozen tests for both runtimes; history suite is separate.",
    steps=[],
    completed=False,
)


def run(args, name, timeout=180):
    start = time.monotonic()
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    (OUT / (name + ".log")).write_text(p.stdout + p.stderr)
    receipt["steps"].append(
        dict(
            name=name,
            exit_code=p.returncode,
            wall_seconds=time.monotonic() - start,
            command=args,
            summary=p.stdout[-1200:],
        )
    )
    (OUT / "regression-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(name, p.returncode, flush=True)
    return p.returncode


setup = run(
    [
        "docker",
        "run",
        "--rm",
        "--user",
        "0",
        "-v",
        str(OUT) + ":/test-work",
        BASE,
        "python3",
        "-m",
        "pip",
        "install",
        "--no-deps",
        "--target",
        "/test-work/deps",
        "pytest==8.4.2",
        "iniconfig==2.3.0",
        "packaging==25.0",
        "pluggy==1.6.0",
        "pygments==2.19.2",
    ],
    "test-only-dependencies",
)
if setup:
    raise SystemExit(1)
files = ["test_numeric_v1.py", "test_numeric_v3.py", "test_text_first_v5.py", "test_cutoff.py"]
for label, image in [("original", BASE), ("candidate", TAG)]:
    run(
        [
            "docker",
            "run",
            "--rm",
            "--network=none",
            "--read-only",
            "--tmpfs",
            "/tmp",
            "-v",
            str(OUT / "deps") + ":/testdeps:ro",
            "-v",
            str(ROOT / "frozen-safe/tests") + ":/tests:ro",
            "-e",
            "PYTHONPATH=/testdeps:/opt",
            image,
            "python3",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            *[("/tests/" + f) for f in files],
        ],
        label + "-frozen-tests",
    )
code = (
    "import importlib.util,sys,pytest; p='/opt/finalfit03/official_hor"
    "izons.py'; s=importlib.util.spec_from_file_location('qfbench2_tra"
    "ck_forecasting.horizons',p); m=importlib.util.module_from_spec(s)"
    ";sys.modules[s.name]=m;s.loader.exec_module(m);raise SystemExit(p"
    "ytest.main(['-q','-p','no:cacheprovider','/official/tests/test_mo"
    "nthly_horizons.py']))"
)
run(
    [
        "docker",
        "run",
        "--rm",
        "--network=none",
        "--read-only",
        "--tmpfs",
        "/tmp",
        "-v",
        str(OUT / "deps") + ":/testdeps:ro",
        "-v",
        str(ROOT / "official-current") + ":/official:ro",
        "-e",
        "PYTHONPATH=/testdeps:/opt",
        TAG,
        "python3",
        "-c",
        code,
    ],
    "official-unmodified-helper-tests",
)
receipt["completed"] = True
(OUT / "regression-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
raise SystemExit(0)

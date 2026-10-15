"""## Executive summary (read this first)
Fail closed on candidate expectations; compare exact input/output hashes to preserved original runs.
The original receipt is explicitly historical and is not counted as new execution.
"""

import argparse
import json
import os
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser()
p.add_argument("--group", required=True)
args = p.parse_args()
work = pathlib.Path(os.environ["RUNNER_TEMP"]) / "ff03-candidate"
c = json.loads((work / "container-receipt.json").read_text())
o = json.loads(
    (
        ROOT / "backtesting/finalfit03/results" / ("baseline-current-" + args.group + ".json")
    ).read_text()
)
result = dict(
    executive_summary="Standalone candidate versus preserved original inputs; no scoring.",
    group=args.group,
    candidate_run=os.environ["GITHUB_RUN_ID"],
    original_run=o["run_id"],
    completed=False,
    kernel_checks=[],
)
try:
    assert c["completed"] and all(r["pass"] for r in c["forecast_processes"])
    assert c["input_manifest"] == o["input_manifest"], "A/B input bytes changed."
    if args.group == "monthly":
        assert c["official_inputs"] == o["official_inputs"]
    before = {(r["name"], r["repetition"]): r for r in o["forecast_processes"]}
    result["ab"] = [
        dict(
            name=r["name"],
            repetition=r["repetition"],
            same_files=r["output_files"] == before[(r["name"], r["repetition"])]["output_files"],
            same_exit=r["forecast_exit_code"]
            == before[(r["name"], r["repetition"])]["forecast_exit_code"],
        )
        for r in c["forecast_processes"]
    ]
    assert all(c["determinism"].values())
    if args.group == "daily":
        assert all(r["same_files"] and r["same_exit"] for r in result["ab"])
    else:
        for test in [
            "backtesting/finalfit02/test_monthly_contract.py",
            "backtesting/finalfit03/test_release_boundaries.py",
        ]:
            q = subprocess.run(
                ["python3", str(ROOT / test), str(work / "container-receipt.json")],
                capture_output=True,
                text=True,
                timeout=30,
            )
            result.setdefault("semantic_assertions", []).append(
                dict(test=test, exit_code=q.returncode, stdout=q.stdout, stderr=q.stderr)
            )
            assert q.returncode == 0
        image = "finalfit03-local:" + os.environ["GITHUB_SHA"]
        for name in [
            "monthly-a",
            "monthly-b",
            "month-start",
            "month-end",
            "lagged-anchor",
            "nonconsecutive",
            "multi-monthly",
            "heterogeneous",
            "heterogeneous-anchor",
        ]:
            argv = [
                "docker",
                "run",
                "--rm",
                "--network=none",
                "--read-only",
                "--tmpfs",
                "/tmp",
                "-v",
                str(ROOT / "backtesting/finalfit03") + ":/audit:ro",
                "-v",
                str(work / "inputs" / name) + ":/input:ro",
                "-v",
                str(work / "outputs" / name / "1") + ":/output:ro",
                image,
                "python3",
                "/audit/kernel_check.py",
                "/input",
                "/output",
            ]
            q = subprocess.run(argv, capture_output=True, text=True, timeout=30)
            result["kernel_checks"].append(
                dict(name=name, exit_code=q.returncode, stdout=q.stdout, stderr=q.stderr)
            )
            assert q.returncode == 0
        lookup = {r["name"]: r for r in c["forecast_processes"] if r["repetition"] == 1}
        assert (
            lookup["month-start"]["output_files"]["forecast.parquet"]
            == lookup["month-end"]["output_files"]["forecast.parquet"]
        )
    name = "f1-ust" if args.group == "daily" else "monthly-a"
    image = "finalfit03-local:" + os.environ["GITHUB_SHA"]
    command = [
        "docker",
        "run",
        "--rm",
        "--network=none",
        "--read-only",
        "--tmpfs",
        "/tmp",
        "-v",
        str(ROOT / "common-current/common") + ":/current-common:ro",
        "-v",
        str(work / "inputs" / name) + ":/input:ro",
        "-e",
        "PYTHONPATH=/current-common:/opt",
        image,
        "python3",
        "-m",
        "qfbench2_common.cli",
        "card",
        "validate",
        "/input",
    ]
    check = subprocess.run(command, capture_output=True, text=True, timeout=30)
    result["official_v261_card_cli"] = dict(
        exit_code=check.returncode, stdout=check.stdout, stderr=check.stderr
    )
    assert check.returncode == 0
    result["exact_ab_inputs"] = True
    result["completed"] = True
except Exception:
    import traceback

    result["error"] = traceback.format_exc()
finally:
    (work / "postcheck-receipt.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
raise SystemExit(0 if result["completed"] else 1)

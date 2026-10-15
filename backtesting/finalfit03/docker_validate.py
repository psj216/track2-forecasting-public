"""## Executive summary (read this first)
Anonymous immutable-image compatibility audit. No image build, scoring, login or submission.
The workflow succeeding means evidence collection completed, not all compatibility gates passed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import time
import tomllib
import traceback

IMAGE = (
    "docker.io/jotj216/track2-f4-approved@"
    "sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874"
)
ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOLS = pathlib.Path(__file__).parent
SECRET = re.compile(
    r"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[A-Z0-9]{16}|"
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    global IMAGE
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", choices=["daily", "monthly"], required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--candidate", action="store_true")
    args = parser.parse_args()
    if args.candidate:
        IMAGE = "finalfit03-local:" + os.environ["GITHUB_SHA"]
    work = args.out.resolve()
    work.mkdir(parents=True, exist_ok=True)
    work.chmod(0o777)
    evidence = dict(
        executive_summary="Exact-image Docker evidence; synthetic tests do not prove performance.",
        source_sha=os.environ.get("GITHUB_SHA"),
        run_id=os.environ.get("GITHUB_RUN_ID"),
        group=args.group,
        image=IMAGE,
        anonymous_pull=True,
        official_source_sha="b9c663d239a0e6b86ebd3f3f2d5aead88516067d",
        shared_source_sha="03c50a0036aaf72675d353aef4c7c01ca86d1fcf",
        forecast_processes=[],
        completed=False,
        safe_image_modified=False,
    )
    evidence["candidate_code_overlay"] = False
    evidence["standalone_candidate"] = args.candidate

    def save():
        (work / "container-receipt.json").write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n"
        )

    def command(argv, name, timeout=90):
        start = time.monotonic()
        try:
            p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
            code, stdout, stderr = p.returncode, p.stdout, p.stderr
        except subprocess.TimeoutExpired:
            code, stdout, stderr = 124, "", "bounded command timeout"
        result = dict(
            command=argv,
            exit_code=code,
            wall_seconds=time.monotonic() - start,
            stdout=SECRET.sub("[REDACTED]", stdout),
            stderr=SECRET.sub("[REDACTED]", stderr),
        )
        (work / (name + ".json")).write_text(json.dumps(result, indent=2))
        print(name, code, round(result["wall_seconds"], 2), flush=True)
        return result

    def docker(extra_mounts=(), validator=False, tooling=False):
        argv = [
            "docker",
            "run",
            "--rm",
            "--network=none",
            "--read-only",
            "--tmpfs",
            "/tmp:rw,size=512m",
            "--cpus=2",
            "--memory=4g",
            "--pids-limit=256",
            "--security-opt=no-new-privileges",
        ]
        if tooling or validator:
            argv += [
                "-v",
                str(TOOLS) + ":/audit:ro",
                "-v",
                str(ROOT / "official-current") + ":/official:ro",
                "-v",
                str(work) + ":/work-test:rw",
            ]
        if validator:
            argv += [
                "-v",
                str(ROOT / "common-current" / "common") + ":/current-common:ro",
                "-e",
                "PYTHONPATH=/current-common:/official",
            ]
        argv += list(extra_mounts) + [IMAGE]
        return argv

    try:
        anonymous = work / "anonymous-docker-config"
        anonymous.mkdir(exist_ok=True)
        os.environ["DOCKER_CONFIG"] = str(anonymous)
        pull = command(
            ["docker", "image", "inspect", IMAGE]
            if args.candidate
            else ["docker", "pull", "--platform=linux/amd64", IMAGE],
            "image-availability",
            150,
        )
        evidence["pull"] = pull
        save()
        if pull["exit_code"]:
            raise RuntimeError("anonymous exact digest pull failed; no forecast executed")
        inspect = command(["docker", "image", "inspect", IMAGE], "image-inspect")
        image = json.loads(inspect["stdout"])[0]
        evidence["oci"] = dict(
            id=image["Id"],
            repo_digests=image["RepoDigests"],
            os=image["Os"],
            architecture=image["Architecture"],
            config=image["Config"],
        )
        assert (image["Os"], image["Architecture"]) == ("linux", "amd64")
        if not args.candidate:
            assert any(x.split("@")[-1] == IMAGE.split("@")[1] for x in image["RepoDigests"])
        assert not image["Config"].get("Volumes")
        assert image["Config"]["Labels"]["qfbench2.interface_version"] == "2.0"
        assert "FORECAST_MODE=text-first-v5.1" in image["Config"]["Env"]
        identity_code = (
            "import pathlib,hashlib,json;\n"
            "p=pathlib.Path('/opt/qfbench2_track_forecasting')\n"
            "print(json.dumps({str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest()\n"
            " for f in p.rglob('*.py')}))"
        )
        identity = command(docker() + ["python3", "-c", identity_code], "source-identity")
        hashes = json.loads(identity["stdout"])
        frozen = ROOT / "frozen-safe" / "qfbench2_track_forecasting"
        evidence["source_files"] = hashes
        evidence["source_identity_verified"] = hashes == {
            str(p.relative_to(frozen)): digest(p) for p in frozen.rglob("*.py")
        }
        assert evidence["source_identity_verified"]
        assert command(docker() + ["forecast", "--help"], "forecast-interface")["exit_code"] == 0
        assert command(docker(), "default-image-command")["exit_code"] == 0
        assert (
            command(
                docker(tooling=True)
                + [
                    "python3",
                    "/audit/container_tools.py",
                    "prepare",
                    "/work-test",
                    "/official",
                    args.group,
                ],
                "prepare",
            )["exit_code"]
            == 0
        )
        assert (
            command(
                docker(validator=True)
                + ["python3", "/audit/container_tools.py", "validate-inputs", "/work-test"],
                "input-schema-preflight",
            )["exit_code"]
            == 0
        )
        assert (
            command(
                docker(tooling=True) + ["python3", "/audit/boundary_inputs.py", "/work-test"],
                "prepare-boundaries",
            )["exit_code"]
            == 0
        )
        manifest = json.loads((work / "synthetic-input-manifest.json").read_text())
        evidence["input_manifest"] = manifest
        normal = (
            ["f1-ust", "f2-eur", "f3-ust", "f4-jpy", "f3-em"]
            if args.group == "daily"
            else ["monthly-a", "monthly-b", "official-cpi", "official-nfp"]
        )
        if args.group == "monthly":
            for label, unit_name in [
                ("official-cpi", "t2-F1-cpi-glidepath-2023"),
                ("official-nfp", "t2-F4-covid-nfp-2020"),
            ]:
                origin = ROOT / "official-current" / "units" / unit_name
                dest = work / "inputs" / label
                dest.mkdir()
                for p in origin.iterdir():
                    if (
                        p.name in {"card.toml", "forecast_spec.json", "text"}
                        or p.suffix == ".parquet"
                    ):
                        if p.is_dir():
                            shutil.copytree(p, dest / p.name)
                        else:
                            shutil.copy2(p, dest / p.name)
                evidence.setdefault("official_inputs", {})[label] = {
                    str(p.relative_to(dest)): digest(p) for p in dest.rglob("*") if p.is_file()
                }

        def forecast(name, repetition, negative=False):
            unit = work / "inputs" / name
            card = tomllib.loads((unit / "card.toml").read_text())
            out = work / "outputs" / name / str(repetition)
            out.mkdir(parents=True)
            out.chmod(0o777)
            resource_code = (
                "import subprocess,resource,json,sys; p=subprocess.run(sys.argv[1:]); "
                "print('FF03_RESOURCE='+json.dumps({'peak_rss_kib':resource.getrus"
                "age(resource.RUSAGE_CHILDREN).ru_maxrss}),file=sys.stderr); sys.e"
                "xit(p.returncode)"
            )
            executable = ["python3", "-c", resource_code, "forecast"]
            argv = (
                docker(["-v", str(unit) + ":/input:ro", "-v", str(out) + ":/output:rw"])
                + executable
                + [
                    "--panels",
                    "/input",
                    "--text",
                    "/input/text",
                    "--asof",
                    card["provenance"]["data_cutoff"],
                    "--out",
                    "/output/forecast.parquet",
                    "--seed",
                    "17",
                ]
            )
            result = command(argv, name + "-" + str(repetition))
            row = dict(
                name=name,
                repetition=repetition,
                expected_failure=negative,
                family=card["metadata"]["category"],
                forecast_exit_code=result["exit_code"],
                wall_seconds=result["wall_seconds"],
                runtime_limit_seconds=90,
                network="none",
                read_only_root=True,
                read_only_input=True,
                cpu_limit=2,
                memory_limit="4g",
                peak_memory="MEASURED_CHILD_RUSAGE",
                peak_rss_kib=next(
                    (
                        json.loads(line.split("=", 1)[1])["peak_rss_kib"]
                        for line in result["stderr"].splitlines()
                        if line.startswith("FF03_RESOURCE=")
                    ),
                    None,
                ),
                output_files={
                    p.name: dict(bytes=p.stat().st_size, sha256=digest(p))
                    for p in out.iterdir()
                    if p.is_file()
                },
            )
            if negative:
                row["pass"] = result["exit_code"] not in {0, 124}
                row["observed_error"] = result["stderr"][-1800:]
            elif result["exit_code"] == 0:
                check = command(
                    docker(
                        ["-v", str(unit) + ":/input:ro", "-v", str(out) + ":/output:ro"],
                        validator=True,
                    )
                    + ["python3", "/audit/container_tools.py", "validate", "/output", "/input"],
                    name + "-validate-" + str(repetition),
                )
                row["pass"] = check["exit_code"] == 0
                if row["pass"]:
                    row["validation"] = json.loads(check["stdout"])
                else:
                    row["validation_error"] = check["stderr"][-1800:]
            else:
                row["pass"] = False
                row["observed_error"] = result["stderr"][-1800:]
            content = "\n".join(
                p.read_text(errors="replace")
                for p in out.iterdir()
                if p.is_file() and p.suffix in {".json", ".md"}
            )
            row["credential_pattern_leakage"] = bool(
                SECRET.search(content + result["stdout"] + result["stderr"])
            )
            row["pass"] = row["pass"] and not row["credential_pattern_leakage"]
            evidence["forecast_processes"].append(row)
            save()
            return row

        if args.group == "monthly":
            normal += [
                "month-start",
                "month-end",
                "lagged-anchor",
                "nonconsecutive",
                "multi-monthly",
                "heterogeneous",
                "heterogeneous-anchor",
            ]
        for name in normal:
            first, second = forecast(name, 1), forecast(name, 2)
            p1, p2 = (
                first["output_files"].get("forecast.parquet"),
                second["output_files"].get("forecast.parquet"),
            )
            evidence.setdefault("determinism", {})[name] = bool(
                p1 and p2 and p1["sha256"] == p2["sha256"]
            )
        if args.group == "daily":
            sentinel = forecast("future-sentinel", 1)
            base = evidence["forecast_processes"][0]
            evidence["post_cutoff_sentinel_ignored"] = sentinel["output_files"].get(
                "forecast.parquet"
            ) == base["output_files"].get("forecast.parquet")
            forecast("missing-history", 1, negative=True)
        else:
            forecast("monthly-missing", 1, negative=True)
            forecast("monthly-conflict", 1, negative=True)
            for boundary in [
                "duplicate-mapping",
                "malformed",
                "duplicate-observations",
                "duplicate-no-mapping",
                "mixed-cadence",
            ]:
                forecast(boundary, 1, negative=True)
            a, b = evidence["forecast_processes"][0], evidence["forecast_processes"][2]
            evidence["monthly_mapping_changes_forecast"] = a["output_files"].get(
                "forecast.parquet"
            ) != b["output_files"].get("forecast.parquet")
            evidence["monthly_distinct_horizons"] = {}
            for name in ["monthly-a", "monthly-b"]:
                row = next(x for x in evidence["forecast_processes"] if x["name"] == name)
                stats = row.get("validation", {}).get("statistics", [])
                evidence["monthly_distinct_horizons"][name] = (
                    len({(x["mean"], x["std"]) for x in stats}) == 4
                )
        evidence["completed"] = True
        if args.candidate:
            baseline_path = TOOLS / "results" / ("baseline-current-" + args.group + ".json")
            baseline = json.loads(baseline_path.read_text())
            evidence["ab_original_run_id"] = baseline["run_id"]
            before = {x["name"]: x for x in baseline["forecast_processes"] if x["repetition"] == 1}
            after = {x["name"]: x for x in evidence["forecast_processes"] if x["repetition"] == 1}
            evidence["ab_parquet_identical"] = {
                name: before.get(name, {}).get("output_files", {}).get("forecast.parquet")
                == row["output_files"].get("forecast.parquet")
                for name, row in after.items()
            }
            original_inputs = {x["name"]: x["files"] for x in baseline["input_manifest"]}
            evidence["historical_ff02_known_input_identity"] = {
                x["name"]: x["files"] == original_inputs.get(x["name"])
                for x in manifest
                if x["name"] in original_inputs
            }
    except Exception:
        evidence["execution_error"] = traceback.format_exc()
    finally:
        save()
    print(
        json.dumps(
            dict(
                group=args.group,
                completed=evidence["completed"],
                forecast_processes=len(evidence["forecast_processes"]),
                pass_count=sum(x["pass"] for x in evidence["forecast_processes"]),
                execution_error=evidence.get("execution_error"),
            ),
            indent=2,
        ),
        flush=True,
    )
    return 0 if evidence["completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

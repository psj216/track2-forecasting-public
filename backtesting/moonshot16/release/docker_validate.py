"""## Executive summary (read this first)
Build an unpushed temporary M16 image and compare actual container runs with frozen M15.
Only synthetic credentials, public inputs and an internal-only mock network are used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tomllib
from pathlib import Path


def run(args, timeout=120):
    completed = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if completed.returncode:
        # Commands may contain synthetic grants; publish only a bounded error, no env.
        raise RuntimeError(
            "command_failed:"
            + args[0]
            + ":"
            + str(completed.returncode)
            + ":"
            + completed.stderr[-1800:]
        )
    return completed.stdout


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True, choices=list("ABCDE"))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[3]
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    out.chmod(0o777)
    sha = run(["git", "rev-parse", "HEAD"]).strip()
    images = json.loads((root / "backtesting/moonshot16/release/frozen_images.json").read_text())
    old = images["candidates"][args.variant]
    image = "m16-release-test-" + args.variant.lower() + ":" + sha[:12]
    network = "m16-release-" + args.variant.lower() + "-" + sha[:10]
    state = out / "state"
    state.mkdir()
    state.chmod(0o777)
    (state / "case.txt").write_text("valid")
    (state / "case.txt").chmod(0o644)
    run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(state / "key.pem"),
            "-out",
            str(state / "cert.pem"),
            "-days",
            "1",
            "-subj",
            "/CN=m16-house",
            "-addext",
            "subjectAltName=DNS:m16-house",
        ],
        timeout=30,
    )
    (state / "key.pem").chmod(0o644)  # synthetic test-only key, never uploaded
    receipt = {
        "executive_summary": (
            "Actual Docker synthetic validation. No live House, score, push or submission."
        ),
        "variant": args.variant,
        "source_SHA": sha,
        "old_image": old,
        "registry_push": False,
        "actual_live_House_calls": 0,
        "cases": [],
        "passed": False,
    }
    receipt_path = out / "container-receipt.json"
    containers = []
    try:
        run(["docker", "version"], timeout=30)
        run(
            [
                "docker",
                "build",
                "--build-arg",
                "M15_VARIANT=" + args.variant,
                "--build-arg",
                "SOURCE_SHA=" + sha,
                "-t",
                image,
                "-f",
                "moonshot15_engine/Dockerfile",
                ".",
            ],
            timeout=240,
        )
        inspected = json.loads(run(["docker", "image", "inspect", image]))[0]
        assert inspected["Config"]["Labels"]["org.opencontainers.image.revision"] == sha
        assert not inspected["Config"].get("Volumes")
        receipt["temporary_local_image_id"] = inspected["Id"]
        receipt["temporary_registry_manifest_digest"] = None
        run(["docker", "pull", old], timeout=180)
        old_inspect = json.loads(run(["docker", "image", "inspect", old]))[0]
        assert old in old_inspect["RepoDigests"]
        receipt["old_source_label"] = old_inspect["Config"]["Labels"].get(
            "org.opencontainers.image.revision"
        )
        assert receipt["old_source_label"] == images["source_SHA"]
        expected = {
            str(p.relative_to(root)): digest(p) for p in (root / "moonshot15_engine").glob("*.py")
        }
        command = (
            "import pathlib,hashlib,json;print(json.dumps({str(p.relative_to('/opt')):"
            "hashlib.sha256(p.read_bytes()).hexdigest() for p in "
            "pathlib.Path('/opt/moonshot15_engine').glob('*.py')}))"
        )
        observed = json.loads(
            run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--network",
                    "none",
                    "--entrypoint",
                    "python3",
                    image,
                    "-c",
                    command,
                ]
            )
        )
        assert expected == observed
        receipt["image_source_files_match"] = True
        run(["docker", "network", "create", "--internal", network])
        prefix = network + "-"
        # Separate House and proxy containers. TLS shares the House network namespace.
        for mode in ["house", "tls", "proxy"]:
            name = prefix + mode
            command = [
                "docker",
                "run",
                "-d",
                "--name",
                name,
                "--read-only",
                "--user",
                "65534:65534",
                "--tmpfs",
                "/tmp:rw,nosuid,size=64m",
                "--pids-limit",
                "128",
                "-v",
                str(root) + ":/fixture:ro",
                "-v",
                str(state) + ":/state:ro",
                "-e",
                "PYTHONPATH=/fixture",
            ]
            if mode == "tls":
                command += ["--network", "container:" + prefix + "house"]
            else:
                command += ["--network", network, "--network-alias", "m16-" + mode]
            command += [
                "--entrypoint",
                "python3",
                image,
                "/fixture/backtesting/moonshot16/release/mock_services.py",
                mode,
            ]
            run(command)
            containers.append(name)
        # Readiness is checked inside the internal network, never through an external API.
        probe = (
            "import socket,time; deadline=time.monotonic()+15\nwhile True:\n try:\n"
            "  for host,port in [('m16-proxy',8080),('m16-house',8080),('m16-house',8443)]:\n"
            "   s=socket.create_connection((host,port),timeout=1);s.close()\n"
            "  break\n except OSError:\n"
            "  if time.monotonic()>deadline:raise\n  time.sleep(.2)"
        )
        run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                network,
                "--entrypoint",
                "python3",
                image,
                "-c",
                probe,
            ],
            timeout=30,
        )

        def forecast(label, target_image, unit, grant="uppercase", case="valid", tls=False):
            (state / "case.txt").write_text(case)
            folder = out / label
            folder.mkdir()
            folder.chmod(0o777)
            flags = [
                "docker",
                "run",
                "--rm",
                "--network",
                "none" if grant == "offline" else network,
                "--read-only",
                "--user",
                "65534:65534",
                "--cpus",
                "2",
                "--memory",
                "8g",
                "--pids-limit",
                "256",
                "--tmpfs",
                "/tmp:rw,noexec,nosuid,size=64m",
                "-v",
                str(unit) + ":/input:ro",
                "-v",
                str(folder) + ":/output:rw",
            ]
            if grant != "offline":
                proxy = (
                    "http://synthetic-user:"
                    + ("wrong-pass" if grant == "bad_auth" else "synthetic-pass")
                    + "@m16-proxy:8080"
                )
                flags += [
                    "-e",
                    "MODEL_ENDPOINT="
                    + ("https://m16-house:8443" if tls else "http://m16-house:8080"),
                    "-e",
                    "MODEL_NAME=synthetic-model",
                    "-e",
                    "MODEL_TOKEN=synthetic-house-token",
                    "-e",
                    ("http_proxy=" if grant == "lowercase" else "HTTP_PROXY=") + proxy,
                    "-e",
                    "NO_PROXY=*",
                ]
                if tls:
                    flags += [
                        "-v",
                        str(state / "cert.pem") + ":/mock-ca.pem:ro",
                        "-e",
                        "SSL_CERT_FILE=/mock-ca.pem",
                    ]
            cutoff = str(
                tomllib.loads((unit / "card.toml").read_text())["provenance"]["data_cutoff"]
            )
            flags += [
                target_image,
                "forecast",
                "--panels",
                "/input",
                "--text",
                "/input/text",
                "--card",
                "/input/card.toml",
                "--asof",
                cutoff,
                "--out",
                "/output/forecast.parquet",
            ]
            log = run(flags, timeout=120)
            meta = json.loads((folder / "forecast_meta.json").read_text())
            rationale = (folder / "forecast_rationale.md").read_text()
            assert rationale.strip()
            output = (folder / "forecast.parquet").read_bytes()
            for secret in [
                "synthetic-house-token",
                "synthetic-pass",
                "wrong-pass",
                "c3ludGhldGljLXVzZXI6c3ludGhldGljLXBhc3M=",
            ]:
                assert secret not in json.dumps(meta) + rationale + log
            row = {
                "label": label,
                "exit_code": 0,
                "parquet_SHA256": hashlib.sha256(output).hexdigest(),
                "metadata_SHA256": digest(folder / "forecast_meta.json"),
                "rationale_SHA256": digest(folder / "forecast_rationale.md"),
                "receipt": meta["moonshot15"],
                "credential_leakage": False,
            }
            receipt["cases"].append(row)
            write(receipt_path, receipt)
            print("M16 container progress", args.variant, label, flush=True)
            return folder, output, meta["moonshot15"]

        for unit_name in ["t2-F1-patient-dropped-2015", "t2-F3-brexit-joint-2016"]:
            unit = root / "units" / unit_name
            label = unit_name + "-"
            _, baseline, _ = forecast(label + "new-offline", image, unit, "offline")
            _, old_baseline, _ = forecast(label + "old-offline", old, unit, "offline")
            assert baseline == old_baseline
            new_folder, upper, m = forecast(label + "new-uppercase", image, unit)
            assert m["adjustment_applied"] and m["response_validated"] and not m["fallback_used"]
            assert upper != baseline
            _, lower, _ = forecast(label + "new-lowercase", image, unit, "lowercase")
            _, old_lower, _ = forecast(label + "old-lowercase", old, unit, "lowercase")
            _, old_upper, _ = forecast(label + "old-uppercase", old, unit)
            assert upper == lower == old_lower
            assert old_upper == baseline
            repeat_folder, repeated, _ = forecast(label + "new-repeat", image, unit)
            assert repeated == upper
            for name in ["forecast_meta.json", "forecast_rationale.md"]:
                assert (new_folder / name).read_bytes() == (repeat_folder / name).read_bytes()
            _, secure, _ = forecast(label + "new-HTTPS", image, unit, tls=True)
            assert secure == upper
            for case, category in [
                ("malformed", "malformed_model_content"),
                ("http_error", "http_503"),
            ]:
                _, failed, m = forecast(label + case, image, unit, case=case)
                assert failed == baseline and m["fallback_used"] and not m["adjustment_applied"]
                assert m["failure_category"] == category
            _, failed, m = forecast(label + "proxy-auth-failure", image, unit, "bad_auth")
            assert failed == baseline and m["failure_category"] == "proxy_authentication_failure"
        receipt.update(
            passed=True,
            internal_network=True,
            frozen_vs_repaired_same_fixture=True,
            fallback_byte_exact=True,
            deterministic_repeat=True,
        )
        write(receipt_path, receipt)
        print("M16_CONTAINER_RECEIPT=" + json.dumps(receipt, sort_keys=True), flush=True)
    except Exception as exc:
        receipt["failure_type"] = type(exc).__name__
        receipt["failure_details"] = str(exc)[:2000]
        write(receipt_path, receipt)
        raise
    finally:
        for name in reversed(containers):
            subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=30)
        subprocess.run(["docker", "network", "rm", network], capture_output=True, timeout=30)


if __name__ == "__main__":
    main()

"""Executive summary: actual isolated Docker A/B replay; no answers opened by this runner."""

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import time
import tomllib

BASE = (
    "docker.io/jotj216/track2-f4-approved@sha256:0b9b08d8a6b59eca262d77778d2b2a9"
    "b33bb938ab68c4db8f71538302f3bf874"
)
FF03 = "sha256:23f226ced859978d7a3f16a23c6d1515a1a3bdb14338297f4818d114bcfa2c1c"
ROOT = pathlib.Path(__file__).resolve().parents[2]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, o):
    p.write_text(json.dumps(o, indent=2) + "\n")


def run(cmd, timeout=90):
    start = time.monotonic()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return dict(
            command=cmd,
            exit=p.returncode,
            stdout=p.stdout,
            stderr=p.stderr,
            wall_seconds=time.monotonic() - start,
        )
    except subprocess.TimeoutExpired as e:
        return dict(
            command=cmd,
            exit=124,
            stdout=str(e.stdout or ""),
            stderr=str(e.stderr or ""),
            wall_seconds=time.monotonic() - start,
        )


def auxiliary(image, unit, out, official, common, extra):
    return [
        "docker",
        "run",
        "--rm",
        "--network=none",
        "--read-only",
        "--tmpfs",
        "/tmp:rw,size=512m",
        "--cpus=2",
        "--memory=4g",
        "-v",
        str(unit) + ":/input:ro",
        "-v",
        str(out) + ":/output:ro",
        "-v",
        str(official) + ":/official:ro",
        "-v",
        str(common / "common") + ":/current-common:ro",
        "-e",
        "PYTHONPATH=/current-common:/official",
        image,
    ] + extra


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--official", type=pathlib.Path, required=True)
    p.add_argument("--common", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    p.add_argument("--batch", type=int, required=True)
    p.add_argument("--batches", type=int, default=6)
    a = p.parse_args()
    official = a.official.resolve()
    common = a.common.resolve()
    root = a.out.resolve()
    root.mkdir(parents=True, exist_ok=True)
    spec = json.loads((ROOT / "backtesting/finalfit04/spec.json").read_text())
    ids = spec["cards"][a.batch :: a.batches]
    for label, image in [("original", BASE), ("ff03", FF03)]:
        info = run(["docker", "image", "inspect", image])
        save(root / (label + "-inspect.json"), info)
        assert info["exit"] == 0
        o = json.loads(info["stdout"])[0]
        assert (
            o["Os"] == "linux" and o["Architecture"] == "amd64" and not o["Config"].get("Volumes")
        )
        assert o["Config"]["Labels"]["qfbench2.interface_version"] == "2.0"
        assert o["Config"]["User"] not in ("", "0", "root")
        if label == "ff03":
            assert o["Id"] == FF03
    start = time.monotonic()
    for ix, cardid in enumerate(ids):
        unit = (official / "units" / cardid).resolve()
        c = tomllib.loads((unit / "card.toml").read_text())
        hashes = {str(f.relative_to(unit)): sha(f) for f in unit.rglob("*") if f.is_file()}
        assert not any(f.is_symlink() for f in unit.rglob("*"))
        assert not any(
            word in k.lower() for k in hashes for word in ["realized", "answer", "reference/"]
        )
        paired = {}
        for label, image in [("original", BASE), ("ff03", FF03)]:
            dest = root / cardid / label
            dest.mkdir(parents=True, exist_ok=True)
            output = dest / "output"
            output.mkdir(exist_ok=True)
            output.chmod(0o777)
            receipt = dest / "receipt.json"
            if receipt.exists():
                old = json.loads(receipt.read_text())
                assert old["inputs"] == hashes and old["image"] == image
                paired[label] = old
                continue
            name = "ff04-" + str(a.batch) + "-" + str(ix) + "-" + label
            cmd = [
                "docker",
                "run",
                "--name",
                name,
                "--platform=linux/amd64",
                "--network=none",
                "--read-only",
                "--tmpfs",
                "/tmp:rw,size=512m",
                "--cpus=2",
                "--memory=4g",
                "--pids-limit=256",
                "-v",
                str(unit) + ":/input:ro",
                "-v",
                str(output) + ":/output:rw",
                image,
                "forecast",
                "--panels",
                "/input",
                "--text",
                "/input/text",
                "--asof",
                c["provenance"]["data_cutoff"],
                "--out",
                "/output/forecast.parquet",
                "--seed",
                "17",
                "--n-draws",
                "1000",
            ]
            record = dict(
                executive_summary=(
                    "Actual Docker process; input/output mounts only; " "no answer mount."
                ),
                card=cardid,
                image=image,
                inputs=hashes,
                forecast=run(cmd, 90),
                source_sha=os.environ.get("GITHUB_SHA"),
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
            ins = run(["docker", "inspect", name])
            record["container_inspect"] = json.loads(ins["stdout"])[0] if ins["exit"] == 0 else ins
            # Preserve exact mounts and network configuration before removal.
            run(["docker", "rm", "-f", name])
            record["output_hashes"] = {f.name: sha(f) for f in output.iterdir() if f.is_file()}
            required = ["forecast.parquet", "forecast_meta.json", "forecast_rationale.md"]
            record["required_outputs"] = all((output / f).is_file() for f in required)
            record["output_bytes"] = sum(f.stat().st_size for f in output.iterdir() if f.is_file())
            if record["forecast"]["exit"] == 0 and record["required_outputs"]:
                scorecmd = auxiliary(
                    BASE,
                    unit,
                    output,
                    official,
                    common,
                    [
                        "python3",
                        "/official/scoring/scoring.py",
                        "score",
                        "--card",
                        "/input/card.toml",
                        "--forecast",
                        "/output/forecast.parquet",
                    ],
                )
                record["gates"] = run(scorecmd)
                try:
                    record["gate_result"] = json.loads(record["gates"]["stdout"])
                except ValueError:
                    record["gate_result"] = None
                check = (
                    "import json,pathlib,numpy as np,pandas as pd; d=pd.read_parquet('/output/fo"
                    "recast.parquet'); m=json.loads(pathlib.Path('/output/forecast_meta.json').r"
                    "ead_text()); print(json.dumps({'finite':bool(np.isfinite(d.value).all()),'n"
                    "umeric_sha256':__import__('hashlib').sha256(d.sort_values(['draw','asset','"
                    "horizon']).value.to_numpy().tobytes()).hexdigest(),'rows':len(d),'draws':in"
                    "t(d.draw.nunique()),'assets':sorted(d.asset.unique().tolist()),'horizons':s"
                    "orted(map(int,d.horizon.unique())),'metadata':m}))"
                )
                record["numerics"] = run(
                    auxiliary(BASE, unit, output, official, common, ["python3", "-c", check])
                )
                try:
                    record["numeric_result"] = json.loads(record["numerics"]["stdout"])
                except ValueError:
                    record["numeric_result"] = None
            save(receipt, record)
            paired[label] = record
            print(
                json.dumps(
                    dict(
                        batch=a.batch,
                        card=cardid,
                        candidate=label,
                        exit=record["forecast"]["exit"],
                        gates=record.get("gates", {}).get("exit"),
                        elapsed=time.monotonic() - start,
                    )
                ),
                flush=True,
            )
        comparison = {
            key: paired["original"]["output_hashes"].get(key)
            == paired["ff03"]["output_hashes"].get(key)
            and key in paired["original"]["output_hashes"]
            for key in ["forecast.parquet", "forecast_meta.json", "forecast_rationale.md"]
        }
        save(
            root / cardid / "paired.json",
            dict(
                card=cardid,
                bytes=comparison,
                status="DAILY_IDENTITY_CONFIRMED"
                if all(comparison.values())
                else "DIFFERENT_OR_FAILED",
            ),
        )
    # One representative repeat per batch, no rereplay of completed whole batches.
    first = ids[0]
    src = root / first / "ff03"
    rec = json.loads((src / "receipt.json").read_text())
    if rec["forecast"]["exit"] == 0:
        out = root / first / "repeat"
        out.mkdir(exist_ok=True)
        out.chmod(0o777)
        cmd = rec["forecast"]["command"].copy()
        i = cmd.index("--name")
        cmd[i + 1] += "-repeat"
        i = cmd.index("-v", cmd.index("-v") + 1)
        cmd[i + 1] = str(out) + ":/output:rw"
        rr = run(cmd)
        rr["hashes"] = {f.name: sha(f) for f in out.iterdir() if f.is_file()}
        rr["identical"] = rr["hashes"] == rec["output_hashes"]
        save(root / first / "repeat.json", rr)
        run(["docker", "rm", "-f", cmd[cmd.index("--name") + 1]])
    save(
        root / "batch.json",
        dict(batch=a.batch, cards=ids, completed=True, wall_seconds=time.monotonic() - start),
    )


if __name__ == "__main__":
    main()

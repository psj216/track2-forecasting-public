"""## Executive summary (read this first)
Chunked compatibility replay for an explicitly supplied future official practice directory.
No model fitting, scoring math, registry push, credentials or submission. No targets are opened.
"""

import argparse
import hashlib
import json
import pathlib
import subprocess
import time
import tomllib

p = argparse.ArgumentParser()
p.add_argument("--units", type=pathlib.Path, required=True)
p.add_argument("--image", required=True)
p.add_argument("--out", type=pathlib.Path, required=True)
p.add_argument("--official-track", type=pathlib.Path, required=True)
p.add_argument("--official-common", type=pathlib.Path, required=True)
p.add_argument("--max-cards", type=int, default=4)
a = p.parse_args()
assert a.units.is_dir() and 1 <= a.max_cards <= 30
work = a.out.resolve()
work.mkdir(parents=True, exist_ok=True)
manifest = []
for card_path in sorted(a.units.glob("*/card.toml")):
    card = tomllib.loads(card_path.read_text())
    unit = card_path.parent
    blocked = [
        f
        for f in unit.rglob("*")
        if f.name in {"realized.parquet", "targets.parquet"}
        or any(part in {"reference", "answers", "realized"} for part in f.relative_to(unit).parts)
    ]
    if blocked:
        raise SystemExit(
            "Answer material is inside this unit. "
            "Use the organizer's participant-input projection; do not mount targets."
        )
    files = {
        str(f.relative_to(unit)): hashlib.sha256(f.read_bytes()).hexdigest()
        for f in unit.rglob("*")
        if f.is_file() and not any(x in f.parts for x in ["reference", "targets", "realized"])
    }
    manifest.append(dict(id=card["task"]["id"], unit=str(unit.resolve()), input_hashes=files))
assert manifest, "No official cards found; do not infer publication."
(work / "planned-inputs.json").write_text(
    json.dumps(
        dict(
            executive_summary="Compatibility replay only, no targets or performance.",
            image=a.image,
            cards=manifest,
        ),
        indent=2,
    )
    + "\n"
)
start = time.monotonic()
done = 0
for item in manifest:
    dest = work / item["id"]
    receipt = dest / "receipt.json"
    if receipt.exists():
        previous = json.loads(receipt.read_text())
        if (
            previous.get("image") == a.image
            and previous.get("inputs") == item["input_hashes"]
            and previous.get("validation_exit") == 0
        ):
            continue
    if done >= a.max_cards or time.monotonic() - start > 420:
        break
    dest.mkdir(exist_ok=True)
    output = dest / "output"
    output.mkdir(exist_ok=True)
    output.chmod(0o777)
    card = tomllib.loads((pathlib.Path(item["unit"]) / "card.toml").read_text())
    asof = card["provenance"]["data_cutoff"]
    args = [
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
        item["unit"] + ":/input:ro",
        "-v",
        str(output) + ":/output:rw",
        a.image,
        "forecast",
        "--panels",
        "/input",
        "--text",
        "/input/text",
        "--asof",
        asof,
        "--out",
        "/output/forecast.parquet",
        "--seed",
        "17",
    ]
    r = subprocess.run(args, capture_output=True, text=True, timeout=90)
    record = dict(
        executive_summary="Unscored official-input compatibility replay.",
        image=a.image,
        inputs=item["input_hashes"],
        command=args,
        forecast_exit=r.returncode,
        stdout=r.stdout,
        stderr=r.stderr,
        validation_exit=None,
        score="NOT_RUN",
    )
    if r.returncode == 0:
        tool = pathlib.Path(__file__).resolve().parent
        args = [
            "docker",
            "run",
            "--rm",
            "--network=none",
            "--read-only",
            "--tmpfs",
            "/tmp",
            "-v",
            str(tool) + ":/audit:ro",
            "-v",
            str(a.official_track.resolve()) + ":/official:ro",
            "-v",
            str(a.official_common.resolve() / "common") + ":/current-common:ro",
            "-v",
            item["unit"] + ":/input:ro",
            "-v",
            str(output) + ":/output:ro",
            "-e",
            "PYTHONPATH=/current-common:/official",
            a.image,
            "python3",
            "/audit/container_tools.py",
            "validate",
            "/output",
            "/input",
        ]
        v = subprocess.run(args, capture_output=True, text=True, timeout=60)
        record.update(
            validation_exit=v.returncode, validation_stdout=v.stdout, validation_stderr=v.stderr
        )
    receipt.write_text(json.dumps(record, indent=2) + "\n")
    done += 1
    print(item["id"], r.returncode, record["validation_exit"], flush=True)
print(
    json.dumps(
        dict(
            executed_this_chunk=done,
            total_registered=len(manifest),
            performance="NOT_RUN",
            resume="Repeat exact command; verified receipts are reused.",
        )
    )
)

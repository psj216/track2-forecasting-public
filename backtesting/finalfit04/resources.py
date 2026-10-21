("Executive summary: two bounded repeat runs measure fore" "cast-child RSS inside Docker.")

import json
import os
import pathlib
import tomllib

from replay import BASE, FF03, run, save, sha

root = pathlib.Path(os.environ["RUNNER_TEMP"]) / "ff04-resources"
root.mkdir(exist_ok=True)
unit = (pathlib.Path("official-current/units/t2-F4-curve-ust3m-008-ps1")).resolve()
c = tomllib.loads((unit / "card.toml").read_text())
code = (
    (
        "import subprocess,resource,json,time,pathlib; t=time.mo"
        "notonic(); p=subprocess.run(['forecast','--panels','/in"
        "put','--text','/input/text','--asof',"
    )
    + repr(c["provenance"]["data_cutoff"])
    + (
        ",'--out','/output/forecast.parquet','--seed','17','--n-"
        "draws','1000']); pathlib.Path('/output/resource.json')."
        "write_text(json.dumps({'forecast_exit':p.returncode,'wa"
        "ll_seconds':time.monotonic()-t,'forecast_child_peak_rss"
        "_kib':resource.getrusage(resource.RUSAGE_CHILDREN).ru_m"
        "axrss})); raise SystemExit(p.returncode)"
    )
)
for label, image in [("original", BASE), ("ff03", FF03)]:
    out = root / label
    out.mkdir(exist_ok=True)
    out.chmod(0o777)
    cmd = [
        "docker",
        "run",
        "--rm",
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
        str(out) + ":/output:rw",
        image,
        "python3",
        "-c",
        code,
    ]
    rec = run(cmd, 90)
    rec["candidate"] = label
    rec["unit"] = unit.name
    rec["image"] = image
    rec["scope"] = "RSS is forecast child maxrss, not total container/cgroup peak."
    if (out / "resource.json").exists():
        rec["resource"] = json.loads((out / "resource.json").read_text())
    rec["hashes"] = {f.name: sha(f) for f in out.iterdir() if f.name != "resource.json"}
    save(root / (label + "-resource-receipt.json"), rec)
    print(json.dumps(rec), flush=True)
    assert rec["exit"] == 0

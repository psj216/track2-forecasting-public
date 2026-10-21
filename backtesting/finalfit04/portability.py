("Executive summary: diagnose same-input portability; no " "production repair or score tuning.")
import os
import pathlib
import tomllib

from replay import BASE, FF03, run, save, sha

root = pathlib.Path(os.environ["RUNNER_TEMP"]) / "ff04-portability"
root.mkdir(exist_ok=True)
unit = pathlib.Path("official-current/units/t2-F4-curve-ust3m-008-ps1").resolve()
c = tomllib.loads((unit / "card.toml").read_text())
save(
    root / "host.json",
    dict(
        cpu=run(["lscpu"]),
        inputs={str(f.relative_to(unit)): sha(f) for f in unit.rglob("*") if f.is_file()},
    ),
)
for label, image, disabled in [
    ("original-normal", BASE, False),
    ("original-repeat", BASE, False),
    ("ff03-normal", FF03, False),
    ("original-simd-disabled", BASE, True),
    ("ff03-simd-disabled", FF03, True),
]:
    out = root / label
    out.mkdir(exist_ok=True)
    out.chmod(0o777)
    common = [
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
        "-v",
        str(unit) + ":/input:ro",
        "-v",
        str(out) + ":/output:rw",
    ]
    if disabled:
        common += ["-e", "NPY_DISABLE_CPU_FEATURES=AVX512F,AVX2,FMA3"]
    cmd = common + [
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
    rec = run(cmd, 90)
    rec["hashes"] = {f.name: sha(f) for f in out.iterdir() if f.is_file()}
    save(root / (label + ".json"), rec)
    print(label, rec["exit"], rec["hashes"], flush=True)
    assert rec["exit"] == 0
    code = (
        (
            "import json,numpy as np,pandas as pd,hashlib;from qfben"
            "ch2_track_forecasting.cli import _read_panels,_series;f"
            "rom qfbench2_track_forecasting.numeric_v1 import _diff_"
            "without_gaps,_state_matched_starts;from qfbench2_track_"
            "forecasting.numeric_v21 import V21_CONFIG;s=_series(_re"
            "ad_panels(__import__('pathlib').Path('/input')),'UST_3M"
            "',"
        )
        + repr(c["provenance"]["data_cutoff"])
        + (
            ");d=pd.DataFrame({'UST_3M':_diff_without_gaps(s)}).drop"
            "na().tail(2520);m=_state_matched_starts(d,3,max(0,len(d"
            ")-120),V21_CONFIG);print(json.dumps({'numpy':np.__versi"
            "on__,'features':{k:bool(v) for k,v in np._core._multiar"
            "ray_umath.__cpu_features__.items()},'matched_starts':m}"
            "));np.show_runtime()"
        )
    )
    fingerprint = run(common + [image, "python3", "-c", code])
    save(root / (label + "-numeric-runtime.json"), fingerprint)

"""## Executive summary (read this first)
Historical synthetic schema probes using only published asset IDs/units and helper fields.
No observations or targets from actual Final dates are generated.
"""

import hashlib
import json
import pathlib
import shutil
import sys
import tomllib
import uuid

import pandas as pd
from container_tools import write_toml

root = pathlib.Path(sys.argv[1])
base = root / "inputs/monthly-a"
manifest = json.loads((root / "synthetic-input-manifest.json").read_text())
for name in [
    "month-start",
    "month-end",
    "lagged-anchor",
    "nonconsecutive",
    "multi-monthly",
    "heterogeneous",
    "heterogeneous-anchor",
    "duplicate-mapping",
    "malformed",
    "duplicate-observations",
    "duplicate-no-mapping",
    "mixed-cadence",
]:
    dest = root / "inputs" / name
    shutil.copytree(base, dest)
    card = tomllib.loads((dest / "card.toml").read_text())
    card["task"]["id"] = "t2-fit03-" + name
    card["contamination"]["canary_guid"] = str(
        uuid.UUID(bytes=hashlib.sha256(name.encode()).digest()[:16], version=4)
    )
    spec = json.loads((dest / "forecast_spec.json").read_text())
    spec["card_id"] = card["task"]["id"]
    df = pd.read_parquet(dest / "synthetic_history.parquet")
    periods = spec["targets"]["observation_periods"]
    if name in ["month-start", "month-end"]:
        spec["targets"]["target_dates"] = [
            p + ("-01" if name == "month-start" else "-" + str(pd.Period(p).days_in_month))
            for p in periods
        ]
    if name == "lagged-anchor":
        df = df.iloc[:-3]
    if name == "nonconsecutive":
        spec["targets"]["observation_periods"] = ["2018-09", "2018-11", "2019-02", "2019-06"]
    if name in ["multi-monthly", "heterogeneous", "heterogeneous-anchor", "mixed-cadence"]:
        nfp_card = tomllib.loads(
            pathlib.Path("/official/units/t2-F4-covid-nfp-2020/card.toml").read_text()
        )
        card["targets"]["value_unit"] += (
            " (CPI_ALL); " + nfp_card["targets"]["value_unit"] + " (NFP)"
        )
        card["targets"]["asset_ids"] = ["CPI_ALL", "NFP"]
        spec["targets"]["asset_ids"] = ["CPI_ALL", "NFP"]
        card["metadata"].update(category="T2-F3", n_assets=2)
        spec["card_family"] = "T2-F3"
        card["panels"]["synthetic_history"]["asset_ids"] = ["CPI_ALL", "NFP"]
        other = df.copy()
        other["asset"] = "NFP"
        other["value"] *= 500.0
        if name == "heterogeneous-anchor":
            other = other.iloc[:-1]
        if name == "mixed-cadence":
            other = pd.DataFrame(
                dict(
                    date=pd.bdate_range(end="2018-09-14", periods=300).strftime("%Y-%m-%d"),
                    asset="NFP",
                    value=100000.0,
                )
            )
        df = pd.concat([df, other], ignore_index=True)
        if name == "heterogeneous":
            del spec["targets"]["observation_periods"]
            spec["questions"] = [
                dict(asset=a, horizon=h, observation_period=p)
                for a in ["CPI_ALL", "NFP"]
                for h, p in zip(
                    [1, 2, 3, 4],
                    periods if a == "CPI_ALL" else ["2018-10", "2018-12", "2019-01", "2019-02"],
                    strict=True,
                )
            ]
    if name == "duplicate-mapping":
        spec["questions"] = [dict(asset="CPI_ALL", horizon=1, observation_period="2018-09")] * 2
    if name == "malformed":
        spec["targets"]["observation_periods"][0] = "2018-13"
    if name in ["duplicate-observations", "duplicate-no-mapping"]:
        df = pd.concat([df, df.iloc[-1:]], ignore_index=True)
    if name == "duplicate-no-mapping":
        del spec["targets"]["observation_periods"]
    write_toml(card, dest / "card.toml")
    (dest / "forecast_spec.json").write_text(json.dumps(spec, indent=2))
    index = json.loads((dest / "text/corpus_index.json").read_text())
    index["card_id"] = card["task"]["id"]
    (dest / "text/corpus_index.json").write_text(json.dumps(index))
    df.to_parquet(dest / "synthetic_history.parquet", index=False)
    manifest.append(
        dict(
            name=name,
            input_kind="SYNTHETIC_CONTRACT_TEST",
            family=card["metadata"]["category"],
            assets=card["targets"]["asset_ids"],
            horizons=[1, 2, 3, 4],
            asof="2018-09-14",
            units=card["targets"]["value_unit"],
            expected_failure=name
            in [
                "duplicate-mapping",
                "malformed",
                "duplicate-observations",
                "duplicate-no-mapping",
                "mixed-cadence",
            ],
            files={
                str(p.relative_to(dest)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in dest.rglob("*")
                if p.is_file()
            },
        )
    )
(root / "synthetic-input-manifest.json").write_text(json.dumps(manifest, indent=2))
print("12 registered monthly boundary fixtures prepared")

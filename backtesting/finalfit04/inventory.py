"""Executive summary: authenticate official inputs and answer grids without exposing labels."""

import argparse
import hashlib
import itertools
import json
import pathlib
import tomllib

import numpy as np
import pandas as pd


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def inventory(official, out):
    cards = []
    files = {}
    errors = []
    sums = {
        line.split()[1].lstrip("*"): line.split()[0]
        for line in (official / "practice-answers/SHA256SUMS").read_text().splitlines()
        if line.strip()
    }
    units = sorted((official / "units").glob("*-ps1"))
    assert len(units) == 22
    for u in units:
        c = tomllib.loads((u / "card.toml").read_text())
        t = c["targets"]
        asof = c["provenance"]["data_cutoff"]
        hs = {str(p.relative_to(u)): sha(p) for p in u.rglob("*") if p.is_file()}
        assert not any(p.is_symlink() for p in u.rglob("*"))
        assert not any(
            x in k.lower()
            for k in hs
            for x in ["practice-answers", "realized", "reference/", "answer_key"]
        )
        m = json.loads((u / "manifest.json").read_text())
        bad = [f["path"] for f in m["files"] if hs.get(f["path"]) != f["sha256"]]
        if bad:
            errors.append(dict(card=u.name, kind="manifest", files=bad))
        panels = []
        for p in sorted(u.glob("*.parquet")):
            f = pd.read_parquet(p)
            col = "asset" if "asset" in f else "asset_id"
            ds = pd.to_datetime(f["date"])
            assert str(ds.max())[:10] <= asof
            panels.append(
                dict(
                    panel=p.stem,
                    columns=list(f),
                    rows=len(f),
                    assets=sorted(f[col].unique().tolist()),
                    start=str(ds.min())[:10],
                    end=str(ds.max())[:10],
                    finite=bool(np.isfinite(f["value"]).all()),
                )
            )
        a = official / "practice-answers" / f"{u.name}.parquet"
        assert a.is_file()
        assert sha(a) == sums[a.name]
        af = pd.read_parquet(a)
        expected = set(itertools.product(t["asset_ids"], t["horizons"]))
        assert not af.duplicated(["asset", "horizon"]).any()
        assert set(zip(af.asset, af.horizon)) == expected and np.isfinite(af.value).all()
        for row in af.itertuples():
            assert row.target_date == str(np.busday_offset(np.datetime64(asof), int(row.horizon)))
        docs = json.loads((u / "text/corpus_index.json").read_text())
        assert all(
            str(d.get("timestamp", d.get("date", "")))[:10] <= asof
            for d in docs.get("documents", [])
        )
        cards.append(
            dict(
                id=u.name,
                family=c["metadata"]["category"],
                asof=asof,
                targets=t,
                panels=panels,
                scoring=c["scoring"],
                text=c["text"],
                input_files=len(hs),
                manifest_pass=not bad,
                answer_sha256=sha(a),
                answer_grid_pass=True,
                target_dates=sorted(af.target_date.unique().tolist()),
                frequency=t.get("target_frequency", "daily"),
            )
        )
        files[u.name] = hs
    payload = dict(
        executive_summary="22 official exposed-practice input inventories; labels withheld.",
        cards=cards,
        count=len(cards),
        errors=errors,
        all_integrity_pass=not errors,
        answers_not_forecast_inputs=True,
    )
    out.mkdir(parents=True, exist_ok=True)
    (out / "FINALFIT04-PRACTICE-INVENTORY.json").write_text(json.dumps(payload, indent=2) + "\n")
    (out / "FINALFIT04-INPUT-MANIFEST.json").write_text(
        json.dumps(
            dict(executive_summary="Exact per-unit input hashes; no answer values.", cards=files),
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(dict(cards=len(cards), errors=errors, files=sum(map(len, files.values())))))
    assert not errors


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--official", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    inventory(a.official, a.out)

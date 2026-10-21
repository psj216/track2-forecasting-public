"""Executive summary: official raw scoring after forecast completion, answers mounted only here."""

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from replay import BASE, auxiliary, run, save

p = argparse.ArgumentParser()
p.add_argument("--official", type=pathlib.Path, required=True)
p.add_argument("--common", type=pathlib.Path, required=True)
p.add_argument("--out", type=pathlib.Path, required=True)
a = p.parse_args()
o = a.official.resolve()
common = a.common.resolve()
root = a.out.resolve()
for path in sorted(root.glob("*/paired.json")):
    unit = o / "units" / path.parent.name
    for label in ["original", "ff03"]:
        dest = path.parent / label
        rec = json.loads((dest / "receipt.json").read_text())
        if rec["forecast"]["exit"] != 0 or not rec["required_outputs"]:
            save(
                dest / "score.json",
                dict(
                    executive_summary="Forecast failed, not scored; denominator retained.",
                    status="NOT_SCORED_FORECAST_FAILURE",
                ),
            )
            continue
        cmd = auxiliary(
            BASE,
            unit,
            dest / "output",
            o,
            common,
            [
                "python3",
                "/official/scoring/scoring.py",
                "score",
                "--card",
                "/input/card.toml",
                "--forecast",
                "/output/forecast.parquet",
                "--realized",
                "/official/practice-answers/" + unit.name + ".parquet",
            ],
        )
        result = run(cmd)
        result["executive_summary"] = (
            "OFFICIAL_RAW_PRACTICE_SCORE; exposed history, not normalized leaderboard score."
        )
        try:
            result["metrics"] = json.loads(result["stdout"])
        except ValueError:
            result["metrics"] = None
        save(dest / "score.json", result)
        print(unit.name, label, result["exit"], result.get("metrics", {}), flush=True)

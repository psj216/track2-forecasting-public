"""## Executive summary (read this first)
Fixed extended release assertions, captured RED on the first standalone image before repair.
Original FF02 four semantic assertions remain unchanged in their inherited file.
"""

import json
import pathlib
import sys


def checks(receipt):
    rows = receipt["forecast_processes"]
    return {
        "monthly_f3_multiple_assets_complete": all(
            r["pass"] for r in rows if r["name"] == "multi-monthly"
        ),
        "heterogeneous_target_grids_complete": all(
            r["pass"] for r in rows if r["name"] == "heterogeneous"
        ),
        "heterogeneous_anchors_complete": all(
            r["pass"] for r in rows if r["name"] == "heterogeneous-anchor"
        ),
        "duplicate_monthly_without_mapping_refuses": all(
            r["forecast_exit_code"] not in {0, 124}
            for r in rows
            if r["name"] == "duplicate-no-mapping"
        ),
    }


if __name__ == "__main__":
    result = checks(json.loads(pathlib.Path(sys.argv[1]).read_text()))
    print(json.dumps(result, indent=2))
    assert all(result.values()), "Extended standalone monthly boundary contract fails"

"""## Executive summary (read this first)
Four fixed semantic assertions against actual Docker receipts. Saved before candidate repair.
Baseline must fail; a candidate must pass the identical assertions, not changed expectations.
"""

import json
import pathlib
import sys


def checks(receipt):
    negatives = {r["name"]: r for r in receipt.get("negative_results", receipt.get("forecast_processes", []))}
    return {
        "explicit_observation_mapping_changes_forecast": receipt["monthly_mapping_changes_forecast"] is True,
        "distinct_monthly_steps_produce_distinct_forecasts": all(receipt["monthly_distinct_horizons"].values()),
        "missing_monthly_mapping_is_rejected": negatives["monthly-missing"]["forecast_exit_code"] not in {0, 124},
        "conflicting_monthly_mapping_is_rejected": negatives["monthly-conflict"]["forecast_exit_code"] not in {0, 124},
    }


if __name__ == "__main__":
    results = checks(json.loads(pathlib.Path(sys.argv[1]).read_text()))
    print(json.dumps({"tests": results, "passed": sum(results.values()), "failed": len(results) - sum(results.values())}, indent=2))
    assert all(results.values()), "monthly observation-period contract failed"

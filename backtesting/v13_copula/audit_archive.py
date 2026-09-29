"""Compare evaluation structure without fitting to archived outcome ratios."""

import argparse
import hashlib
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--archive", type=Path, default=Path(
        "backtesting/v13_copula/archive/full_eval_final.json"))
    p.add_argument("--smoke-dir", type=Path, default=Path("backtesting/v13_copula"))
    p.add_argument("--proxy", type=Path, default=Path(
        "backtesting/v13_copula/proxy_24_reconstructed.json"))
    p.add_argument("--out", type=Path, default=Path(
        "backtesting/v13_copula/full_eval_reconstructed.json"))
    a = p.parse_args()
    archive = json.loads(a.archive.read_text())
    smokes = [json.loads((a.smoke_dir / f"smoke_F{i}.json").read_text())
              for i in range(1, 5)]
    proxy = json.loads(a.proxy.read_text())
    families = {x["family"] for x in smokes}
    assert archive["draws"] == 2000 and archive["cases"] == 24
    assert set(archive["models"]) == {"V11", "V12", "A", "B", "C"}
    assert families == {"T2-F1", "T2-F2", "T2-F3", "T2-F4"}
    assert all(x["shape"][0] == 2000 and x["finite"] and
               x["marginals_identical_abc"] for x in smokes)
    assert proxy["cases"] == 24 and proxy["draws"] == 2000
    assert all(set(m["family"]) == families and
               all(g["cases"] == 6 for g in m["family"].values())
               for m in proxy["models"].values())
    frozen = {model: {"overall": archive["models"][model]["versus_v5"]["geometric_ratio"],
                      "marginal": archive["models"][model]["versus_v5"]["marginal_ratio"],
                      "joint": archive["models"][model]["versus_v5"]["joint_ratio"],
                      "tail": archive["models"][model]["versus_v5"]["tail_ratio"]}
              for model in ("V12", "A", "B", "C")}
    out = {
        "kind": "RECONSTRUCTED_IMPLEMENTATION_STRUCTURAL_AUDIT",
        "not_an_outcome_evaluation": True,
        "archived_json_sha256": hashlib.sha256(a.archive.read_bytes()).hexdigest(),
        "archived_cases": 24, "archived_draws": 2000,
        "new_outcome_cases": 24,
        "archived_metrics_read_only": frozen,
        "new_distinct_proxy_metrics": {name:proxy["models"][name]["overall"]
                                       for name in "ABC"},
        "paired_case_comparison_possible": False,
        "archived_postfit_cases": 9,
        "new_proxy_postfit_cases": proxy["models"]["A"]["postfit"]["cases"],
        "groups_in_archive": list(archive["models"]["A"]["breakdown"]),
        "new_smokes": smokes,
        "mismatch_classification": {
            "A_implementation_mismatch": "23 public-panel decoder assets and 368 usable fitting origins, versus archived 25 and 414; model code newly reconstructed",
            "B_missing_historical_private_artifact": "original bank bytes and case/pair outcome ledger absent; a new revised-history bank was generated for smoke only",
            "C_randomness_seed_mismatch": "cannot assess without original executable and saved case seeds",
            "D_irrecoverable_original_model_detail": "original frozen V12 coefficient bytes and exact 24 pseudo-origin definitions are missing; new alphabetical public-card selection is a separate proxy",
        },
        "ready_for_one_shot_submission": False,
    }
    a.out.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"archive_schema_ok": True, "four_family_smoke_ok": True,
                      "new_outcome_cases": 24, "paired_case_comparison_possible": False}))


if __name__ == "__main__":
    main()

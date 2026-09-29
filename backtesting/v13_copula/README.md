# V13 reconstructed research path

The files in `archive/` and the root `V13-COPULA-report.md` are immutable historical references from the recovery pack. The new model is a reconstruction from that specification, not a restoration of its code or coefficient bytes. In particular, 0.893 is an **archived** V13-A ratio and is not reproduced here.

Build a **new** private bank outside this Git repository. Do not publish its outcome values:

```bash
python -m backtesting.v13_copula.build_bank --units units \
  --artifact qfbench2_track_forecasting/v12/artifacts.json \
  --out /tmp/v13_reconstructed_private_bank.npz \
  --manifest qfbench2_track_forecasting/v13/bank_manifest.json
```

Run the real V5.1 CLI (requires Python 3.13 and the public toolkit), then V13:

```bash
python -m backtesting.v13_copula.run_card --unit units/t2-F3-bear-flattener-2022 \
  --artifact qfbench2_track_forecasting/v12/artifacts.json \
  --bank /tmp/v13_reconstructed_private_bank.npz --out /tmp/v13_F3 --draws 2000
```

Omit `--bank` for V13-A offline; B/C then use V5.1 ranks as the documented bank-unavailable fallback. `evaluate_proxy.py` scores a **different, preselected** set of 24 public historical cards (six alphabetical eligible cards per family) with 2,000 draws; individual outcome rows remain outside Git. `audit_archive.py` verifies both 24-case schemas and the four new offline shape/marginal checks. It does not claim to rerun the missing original 24-case outcome ledger.

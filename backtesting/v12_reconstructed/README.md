# V12 reconstructed evaluation boundary

The archived V12 report records overall 0.933, post-fit 1.077 and joint 1.151 versus V5.1. Those are historical observations from an unavailable original artifact, not scores produced by this branch.

This branch fits a new artifact from currently shipped public panel prefixes. Current histories are revised and lack verified historical release vintages. Training and smoke tests do not establish a new out-of-sample result. The 950 origin cap is structural; the counts of eligible origins, cells and assets are recomputed and may differ from the archived 414/38,134/25.

To reproduce the reconstructed artifact:

```bash
python -m qfbench2_track_forecasting.v12.train --units units --out qfbench2_track_forecasting/v12/artifacts.json
python -m pytest --noconftest tests/test_v12_reconstructed.py
python -m backtesting.v12_reconstructed_smoke --artifact qfbench2_track_forecasting/v12/artifacts.json --draws 500
```

No private outcomes or original-model coefficients are included.

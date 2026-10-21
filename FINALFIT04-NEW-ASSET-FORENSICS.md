## Executive summary (read this first)

No official-card contract failure was found in either image on the 22-card replay. No canonical routing, units, quote, horizon, missing-data or forecasting code was changed. A later cross-runner output discrepancy affects both images and is tracked separately as a portability risk.

## Verified contract coverage

| Official cohort | Cards per image | Result | Interpretation |
|---|---:|---|---|
| Treasury bills 3M/6M/1Y, including F3 joint tenor grids | 8 | 8/8 execution, grid and official gates | Existing generic asset lookup reads UST_3M, UST_6M and UST_1Y from rates_daily. Percent-per-annum levels retained. |
| ECB-derived MXN/BRL/ZAR/KRW/INR, including joint cards | 11 | 11/11 execution, grid and official gates | em_fx_ecb_daily is read by the existing generic parquet/asset path. Inputs already contain currency-per-USD crosses. No second EUR/USD conversion is applied. |
| Existing H.10 G10, including EUR/JPY/CHF joint grid | 3 | 3/3 execution, grid and official gates | Authored quote conventions retained; no inversion or new panel routing. |

Every card keeps its original bytes, cutoff, text, family, target frequency and horizon list. The inventory records all panels, series metadata, units and target dates. All input panel observations end at or before cutoff; no answer files, symlinks or reference directory occur in mounted units. All realized grids and target-date mappings match exactly. Missing-file, insufficient-history and overlapping-grid errors: none in this set. All forecasts have finite values, exactly 1,000 draws per requested cell and no duplicate sample keys.

## Limits of these results

The historical G10 practice panel is H.10; ranked Final G10 is ECB-derived. Generic lookup is not hardcoded to a panel filename, but unseen panel bytes, units and asset spellings have not been executed. No synthetic Final schema is asserted. No new monthly or macro card was published in this set. Existing CPI/NFP tests cannot certify GDP, claims or unseen release-vintage conventions.

## Failure ledger

- Main replay: 0 failed cards; all 44 official CLI score calls admissible.
- No unsupported card was dropped from a denominator.
- Extra resource replay: both processes exit zero and the two candidates remain byte-identical to each other, but their outputs differ from the earlier runner for the same card. This is not a new-asset lookup failure or an FF03-only regression. The exact cause is investigated in the portability receipt; uncertainty is retained.
- Whole-repository CI: inherited lint and missing research dependencies remain red, separately from actual image execution.

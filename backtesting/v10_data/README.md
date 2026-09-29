## Executive summary (read this first)

V10-DATA downloaded independent source **files**, but the as-of-safe F1 shadow
benchmark is still **not feasible** under the preregistered five-episode gate.
The V9 plus legacy exposure ledger covers 1993–2024. Only 2025 is unexposed
inside 2000–2025. An exploratory pre-1994 date-only rescue has six SELECT
years and four FINAL years, with no confirmed point-in-time source vintages.
No forecast, realization, metric, or CodaBench submission was produced.

## Source mapping and provenance

The private byte-for-byte snapshot is described by `source_snapshot.json`.
The raw files are **not in this public repository**, because they include
post-card observations. Recreate them with
`python -m backtesting.v10_source_snapshot --out <private directory>`.
The snapshot fixes each source URL, SHA-256, date coverage, byte count, and
quote units. It contains six FRED H.10 FX series, DGS2/DGS10 H.15 yields,
CPIAUCSL/UNRATE monthly series, and the French daily market/momentum archives.
The FRED CSV request stops on 2025-12-31; French archive bytes are a current
download and can extend beyond that date.

| F1 target | Source series | Reliability for FINAL |
| --- | --- | --- |
| AUD, CAD, CHF, EUR, JPY, DKK | H.10 via FRED | Provisional current-history market data; historical release snapshot not proved |
| UST_2Y, UST_10Y | H.15 via FRED | Provisional current-history market data; historical release snapshot not proved |
| CPI_ALL, UNRATE | FRED current values | Ineligible as as-of features until ALFRED vintage retrieval |
| MKT, MOM | French daily factors | Secondary only; history is reconstructed/updated |

The historical cards' publicly supplied as-of inputs matched the current
source values on ten checked market/macro target dates. The two checked factor
dates matched after converting percentage returns to decimals. This checks
identity and units, **not** vintage accuracy or future predictive ability.

ALFRED uses `realtime_start=realtime_end=<origin>` for a historical information
set, and its API requires a registered FRED key. None was configured during
this snapshot. An as-of input also needs the original publication timestamp
and lag; a monthly observation date is not its release date. The current
FRED CSVs and factors are not silently promoted to a point-in-time dataset.

## Origin and episode audit

The date-only program `backtesting.v10_data_manifest` verifies all raw hashes,
reconstructs old 3/5/6/8/12 cutoff exposure and reads V9's scored intervals.
It adds V10's inspected dates conservatively. Every calendar year touched by
an origin **or its outcome horizon** is unavailable across all families.
The complete V6/V7 event interval ledger is missing, so an episode absent from
this list is still not guaranteed pristine.

| Period | Year episodes | Status |
| --- | --- | --- |
| 1993–2024 | 32 | Previously exposed; unavailable |
| 2000–2025 after exclusion | 2025 only | One episode; gate fails |
| Provisional pre-1994 FIT | 1972–1980 | Nine years, current-history market data |
| Provisional pre-1994 SELECT | 1982–1987 | Six years, current-history market data |
| Provisional pre-1994 FINAL | 1989–1992 | Four years, current-history market data |

The 1981 and 1988 calendar years are embargoed. Each provisional origin is
chosen by a deterministic hash of card configuration and date from source
nonmissing indexes. The longest forecast horizon must finish within its
calendar-year episode. No row crosses a previously exposed year. The public
manifest contains 366 **provisional date-only** rows: market 326 and factor
40. These rows are highly dependent across cards and are not 366 independent
tests. No monthly macro row is admitted without a vintage/release calendar.

## Fixed gate and next step

The gate requires five market years and three card templates in both SELECT
and FINAL **from archived as-of sources**, with F1 target strata restored.
Observed strict coverage is SELECT 0 / FINAL 0. Even ignoring the vintage
problem, the fixed pre-1994 FINAL has four years. EUR is unavailable before
1999, and macro monthly and factors do not meet the strict source tier.
Changing split boundaries or excluding these F1 targets after seeing this
audit would weaken the preregistered design. V10-A remains blocked.

Manifest file SHA-256:
`85ff57d66bcbb63e599e561a54600ed27f3170239e04b4820abd327306fec4a3`.
Canonical row SHA-256:
`ae7dd2f14f60ffe5484c09079e86c4924c6b2fc7a10c0c41951a3e5409498724`.
Private source metadata SHA-256:
`3309dbd251e0e84e4fc3a8a1bf522dab7825768cff7a6eab1a4f9fb719df09fd`.

To continue V10-DATA, obtain registered ALFRED access, historical release
snapshots for market rates/FX, and archived factor files or equivalent true
point-in-time series. The validation origin ledger must also account for all
V6/V7 event episodes. Run the feasibility audit again on a **new registered
source version** before any model, parameter, or mixture weight is selected.

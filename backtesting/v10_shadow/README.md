## Executive summary (read this first)

V10-0 stops here: **independent validation insufficient**. This folder freezes a
date-only feasibility benchmark, but its F1 SELECT split contains zero cases and
its F1 FINAL split contains only one market episode. No V10 model was fitted,
selected, scored, packaged, or submitted. V5.1 remains the 0.9541 official baseline.

## Frozen files and reproduction

- `v10_shadow_manifest.csv` contains public card configurations, origin dates,
  evaluation end dates, a shared calendar-year episode label, and FIT/SELECT/FINAL.
  Its first comment line is an executive summary. Read with `comment="#"`.
- `v10_shadow_audit.json` records the source date-index hashes, exclusions,
  coverage, failure reasons, and the SHA-256 of the CSV bytes.
- CSV SHA-256: `3146fb07192149ffd732e2b55d0322d227de4b3d4135f0864ab86d6331e8b9a9`.
- Canonical manifest rows SHA-256: see `v10_shadow_audit.json`.
- Run `python -m backtesting.v10_shadow_manifest --root . --out backtesting/v10_shadow`
  from the repository root. An identical public checkout reproduces both hashes.

## Date-only selection and leakage control

Every card uses its common non-null panel date index. The program excludes all
evaluation intervals from earlier 3-, 5-, 6-, 8-, and 12-cutoff procedures and
every V9 manifest interval on the same card. It hashes card configuration and
date to choose no more than one origin per card and calendar year, then rejects
overlapping selected intervals within a card. No realized value magnitude,
score, or future text is used to choose an origin.

FIT origins are dated 2000–2008 and must finish before 2009. SELECT origins are
dated 2010–2016 and must finish before 2017. FINAL origins start in 2018.
Calendar years 2009 and 2017 are embargoed; all cards in a calendar-year market
episode have the same split. The end-date and embargo checks separate outcome
windows across splits. The FINAL dates are listed for audit, but no FINAL
outcome or metric was opened.

| Family | Public cards | Cards with any safe origin | FIT origins | SELECT origins | FINAL origins | SELECT / FINAL episode years |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| T2-F1 | 23 | 4 | 4 | 0 | 1 | 0 / 1 |
| T2-F2 | 27 | 19 | 100 | 76 | 33 | 7 / 6 |
| T2-F3 | 22 | 14 | 93 | 75 | 45 | 7 / 7 |
| T2-F4 | 31 | 27 | 217 | 129 | 45 | 7 / 7 |

The 818 selected dates are **not 818 independent market experiments**. There
are repeated cards and correlated assets in the same year. F1 has only three
remaining eligible origin years (2001, 2005, 2018); all monthly F1 target
configurations lack a safe origin. A calendar-year episode is a coarse cluster,
not proof of independence within that year. The detailed frequency, target type,
cell, and horizon counts are in the audit JSON.

## Predeclared feasibility gate and result

For every family, SELECT and FINAL each require at least five distinct episode
years and three card templates, and every original target stratum must be
represented somewhere. F1 fails both split gates and loses daily and monthly
level target strata. These failures
arise from dates and configurations alone, before looking at any V10 forecast.

The result **does not authorize Phase 1**. Existing public panels may have
revisions, and a complete per-card origin ledger for V6/V7 event research is
not present here. Even the other three families cannot be advertised as a
genuinely untouched independent OOS benchmark. Obtain new frozen data with
real-time vintages and predeclared evaluation dates before building or selecting
a conditional distribution engine. Do not use Development to fill the gap.

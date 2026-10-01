## Executive summary (read this first)

SURPRISE-01 uses official archived U.S. macroeconomic releases as public,
point-in-time research inputs. It does not use commercial consensus data or
current revised macro series as first releases. A verified independent 2025
holdout is not claimed: a FRED export ignored the requested 2024 date limit
and was loaded during source-overlap auditing before the model freeze.
No 2025 target labels or scores were calculated. The conservative status is
NO_INDEPENDENT_FINAL_HOLDOUT; subsequent evaluation uses exposed 2001–2024
history with chronological, maturity-safe fitting.

### Competition rules actually inspected

Audit date: 2026-10-01. Parent:
`809b2e192e36db0bcb25b9d62e19b7680a4f3e91`.

| Question | Finding | Evidence |
| --- | --- | --- |
| External public historical data | Conditional permission; public, lawful, licensed and track-permitted data must respect each task cutoff. No blanket ban was found. | [Official Rules §6.1](https://www.agenthon.net/rules/); [Artifact policy](https://github.com/Agenthon-2026/track2-forecasting-public/blob/main/docs/ARTIFACT-POLICY.md), revision 2026-09-21.1, blob `713c0fd6b2edd4e4e5b16117aefca333b0313311`. |
| Runtime internet | Arbitrary data fetching is prohibited. Restricted egress supports only the organizer House route. | Track README, leakage rule 3; [current Development runtime](https://github.com/Agenthon-2026/Agenthon2026-public/blob/main/docs/DEVELOPMENT-RUNTIME.md), blob `344f12e77aa0314e3d0fd42e2fdff903a43cb6be`. |
| Offline fitted artifacts | Non-neural linear models, calibration parameters and static tables are allowed with immutable version, actual fitting cutoff and provenance. | Artifact policy: What you may package; Data cutoff and provenance. |
| Raw official U.S. releases | Underlying BLS, Census and Federal Reserve Board statistical facts are public government data. BLS explicitly publishes its work in the public domain. | [BLS copyright policy](https://www.bls.gov/bls/linksite.htm); [Track data license](https://github.com/Agenthon-2026/track2-forecasting-public/blob/main/DATA-LICENSE.md), blob `b0808ff444d2b6aa26082769641249e9d5f8544a`. |
| Consensus raw data | No reproducible pre-release historical consensus source with established reuse rights was obtained. No raw consensus is collected or bundled. | Source audit; TRUE_CONSENSUS_SURPRISE sample count is zero. |
| Compact derived artifact | First-release innovations and linear response parameters may be stored offline subject to the same information cutoff. Derived material does not bypass cutoff or licensing. | Official Rules §6.1; Artifact policy. |

The fork README's older adapter and token-budget descriptions are superseded
by the current organizer policies. The artifact-policy permission is not an
approval to deploy a model trained in 2024 on an earlier-as-of competition
card. Historical research forecasts must fit exclusively on earlier matured
labels. No competition image or submission is produced in this study.

### Primary source universe, fixed before outcome scoring

| Family | Actual representation | Archive source |
| --- | --- | --- |
| CPI | First reported seasonally adjusted monthly percent change | [BLS CPI archive](https://www.bls.gov/bls/news-release/cpi.htm) |
| Core CPI | First reported all-items-less-food-and-energy monthly percent change | Same CPI release, shared release-event cluster |
| Payrolls | First reported change in nonfarm payroll employment, thousands | [BLS Employment Situation archive](https://www.bls.gov/bls/news-release/empsit.htm) |
| Unemployment | First reported unemployment rate, percentage points | Same employment release, shared release-event cluster |
| Retail Sales | Advance retail and food-services monthly percent change | [Census MARTS historical releases](https://www.census.gov/retail/marts/historic_releases.html) |
| Industrial Production | First reported total IP monthly percent change | [Federal Reserve Board G.17 archive](https://www.federalreserve.gov/Releases/g17/) |

The archive collectors select the release's newest reference period, never
the later-revised prior-month column. Parse failures are quarantined before
scoring and reported by family. They are not replaced with current-series
values. ALFRED and the Philadelphia Fed first/second/third-release files
were audited as supporting vintage-aware sources. The primary numerical
ledger comes from the original issuing agency's dated release.

### Direct archive checks

- BLS CPI release 2024-12-11 reports November headline and core monthly
  changes as 0.3%; these are the current-period entries in that release.
- BLS employment release 2024-12-06 reports November payroll change
  227,000 and unemployment 4.2%.
- Census retail release 2024-11-15 reports October advance monthly change
  0.4%, separately marking the prior-month revision.
- Board G.17 release 2024-12-17 reports November IP monthly change -0.1%,
  separately marking prior estimates.
- A historical BLS employment release 2001-02-02 reports January
  payroll change 268,000 and unemployment 4.2%.

These checks demonstrate what must be selected. The machine parser and its
coverage/error ledger are validated against these original documents.

### Expectation, timing and exposure

No market consensus is inferred. Every primary signal is named
RELEASE_INNOVATION: current first-release actual minus the immediately
preceding valid first-release actual of the same family. This deliberately
simple expectation ignores later revisions. Standardization uses an
expanding sample standard deviation of strictly earlier innovations,
minimum 24, clipped to [-5,5]. The original raw unit is retained.

Known 08:30 Eastern BLS/Census and 09:15 Eastern G.17 release timestamps
precede the panel observation times. If the actual release timestamp cannot
be verified from the archived document, use the next valid business
observation. Targets start strictly after the origin observation.

Exposed history: 2013–2023 from prior studies; 2018–2023 THESIS final;
2024 ORIGIN final. The 2025 raw-export audit incident means no 2025
independent final claim is made. 2025 is not reassigned as a validation
period or used for fitting. EM source IDs are unverified in the original
manifests, and French/AQR factor-data reuse and definition continuity need
separate confirmation. No 2025 market extension is accepted.

Raw archives, parsed event values, market target labels and per-event scores
remain outside Git. Public artifacts contain source identifiers, hashes,
coverage, grouped research scores and fitted-parameter provenance.

### Completed acquisition audit before scoring

The calendar audit includes legacy six-digit BLS release URLs and G.17
`default.htm` pages. There are 1,296 requested archives, 324 per source.
Parsed records: CPI 323, Core CPI 323, Payrolls 324, Unemployment 324,
Industrial Production 324, Retail Sales 283; total 1,901 family records.
Exclusions: one empty BLS CPI response (2016-06-16), and 40 Census reference
periods 1998-01 through 2001-04 with the earlier retail-only definition.
They are not spliced into retail-and-food-services history. December 2024
retail is released in 2025 and excluded. The Census 2007-01 PDF was retrieved
from the same official file's `?download=1` alias after its canonical response
was unusable; no third-party source was substituted.

A scan spot-check (Census 2006-01-13, reference December 2005) confirms
current +0.7% and a separate prior-month revision to +0.8%. G.17 2024-05-16
says little changed, but its preliminary monthly column explicitly prints
0.0%; a qualitative phrase is not rounded to zero without a numeric column.
The unaccepted FRED audit export SHA-256 is
`17992c59348db3e66dfc04957c733f66ddb19cedf3a80b63cdac11d34e7d9e0b`
(1,150,416 bytes). It is not an accepted fitting input.

The execution environment reset during baseline preparation. Source code
was recovered from the verified GitHub checkpoint, and original agency
archives were recovered from previously preserved copies. No SURPRISE
candidate had been scored. The specification and exposed-period status
were retained; baseline caches are regenerated with the same fixed seed.

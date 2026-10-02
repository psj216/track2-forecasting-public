# INFO-01 — New Pre-Outcome Information Source Audit

## 1. Executive summary

**Decision: SOURCES_FOUND_RESEARCH_ONLY.** Twenty-four candidate sources across all eight required information families were reviewed. Four satisfy the frozen preliminary source gate; the top three are ECB original Survey of Professional Forecasters (SPF), Federal Reserve original Senior Loan Officer Opinion Survey (SLOOS), and New York Fed original Survey of Primary Dealers (SPD). The single primary source is **ECB SPF original releases**, quality score **17/20**, PIT **B**, novelty **HIGH**, initial asset scope **EUR only**. These are source-quality scores, not forecasting scores or evidence of alpha.

No forecasting model or router was fitted, no new CRPS was calculated, and no V5.1, R2 or T0 Ridge parameter, feature or threshold was changed. INFO-01 does not establish predictive value. The next concrete action is a complete ECB original-release/field/errata acquisition audit, followed by a separately frozen LOCATION-02 research-crossfit implementation. Independent validation is unavailable now; `READY_FOR_LOCATION02=false` and `READY_FOR_SUBMISSION=false`. A research-only protocol draft is preserved, not executed.

Research parent: `a37f232d5fcdf8dd8fa1c44e30bde68b3dda458c`. Branch: `track2/info-01-new-information-audit`. PRE_RESULT_INFO01: `0bd2a1e768156d74f82a9959a62da40184d30d87`. The implementation/gate/protocol was frozen and remotely verified before source ranking. RESULT SHA and final remote/recovery proofs live in an external completion receipt to avoid a self-referential commit identifier.

## 2. Why new information is the next research axis

The prior-channel ledger has 31 entries covering own/cross-market prices, shock propagation, macro innovations and simple statistical expectations, card semantics/routing, distribution engineering, and additional expectation/positioning probes. A rejected acquisition/PIT channel is distinguished from a source actually tested and found weak. No failed source is silently renamed new information.

TEXT-ROUTE-AUDIT-02 primary ST0 logistic was 1.007942, its 2-way oracle 0.953566, frozen R2 always 0.980115, exposed structural routing 0.969262 and secondary T0 Ridge 0.957520. These inherited descriptive scores are not recalculated here. The final parent verdict was NO. T0 Ridge remains a frozen descriptive lead only. CEILING's future-informed location headroom is mathematical opportunity, not proof that any present-day source predicts it.

The question is whether source information genuinely adds pre-outcome expectations, bank behavior or positions beyond ordinary price/text history. Source quality is a necessary feasibility screen; only a later properly frozen experiment can test forecast-error relevance.

## 3. Current competition rules and data constraints

The current official policy and repository task/data artifacts were inspected; the rule evidence and exact Git blobs are recorded in `competition_data_constraints.md` and the environment ledger. Per-task cutoff, source provenance, data rights and offline availability apply to any future bundle. The evaluation runtime is CPU-only, with the documented 16 CPU/128 GB/1800-second constraints. Additional neural checkpoints are not assumed permissible. A permissive repository code license does not license third-party data.

The numeric research-probe cutoff is 2024-12-18. Later documentation can explain schema or current rights but cannot be used as a historical observation. Nothing was purchased and no private vendor account was used. Licensed CME/Consensus Economics/LSEG access and redistributable historical vintages were not demonstrated. Current public charts do not substitute for licensed archived originals.

ECB statistics reuse requires attribution, accuracy and clear identification of modifications; named-author publications have additional exclusions. New York Fed material has its own use/storage/copyright conditions and is not automatically treated as federal public-domain data. BoE material is restricted to the applicable personal/internal noncommercial use here; third-party survey microdata rights are not assumed. Public Git contains minimal derived audit facts and hashes, not the fetched document corpus. Contest compatibility remains conditional on the actual future data bundle and task cutoff.

## 4. Source inventory

All 24 candidates have complete source inventory, documentation, PIT, novelty, asset and horizon rows. The following table summarizes the ranked candidates and representative exclusions; full values are in the CSV artifacts.

| Source | Information family | PIT | Novelty | Admitted asset scope | Quality /20 | Audit disposition |
|---|---|---|---|---|---:|---|
| ECB SPF original releases | True consensus | B | HIGH | EUR | 17 | Primary, research only |
| Fed SLOOS original releases | Liquidity/credit conditions | B | HIGH | US rates; MKT plausible | 17 | Shortlist #2 |
| NY Fed SPD original releases | Policy expectations | B | HIGH | US rates; FX plausible | 15 | Shortlist #3 |
| BoE original inflation-attitudes headlines | True survey expectations | B | HIGH | GBP | 14 | Eligible #4, outside top three |
| US SPF already tested | True consensus | B | REDUNDANT | Prior tested scope | See scorecard | Do not retest |
| Consensus Economics | True consensus | D | HIGH | Potential FX/macro | 11 | Licensed historical access unverified |
| CME policy futures | Market-implied policy | D | HIGH | US rates | 10 | Contract vintages/rights unverified |
| CFTC legacy / TFF | Positioning | D | HIGH | Potential FX/rates | 14 / 13 | Corrections/backfills unresolved |
| Treasury DTS cash balance | Liquidity | D | MEDIUM | Potential US rates | 12 | Endpoint blocked, original vintages unverified |
| GDELT 2 events | News/events | D | MEDIUM | Plausibility only | 9 | Ingestion/PIT/rights issues |

Remaining sources include LSEG OIS and I/B/E/S, H15 TIPS, NY Fed dealer positions and ON RRP, tested TIC Form S and H41 reserves, Atlanta Fed GDPNow, ECB SMA, ACM term premia, BIS REER, EIA inventories, and the BLS calendar. This covers true consensus, market-implied expectations, positioning, liquidity, real-time expectations, fundamentals, news/events and structural calendar information. No hundreds-variable expansion or outcome-based screen was used.

## 5. Point-in-time integrity

PIT-A requires exact vintages, proven availability and field revision audit. PIT-B allows reconstructible original-release fields with evidenced publication dates and an explicit correction policy. None of the shortlisted sources has been promoted to PIT-A. The admitted B classification is field-scoped and preliminary; full-panel revision/errata verification remains mandatory before fitting. Current revised history with unverified availability is D, not silently C.

ECB's archived dated release history supports admission from 2015-01-23. An inspected 2010Q4 PDF proves that a report/field existed but does not prove its release date; it is rejected from usable history. Only the original round's published point forecasts are eligible, not current microdata or aggregate CSV history.

SLOOS uses original current-round bank-count tables and evidenced release dates. The October 2024 results were published **2024-11-12**, not an inferred November 4 date. The 2012 panel expansion is a structural break. All-bank C&I denominators exclude banks reporting that they did not originate the loan category.

SPD's December 2011 round first became publicly available on **2012-01-04**. The January 2018 result date, **2018-02-22**, is reconstructed at B quality from the official one-day-after-FOMC-minutes rule and the February 21 minutes publication; this is not an immutable timestamp. September 2024 results and same-content numerical export became available **2024-10-10**. The exported column `survey_release_date=2024-09-04` means survey distribution, and the due date is September 9: neither is the public results date. This schema trap is recorded and tested. Combined SPD/SMP rows require explicit panel selection before any future feature use. Later corrected appendices/asterisked reports are excluded unless the original admitted field version is established.

BoE original headlines are distinct from its subsequently revised research dataset and third-party GfK/Ipsos microdata. Earlier ambiguous metadata is quarantined; admitted source history starts in 2014. Online collection and provider/panel changes are documented. For all sources, date-only availability uses a conservative timezone-aware end-of-publication-date bound. Survey response dates, observation dates and event dates never activate features. Real release calendars and holiday delays must be established before fitting; the parent's weekday cutoff helper is not a full exchange holiday calendar.

## 6. Novelty versus already tested channels

ECB SPF adds euro-area survey expectations, unlike the already tested US SPF series. The geography and original-release field scope make this a new candidate source, not a claim that another SPF model will work. SLOOS adds reported bank lending standards/demand rather than a transformation of US Treasury returns. SPD adds participant distributions for prospective policy, distinct from a current rate or price-derived state; prior partial source work is disclosed instead of erased.

US SPF, TIC Form S and H41 reserves are explicitly marked already-tested equivalents and barred by the gate. ACM term premia and some market-state transformations have low novelty and unresolved historical model vintages. Market-implied prices can be valuable only if genuinely new contract information and historical as-of values exist; reusing past spot prices under a new feature name is excluded.

## 7. Asset and horizon mapping

The actual audited union is 28 assets, including 25 continuous market assets and three public macro targets. Commodity targets are absent. Public cards include noncanonical horizons as well as the canonical 5/21/63/126/189 business-day grid; they are not relabeled to fit a source.

Primary coverage is **EUR**, not all FX or all cards. Euro-area HICP/GDP expectations plausibly affect EUR policy/growth location over the five listed horizons, but annual calendar-year forecast targets are not themselves 21-day FX labels. SLOOS plausibly maps to US rate assets and MKT; SPD to US rates and selected FX; BoE to GBP. EIA's genuine inventory information fails actual asset coverage here, and I/B/E/S would need historical constituent/factor mapping. No broadcast of a commodity signal to AUD/CAD is automatically declared direct coverage.

## 8. Bounded availability probe

Twelve distinct original rounds were checked: three each for ECB, SLOOS, SPD and BoE. Complementary PDF/table/XLSX forms refer to those same rounds, not additional numeric periods. Original HTTP response bodies were hashed and receipts record URLs, retrieval time and byte counts. These are exact current retrieval bytes, **not immutable historical byte proof**. Web-tool response hashes are labeled separately and never presented as provider bytes.

Examples demonstrate schema only: ECB 2019Q4 next-year HICP/GDP forecasts are 1.2/1.0%; ECB 2024Q4 next-year forecasts are 1.9/1.2%. The latter are 2025 expectations published in October 2024, not 2025 realized outcomes. SLOOS bank counts and their original denominators were checked, without reconstructing a hindsight bank roster. SPD's September 2024 PDF has numerical-font extraction gaps, so the provider's same-round XLSX was checked; its single sheet has 2,199 rows and 21 columns. No full forecast panel was constructed.

PDF metadata can be misleading: the December 2011 SPD file retains an older title; the January 2018 PDF contains hidden 2016 template text, while its rendered cover establishes January 2018. An early BoE PDF has conflicting title/body dates and is excluded. Some guessed SLOOS table URLs returned 404; observed native links and matching PDFs were used once. A FiscalData endpoint returned 403; access was not faked.

A current Board H15 documentation page automatically surfaced a 2026 rate table during release-time inspection. This incidental exposure is explicitly recorded, excluded from probes/features/labels/ranking, and does not justify an untouched 2026 holdout. No new target dataset was loaded. The audit does not falsely claim that every browsed page contained only pre-2024 numbers.

## 9. Frozen source-quality scorecard

Ten criteria were fixed at 0–2 points: PIT integrity, novel information, historical depth, asset coverage, horizon relevance, machine readability, reproducibility, offline feasibility, licensing/contest feasibility, implementation ease. Maximum quality score is 20; the preliminary gate requires at least 14 plus PIT-A/B, novelty HIGH/MEDIUM, proven publication, accessible/reproducible transformable source, research use allowed, contest use not prohibited, asset coverage, and at least eight years/three eras of accepted history.

ECB and SLOOS both score 17. The frozen family tie priority puts true consensus first, so ECB wins without changing weights. SPD scores 15; BoE 14. A high score does not override a failed gate: CFTC legacy scores 14 but remains ineligible because historical corrected/backfilled values are not proven as-of. Outcomes, CRPS gains and winning-card labels never enter selection; tests verify that adding invented outcome fields cannot change the shortlist.

## 10. Top-three shortlist

**1. ECB SPF originals:** original published euro-area next-calendar-year HICP and real GDP point forecasts; accepted dates 2015–2024, EUR only, quarterly cadence. Straightforward original documents and source reuse conditions. Risks: field-level errata, calendar-target rollover, annual expectations versus daily trading horizons, small effective number of independent releases, and absence of a full acquisition manifest.

**2. Fed SLOOS originals:** US bank standards and demand counts, quarterly reports with independently evidenced publication dates. New lending information and broad US rate plausibility. Risks: response composition, panel changes, denominator consistency and actual date/time verification throughout the panel. Not an independent alpha test.

**3. NY Fed SPD originals:** prospective policy modes/probabilities, published after meetings/minutes rather than when respondents answered. Risks: publication reconstruction, changing questionnaires, hidden PDF templates, numerical extraction, combined panel exports and revised appendices. Full consistent original main-field history remains necessary.

BoE is the fourth eligible source, outside the frozen top-three limit; its narrower asset scope, panel breaks and research rights constraints are not repaired with another ranking pass.

## 11. Single selected primary

`INFO01_PRIMARY_SOURCE=ECB_SPF_ORIGINAL`. This is a source-quality selection, not a statement of predictive superiority over SLOOS. Only original current-round HICP and GDP point forecasts for the next calendar year are initially admitted. The accepted period is 2015-01-23 through 2024-10-18. The full roughly 40-release acquisition/field/errata manifest is **not yet built**, and `full_dataset_ready=false`.

Before LOCATION-02 fitting, each eligible original release needs its exact source document, evidenced publication date, field/units/target year, original-versus-amended status, hash, and source-rights record. Missing or unproved rows remain inactive; they cannot be replaced with current revised CSV values.

## 12. Independent validation audit

`INDEPENDENT_VALIDATION_UNIVERSE=NOT_AVAILABLE`. The old continuous universe already covers 1,250 origins/135,994 cells across 2001–2024; its exposed 2010–2024 evaluation includes 780 origins/82,184 cells. The 24 proxy cards are already exposed. Renaming 2020–2024 a holdout or adding a source cannot reset target exposure.

No untouched asset set, independent public-card cohort, clean external continuous ledger or new labels was verified. A prior SURPRISE export incident exposed post-cutoff raw data, so 2025 is not established as clean merely because it was not scored. The H15 inspection incident is also disclosed. Sealed or later prospective cards/labels were not probed. Any future independent validation must freeze source/parser/model/cutoffs before clean prospective outcomes become available.

## 13. Rejected sources and gates

Commercial vendor claims about historical consensus, OIS, I/B/E/S and futures vintages are documentation, not proof of accessible licensed bytes. CFTC observation dates do not prove release dates, and corrected/backfilled records require version-aware archives. Dealer positions, ON RRP, BIS and H15 current series lack the demonstrated full original-vintage history needed here. Treasury cash-balance API access/reconstruction is unresolved.

GDPNow is a model estimate, not true consensus; pre-live archive backcasts are not contemporaneous public forecasts. ECB SMA's public history is too short. GDELT native launch history differs from older backfilled events, and ingestion/duplication/content rights are unresolved. Calendar event structure is low novelty and not a forecast of outcomes. EIA fails the actual target-asset gate. None of these failures was repaired through an outcome-based selection or model expansion.

## 14. Preserved historical leads

T0 Ridge remains `FROZEN_LEAD_ONLY`. V5.1, R2, historical routing code and parent result artifacts are protected by hashes and Git diff checks. No TEXT-ROUTE-03, alpha/threshold change, added topics, new text embeddings, card-specific rules, oracle reuse or reoptimization of the 24 exposed cards occurred.

## 15. LOCATION-02 frozen research-only draft

`location02_frozen_draft.md` preserves a proposal rather than an implementation. It uses EUR only and five source features: next-calendar-year HICP, next-calendar-year GDP, their previous-round changes for the **same target calendar year**, and business-day source age. A 90-business-day age limit and missing-field inactivity are fixed; there is no hindsight filling, new source search or test-result threshold tuning.

The proposed target is standardized V5.1 center error; a future alpha=1 ridge would change the center of the original draws using original scale, with no new scale/tail/copula model. Monthly origins, train-only preprocessing, train 2015–2019 and annual forward research folds 2020–2024 are specified, with target maturity capped at 2024-12-18 and up to 189-business-day purge. R2 and T0 are not modified. These later folds remain exposed research crossfit, not independent OOS. No part of that model was fitted in INFO-01.

## 16. Limitations, tests and recovery

PIT-B is reconstructibility for a carefully limited original field scope, not immutable full-panel vintage assurance. Quarter-level effective sample size, changing respondents, stale information, target-year rollover, calendar-time precision, uncertain incremental signal and per-source rights are material limits. Multi/F1 safety must be evaluated with full frozen cards in a later authorized experiment; INFO-01 makes no multi-card performance claim.

Tests ran in order: research-specific **53 passed**, directly affected **42 passed**, full repository **593 passed / 2 integration skips / 3 existing pandas deprecation warnings**, common toolkit v2.4.3 **250 passed**. The full suite took 25.10 seconds. All **156 protected parent and PRE files** retain their recorded hashes. Commands, log hashes and scope are in `execution_audit.json`; logs are preserved privately. PRE was remotely verified before source selection. RESULT verification checks parent lineage, remote file blobs, main unchanged and clean working tree. Final remote and archive proofs are recorded externally, because a committed file cannot include its own commit SHA.

The private recovery archive contains branch metadata, PRE/RESULT identifiers, report, implementation/protocol, tests, all result artifacts, STATUS, manifests, scoped evidence and test logs. CRC, per-member hashes and whole-archive SHA256 are verified. Unnecessary raw web-search response corpora and vendor proprietary data are excluded. Resume uses completed stage receipts; completed source downloads are not repeated.

## 17. Final decision and next axis

**SOURCES_FOUND_RESEARCH_ONLY.** Primary: **ECB SPF originals**. New information is plausible and preliminary source feasibility passes, but predictive location information has not been demonstrated. Independent validation is unavailable. `READY_FOR_LOCATION02=false`, `READY_FOR_SUBMISSION=false`, `T0_RIDGE_STATUS=FROZEN_LEAD_ONLY`.

Next axis: finish the full ECB original-release/field/errata acquisition audit, freeze a separate LOCATION-02 implementation before any forecast evaluation, run only the predeclared research crossfit, and obtain prospective independent validation before submission. Do not tune the old text router or treat these source-quality scores as alpha.

### Primary documentation

- [Official Agenthon rules](https://www.agenthon.net/rules/)
- [ECB SPF dated archive](https://www.ecb.europa.eu/stats/ecb_surveys/survey_of_professional_forecasters/html/index.en.html)
- [ECB Q4 2019 original report](https://www.ecb.europa.eu/stats/ecb_surveys/survey_of_professional_forecasters/html/ecb.spf2019q4~909ade9ae4.en.html)
- [ECB Q4 2024 release](https://www.ecb.europa.eu/press/pr/date/2024/html/ecb.pr241018_1~9b5ce6a9bf.en.html)
- [ECB copyright and reuse](https://www.ecb.europa.eu/services/disclaimer/html/index.en.html)
- [Federal Reserve SLOOS archive](https://www.federalreserve.gov/data/sloos.htm)
- [Federal Reserve October 2024 SLOOS](https://www.federalreserve.gov/data/sloos/sloos-202410.htm)
- [New York Fed primary-dealer survey](https://www.newyorkfed.org/markets/primarydealer_survey_questions.html)
- [New York Fed terms](https://www.newyorkfed.org/terms)

Additional original URLs, provider identities, publication evidence, rights and retrieval hashes are in `source_documentation_manifest.json`. The official rule paths and exact Git blob identifiers are recorded in `competition_data_constraints.md`; the rules link above is contextual, not a substitute for those versioned policy files.

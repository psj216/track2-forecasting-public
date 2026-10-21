## Executive summary (read this first)

Both actual Docker images completed and passed all four official gates for all 22 cards. Every paired forecast file and raw component is equal. These are exposed public practice diagnostics, not independent forecasts or normalized leaderboard scores.

The values below apply to **both** original V5.1 and FF03. Each row is in that card’s units. Do not average the raw composites across different units or compare them with historical Development 0.9541.

| Card | Family | Assets | Horizons | CRPS | Variogram | Tail pinball | Raw composite |
|---|---|---|---|---:|---:|---:|---:|
| t2-F1-curve-ust1y-001-ps1 | T2-F1 | UST_1Y | 2,3 | 0.008074996821 | 0.0239962946 | 0.001493246792 | 0.01153503615 |
| t2-F1-curve-ust3m-002-ps1 | T2-F1 | UST_3M | 2,3 | 0.005959308606 | 0.0111744194 | 0.000791215855 | 0.006490223294 |
| t2-F1-fx-eur-020-ps1 | T2-F1 | EUR | 1,4 | 0.007575170041 | 0.004463151587 | 0.0008563107836 | 0.005297792653 |
| t2-F1-fx-inr-010-ps1 | T2-F1 | INR | 1,4 | 0.1733021016 | 0.1197264308 | 0.0166529308 | 0.1258995662 |
| t2-F1-fx-krw-011-ps1 | T2-F1 | KRW | 1,4 | 4.032576898 | 1.654911507 | 0.560375355 | 2.624836972 |
| t2-F1-fx-zar-009-ps1 | T2-F1 | ZAR | 1,2 | 0.1063111267 | 0.002748946934 | 0.006652746467 | 0.05531079674 |
| t2-F2-curve-ust1y-003-ps1 | T2-F2 | UST_1Y | 3,4 | 0.007452234966 | 0.0004284612701 | 0.002476603019 | 0.004349976468 |
| t2-F2-curve-ust6m-004-ps1 | T2-F2 | UST_6M | 1,4 | 0.06275608109 | 0.008011425839 | 0.005905408537 | 0.03496255 |
| t2-F2-fx-brl-012-ps1 | T2-F2 | BRL | 3,4 | 0.03506146244 | 0.004757555404 | 0.003020634485 | 0.01956212474 |
| t2-F2-fx-eur-021-ps1 | T2-F2 | EUR | 2,4 | 0.01246693468 | 0.01758335467 | 0.001221804401 | 0.01175283462 |
| t2-F2-fx-krw-015-ps1 | T2-F2 | KRW | 1,3 | 3.301358703 | 1.075424243 | 0.4049853633 | 2.054303697 |
| t2-F2-fx-mxn-013-ps1 | T2-F2 | MXN | 1,4 | 0.04982825237 | 0.02187305481 | 0.009785487038 | 0.03343314003 |
| t2-F2-fx-zar-014-ps1 | T2-F2 | ZAR | 1,4 | 0.1631491456 | 0.060240978 | 0.01448248683 | 0.1025433636 |
| t2-F3-curve-ust3m-ust6m-ust1y-006-ps1 | T2-F3 | UST_3M,UST_6M,UST_1Y | 3 | 0.009612046242 | 0.005000073416 | 0.001152636935 | 0.006536572532 |
| t2-F3-curve-ust3m-ust6m-ust1y-ust2y-005-ps1 | T2-F3 | UST_3M,UST_6M,UST_1Y,UST_2Y | 3 | 0.02652591797 | 0.02301110528 | 0.002409765147 | 0.02064824359 |
| t2-F3-fx-eur-jpy-chf-022-ps1 | T2-F3 | EUR,JPY,CHF | 3 | 0.252801648 | 0.01607251676 | 0.02021009273 | 0.1352645976 |
| t2-F3-fx-krw-inr-zar-017-ps1 | T2-F3 | KRW,INR,ZAR | 4 | 0.7641036468 | 0.004292208445 | 0.2008580594 | 0.4235110978 |
| t2-F3-fx-mxn-brl-zar-016-ps1 | T2-F3 | MXN,BRL,ZAR | 2,4 | 0.05876396419 | 0.04658924626 | 0.01013996063 | 0.0453867481 |
| t2-F4-curve-ust3m-008-ps1 | T2-F4 | UST_3M | 1,3 | 0.01760884608 | 0.002261857425 | 0.001877178689 | 0.009858416008 |
| t2-F4-curve-ust6m-007-ps1 | T2-F4 | UST_6M | 1,2 | 0.004792778164 | 0.000244598382 | 0.001556467991 | 0.002781062195 |
| t2-F4-fx-brl-019-ps1 | T2-F4 | BRL | 3,4 | 0.1098407335 | 0.09098660873 | 0.02412935113 | 0.08704221958 |
| t2-F4-fx-mxn-018-ps1 | T2-F4 | MXN | 1,4 | 0.06562338643 | 0.03325363732 | 0.009139158099 | 0.04461561603 |

All 22 paired differences are exactly zero for marginal CRPS, variogram, tail pinball and raw composite. No forecasting parameter was changed after observing scores.

## Coverage and grouping

- Usable cards: 22/22 for each candidate; unscored or omitted: 0.
- F1: 6/6; F2: 7/7; F3: 5/5; F4: 4/4 for each candidate.
- Eight UST cards, eleven ECB-derived EM cards, three H.10 G10 cards.
- All cards have more than one cell. Single-cell official-card result: NOT_RUN; one-cell slices do not create official cards.
- Per-asset and per-horizon component slices are in the JSON receipt. They call pinned official component functions after forecast generation; they are diagnostic subsets, not new official normalized scores.
- No official normalized aggregate was generated: no authenticated organizer reference-scale bundle was supplied and this task did not reimplement the M0 generator. The public M0 procedure was reviewed.
- The representative cross-runner discrepancy discovered in a later resource run is preserved separately. The table describes the original frozen 44-process replay only.

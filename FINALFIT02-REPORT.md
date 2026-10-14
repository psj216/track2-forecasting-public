## Executive summary (read this first)

**CANDIDATE_REPAIR_NEEDS_VALIDATION**. The original V5.1 image works for covered existing daily assets at 1–4 BD, but fails the newly published monthly observation-period contract. A separate minimal adapter passes the registered Docker checks. New Final target schemas and a standalone release remain unverified.

1. Classification: CANDIDATE_REPAIR_NEEDS_VALIDATION; original is SAFE_INCOMPATIBLE for explicit monthly metadata.
2. Branch: track2/final-fit-02-short-horizon-compatibility.
3. Parent: `78e438c0aeb7ce888a1b8e9ba4f90b99dcf3ed20`.
4. PRE: `32fdc3931d36adf471813203431dd7226c76a8d7`.
5. RESULT: the enclosing remote report commit; executable candidate source is `9108ba25737dc88fcdeb478d45c749dddc2bbcb0`. Remote RESULT SHA is supplied in the delivery response (a commit cannot embed its own hash).
6. Current rules: verified official October 13 corrections; Final October 26 20:59 KST, one upload, as-of October 26, 1–4 BD, 1,800 seconds/unit and 43,200 seconds total.
7. Announced new ~30-card practice set: not found as of the recorded check; did not wait or repeatedly search.
8. Inputs: historical synthetic contract fixtures plus two current official monthly public input examples. No targets, ranked cards, current market values or future Final truth.
9. Exact image: `docker.io/jotj216/track2-f4-approved@sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874`.
10. Actual Docker: original run [38588467433](https://github.com/psj216/track2-forecasting-public/actions/runs/38588467433); candidate overlay run [38589731625](https://github.com/psj216/track2-forecasting-public/actions/runs/38589731625). Anonymous pull, linux/amd64, interface 2.0, no VOLUME, all 26 source hashes match.
11. Each designated run has 13 input cases / 22 forecast processes. Original 21 zero exits, one correct missing-history refusal; 19/22 receipt expectations, one test-validator error and two wrongly accepted monthly negatives. Four additional semantic assertions fail. Candidate 19 zero exits + three correct refusals = 22/22 expectations; identical semantic assertions 4/4 pass. An expected error exit is not a successful forecast.
12. 1–4 BD: tested daily keys remain distinct and grid-complete; covered repeats byte-identical. Not a proof of forecast loss.
13. New UST 3M/6M/1Y: BLOCKED, canonical contract not published/recovered. Existing UST_2Y/5Y/10Y/30Y tested.
14. ECB G10: BLOCKED. Existing EUR/JPY USD quote fixtures tested; raw ECB EUR-base definition is not an organizer mapping.
15. EM: existing BRL/INR numeric daily fixtures pass; full ECB EM set remains BLOCKED (MXN/ZAR/KRW contract unavailable).
16. Macro: original explicit monthly mapping fails; candidate CPI/NFP tests pass. Candidate actual steps are [1,2,3,4], [2,3,4,5], official CPI [8,9], official NFP [2]. GDP/claims and other new release metadata remain BLOCKED.
17. F1–F4: registered daily family routes pass; candidate parquet remains byte-identical to original in every daily case.
18. Errors/fallback: short history refuses explicitly. F2/F3 family_frozen and neutral-text numeric fallback are recorded intentionally, not concealed transport failures. Monthly missing/conflict now refuse. No House call is used.
19. New compatibility bug: CONFIRMED explicit monthly horizon handling, not proven forecast-score degradation.
20. Minimal repair: only isolated candidate_monthly.py adapter and exact official helper; tool fixes for valid card IDs, permissions and sentinel classification. All original forecasting code, weights, prompts and image preserved.
21. Practice diagnostic: NOT_RUN; no CRPS/variogram/tail/composite score generated. Historical current-vintage inputs do not constitute independent PIT/OOS evidence.
22. V5.1 Final safety: preserve safe image/ZIP, but do not declare global compatibility or automatically submit it. Original monthly route has concrete contrary evidence; candidate is not Final-eligible.
23. Remaining risks: canonical new assets/ECB quotes, new macro release/vintage semantics, heterogeneous monthly grids, standalone candidate build/whole release, local ZIP bytes, official historical 0.9541 identity and predictive performance UNKNOWN.
24. NEXT ACTION: once organizer practice schemas are available, inspect canonical IDs/units and macro observation periods first; run only the remaining blocked strata. If Final includes explicit monthly cards, independently release-validate a separately built repair image before considering it. No automatic submission or tuning.

Observed max per-process wall time: original 1.995s; overlay 2.069s. Max total output: original 41258 bytes; overlay 41258 bytes. Containers enforced 2 CPUs / 4 GiB / 256 PIDs, read-only root/input and tmpfs /tmp with network none. Peak RSS was NOT_MEASURED; the full Final batch runtime is UNKNOWN.

Fresh scoped Ruff check passed. The checks() assertion AST stayed identical across RED and candidate. Inherited repository CI failures are not hidden or converted into a release PASS; no full release proof is claimed. Source/archive/test code, manifests, logs, predictions and hashes are retained in Actions artifacts and JSON receipts. Raw forecast outputs are predictions, not realized answers. Earlier broad workflow paths caused redundant audit executions during receipt commits; their outputs are not counted as new evidence, and paths were narrowed before the candidate checkpoint.

No protected branch, Docker tag, immutable image or Windows ZIP was changed. No Team Key, House token, CodaBench submission, deployment or model tuning was used.

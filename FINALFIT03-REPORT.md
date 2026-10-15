## Executive summary (read this first)

**REPAIR_VALIDATED_WITH_SCHEMA_GAPS.** The monthly repair is now a standalone Docker image, not an overlay. Available-scope release checks pass. Unpublished Final schemas and predictive performance remain unresolved.

1. **Classification:** REPAIR_VALIDATED_WITH_SCHEMA_GAPS.
2. **Branch:** track2/final-fit-03-monthly-repair-release.
3. **Parent SHA:** `d611cff8c2a674f962cecb8cf52f9f8f8cc91c41`. The protected FF02 branch is unchanged.
4. **PRE SHA:** `a4475063928d1698646cb498c620148feb4898ba`.
5. **RESULT SHA:** the enclosing remote report commit, supplied in the final delivery response. Executable image source is `c5b8bbbd6227888b7a3dc0bbd05dc414d2d7c3f6`; TEST checkpoint `b7f4f3307556ccbe0aa5822b541bdb086f1c8f11`. A report commit cannot contain its own commit hash.
6. **Official version:** Track b9c663d239a0e6b86ebd3f3f2d5aead88516067d; common v2.6.1 = 03c50a0036aaf72675d353aef4c7c01ca86d1fcf. Monthly helper blob 04650003bac311fd5c0cee7cb2c8d17484ddcbe6. Final October 26 20:59 KST; one upload; ranked as-of October 26; 1–4 BD; 1,800 seconds/unit and 43,200 seconds/run.
7. **Practice:** PRACTICE_NOT_YET_PUBLISHED at the recorded authoritative check. No waiting, target fabrication or practice tuning. Existing official examples are not relabelled as the new set.
8. **Standalone build:** successful. Wrapper/helper and executable forecast launcher are inside the image. A separate runner restores the archive and executes the official command with input/output mounts only. No host Python files are mounted into any of the 41 forecast runs.
9. **Image identity:** `sha256:23f226ced859978d7a3f16a23c6d1515a1a3bdb14338297f4818d114bcfa2c1c` (local Docker image/config ID, not a registry manifest digest), linux/amd64. Base `docker.io/jotj216/track2-f4-approved@sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874`. Registry digest is NULL because push was prohibited. Archive SHA256 `df232487177cb56cb0ae945b2613fbbebbb24eff702f21712662e589d04f636c`; 195498115 bytes.
10. **Provenance:** source `c5b8bbbd6227888b7a3dc0bbd05dc414d2d7c3f6`; original frozen safe source 47194f28d5188b87cdca1d591d86b9eeda86f7cf, tree f2f9163372ab179c3e58a0dbac00acee119a41cf. All original 26 production file hashes match inside the new image. Runtime dependencies remain pinned by the base digest; no model code or parameters changed.
11. **Monthly contract:** original four semantic failures fixed. Extended RED checks found F3 KeyError, unsupported per-asset grids and damaged-monthly legacy fallback; 7 failed processes were preserved before repair. Final 29/29 monthly expectations pass: 22 normal forecast processes, 7 clear refusals. Includes nonconsecutive periods, lagged anchors, date labels, homogeneous and heterogeneous grids/anchors, duplicate/malformed mappings and duplicate observations/mixed cadence.
12. **Daily A/B:** final 12/12 expectations; all produced files byte-identical to the unchanged original, including metadata/rationale. Normal cases repeat deterministically; one numeric post-cutoff sentinel is deliberately invalid input and proves filtering only. The original was freshly run in the first standalone workflow and then reused by receipt in the final workflow. Same pinned base, dependencies and exact input hashes; different hosted runners are explicitly not claimed to be the same VM.
13. **F1–F4:** tested daily family routes pass, including UST joint and BRL/INR joint. Monthly F3 multi-asset now passes. Family-frozen text fallback remains intentional, recorded and unchanged.
14. **New UST:** 3M/6M/1Y BLOCKED by absent canonical new practice/card metadata. Existing UST_2Y/5Y/10Y/30Y tested.
15. **ECB G10:** actual new ECB cards BLOCKED. Official quote convention is now verified: USD-derived G10 quotes match practice; FF02's earlier transformation uncertainty is corrected. Tested EUR/JPY native-quote fixtures are not actual ECB Final cards.
16. **EM FX:** existing BRL/INR fixtures pass. New MXN/ZAR/KRW identifiers and actual ECB fixtures remain BLOCKED.
17. **Macro:** existing CPI/NFP and synthetic official-contract monthly cases pass. Organizer manifests declare as-of ALFRED inputs and separately stated target vintages; the wrapper neither changes vintage nor substitutes a release date. Independent ALFRED reconstruction, GDP/claims schema and actual new release conventions remain unverified.
18. **Counts:** final verification contains 120 checks: 41 container expectations, 35 frozen-package pytest tests, 25 official helper pytest cases, 8 fixed semantic assertions, 9 frozen-kernel tensor comparisons, 2 official CLI card checks. They are overlapping correctness checks, not 120 independent forecast samples. All pass; zero skips in scoped pytest. Eight process exits are correct refusals, not successful forecasts. Actual normal forecasts = 32; one additional exit-zero run is the adversarial cutoff probe. Full repository is not passed: 61 collection errors and 2,288 lint errors also reproduce at the parent with matching installed dependency lines; missing sklearn/requests/bs4 belong to research modules not shipped in this image.
19. **Resources:** max forecast wall 2.139s; forecast-child peak RSS 200608 KiB (~195.91 MiB); max total output 41258 bytes. Tests enforce 2 CPUs, 4 GiB, read-only root/input, tmpfs, network none and 90-second forecast timeout. RSS is process max, not cgroup peak. Full actual Final run time UNKNOWN.
20. **Behavior differences:** daily output is unchanged. Monthly sampling uses the union of official monthly steps and selects each requested asset/horizon cell from the existing frozen joint paths. Nine neutral-text tensors equal an independent call to the unchanged kernel at those steps; spread/covariance follow that existing kernel. This is a horizon selection repair, not new variance/dependence tuning or architecture.
21. **Practice performance:** NOT_RUN; no CRPS, variogram, tail or composite score manufactured. Independent alpha UNKNOWN. R17/M16 research was not rerun.
22. **Remaining risks:** actual new asset/release schemas, unseen cadence/vintage conventions, all untested schema variants, full historical research-suite environment, public registry availability and Final package readiness. The wrapper's tested monthly route requires the declared targets.target_frequency monthly contract; no universal compatibility with unseen representations is claimed.
23. **Release gate:** tested standalone repair passes; global Final eligibility FALSE because schema/deployment/package gates remain blocked or NOT_RUN. See FINALFIT03-RELEASE-GATE.json for exact scoped values.
24. **Recommended Final candidate:** FF03 is the technical repair candidate; actual Final selection is DEFERRED. Preserve V5.1 as the untouched safety net. No independent performance superiority is established.
25. **NEXT ACTION:** once the official new practice participant-input projection is published, verify its source/IDs/units/release periods and run only remaining compatibility strata. Use the chunked replay tool; score only with actual released targets and the official scorer/M0 context, labelled EXPOSED_PRACTICE_DIAGNOSTIC. Do not tune. Registry publication and Final submission need separate instructions and are not performed here.

## Recovery and reproduction

Final standalone workflow: [38798442114](https://github.com/psj216/track2-forecasting-public/actions/runs/38798442114). [Image archive artifact](https://github.com/psj216/track2-forecasting-public/actions/runs/38798442114/artifacts/12003002655), retention 30 days. First build/RED evidence remains in run 38796987425; it is not overwritten. A checkpoint-triggered redundant pre-repair run was cancelled and is not counted as evidence.

Restore the downloaded candidate-image.tar.gz with a bounded command:

```bash
timeout 120 bash -o pipefail -c 'gzip -dc candidate-image.tar.gz | docker load'
```

The restored local tag is `finalfit03-local:c5b8bbbd6227888b7a3dc0bbd05dc414d2d7c3f6`. It runs `forecast --panels /input --text /input/text --asof YYYY-MM-DD --out /output/forecast.parquet --seed 17` with read-only input/root, tmpfs /tmp, writable output and network none. No test overlay is required.

After actual practice publication, use explicit official source paths and chunks:

```bash
python backtesting/finalfit03/replay_practice.py \
  --units /path/to/official-participant-units \
  --image finalfit03-local:c5b8bbbd6227888b7a3dc0bbd05dc414d2d7c3f6 \
  --official-track /path/to/pinned-track \
  --official-common /path/to/common-v2.6.1 \
  --out /tmp/ff03-practice-private --max-cards 4
```

The replay tool is syntax/lint checked but NOT_RUN on absent new practice. It refuses common answer-tree layouts instead of mounting targets. Actual practice schemas must first be reviewed; the tool does not invent a scoring target layout or M0 normalization.

All original/model assertions are preserved. The original FF02 four-check function AST is e6695c6ee3e79a707ae884751937ce753f87242045d1f30ae0a7ff867bba3562. No main/V5.1/M15/M16/R17/FF02 branch, original image/tag or Windows ZIP was changed. No Team Key, House token, registry push, package creation or CodaBench submission was used.

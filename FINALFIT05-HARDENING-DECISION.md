## Executive summary (read this first)

NO_PATCH. Retain the exact existing FF03 image. HARDENING_RESULT = NOT_APPLICABLE. Severity B is the frozen conservative paired-draw screening classification; observed distribution impact is not material enough to justify replacing the already validated image. This is explicitly not a Severity C result: the PRE paired-RMS threshold was crossed.

## Decision before release regression

The PRE threshold flags B when paired-draw RMS exceeds 5% of IQR; measured maximum is 5.599%. It requires review, not an automatic production alteration. All outputs remain valid, repeats deterministic, raw-score sensitivity below 0.05%, central/tail test quantiles unchanged and empirical distribution movement below 0.3% of IQR. A universal byte-reproducibility requirement was not found in the T2 statistical rerun contract. No A trigger is observed.

A stable secondary ordering would remove the exact-tie component in these measured pools; traces show identical stable orders. It is not proof of universal near-tie portability, and adopting it would reorder many historical pool positions and replace a broad set of legacy fixed-seed draws. That larger behavioral change would buy CPU byte consistency without demonstrated improvement in output validity or material distribution stability. Avoid it this close to release.

NO_PATCH_REASON: sparse draw-coupling changes with small measured marginal and score sensitivity; changing frozen daily behavior is not justified by the evidence. This decision does not claim the numerical risk vanished, statistical rerun success is guaranteed, or unseen Final cards are supported. If future evidence shows crash/gate failure or material distribution movement, revisit with a separately frozen hardening candidate.

Original/FF03 files, archive and images remain untouched. No FF05-HARDENED-CANDIDATE exists. Reuse inherited FF04 22/22; execute targeted monthly and runtime/isolation tests only. No parameter sweep or score-driven patch choice.

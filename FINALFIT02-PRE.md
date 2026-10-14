## Executive summary (read this first)

FINAL-FIT-02 is an immutable V5.1 compatibility audit, not a forecast performance experiment. The safe image, protected branches, Windows ZIP and submissions remain untouched. This PRE fixes the matrix before any new forecast output is observed.

Parent: 78e438c0aeb7ce888a1b8e9ba4f90b99dcf3ed20.
Safe source: 47194f28d5188b87cdca1d591d86b9eeda86f7cf.
Image: docker.io/jotj216/track2-f4-approved@sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874.
Official Track source: f43655cdb624a3e5e5fed772ed9313ef57a54bc5.
Shared source: 6181b9c9f45c93ee526a6692406367a4042da7ad.
Rules: issue 4 comment 6150556139 and shared issue 2 comment 6150553933 (2026-10-13): whole Final 43,200 seconds, per unit 1,800. Ranked as-of October 26; 1–4 business-day targets October 27–30. Final deadline October 26 20:59 KST; one team/track upload. Monthly targets now require explicit observation periods (docs/MONTHLY-HORIZONS.md).

Fixed tests: five synthetic daily cases (F1 UST, F2 EUR, F3 UST, F4 JPY, F3 BRL/INR) with horizons [1,2,3,4], plus synthetic CPI monthly metadata-sensitive cases and two current official monthly public input cards. Repeat each normal case twice, fixed seed 17; F3 >=500 draws, F4 >=1000. Negative cases: missing history, absent monthly mapping, conflicting monthly mapping. One historical synthetic post-cutoff sentinel tests filtering, without any Final future values. New UST identifiers, ECB FX quote/series definitions and GDP/claims not actually defined in official inputs remain BLOCKED; no guessed identifiers.

PASS means actual exact-image Docker execution, forecast schema and exact grid, finite samples, required sidecars, byte-identical repeated parquet, no post-asof input use, interface 2.0, linux/amd64, no VOLUME, no network. Numeric exit 0 alone is insufficient. Monthly mapping must affect sampled observation steps; missing/conflicting mappings must fail clearly under the new official contract. Sampling differences are not evidence of better predictive quality.

Execution: anonymous pull only; no build or push of original image. GitHub Actions if local Docker unavailable. Read-only root/input, writable output, tmpfs /tmp, network none; each forecast <=90 seconds, runner <=510 seconds, job <=9 minutes. Record enforced resource limits and runtime. No secrets. No scoring if the newly announced practice set is unavailable. Existing public monthly cards are compatibility inputs only, not new practice/OOS.

Allowed repair only after an immutable-image reproducible failure and a pre-fix red test: separate candidate code for explicit horizon/schema compatibility, no changes to model constants, prompts, scales or protected production sources. Ambiguous semantics or insufficient time => leave BLOCKED. Two failures of an execution stage => stop that stage and preserve evidence. PRE -> execution checkpoint -> RESULT with remote SHA verification.

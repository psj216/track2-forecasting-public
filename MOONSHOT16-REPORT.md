## Executive summary (read this first)

Classification: INCONCLUSIVE. M16 did not reach implementation. Authoritative remote refs, frozen tree and existing delivery/strict receipts were recovered, and a PRE checkpoint was published. The same local frozen-source checkout failed twice, so the requested stop rule ended execution. Keep the existing V5.1 safe artifact as the preferred Final candidate. No submission was made.

# MOONSHOT16 report

1. **Classification:** INCONCLUSIVE, PHASE_0_STOP_TWO_CHECKOUT_FAILURES. This is a blocked recovery report, not a completed repair.
2. **Branch:** track2/moonshot-16-house-transport-repair, created remotely from the exact frozen M15 source.
3. **Parent SHA:** 361018c14bab3cb7d8da101aa332066644921bac. Remote tree: 9c7a78e3c23078bbe7f9c50f7eb50d65451869db.
4. **PRE SHA:** ec36fbda44ca17c1c64b0b07da7d6adffbdb721b. Remote ref was re-read after publication.
5. **RESULT SHA:** The stopped-state evidence commit is reported in the handoff response and on the branch. It is not a tested repair release. A file cannot embed its own containing commit SHA without changing that SHA.
6. **Modified files:** Runtime files and existing assertions: none. New/updated M16 PRE, contract, repair status, test receipt, fallback matrix, provenance, Final gate, report, RECOVERY and STATUS documents only, on the new branch.
7. **Proxy issue fixed:** No. Uppercase-only failure remains in the original implementation; M16 repair not attempted.
8. **House normal request reproduced:** No new M16 execution. Historical M15 mock success is not counted as M16 proof.
9. **Fallback validation:** No new M16 execution. Historical M15 76-case evidence was recovered, not rerun.
10. **A-E tests:** All NOT_RUN.
11. **Test totals:** New 0 executed; existing 0 executed; container 0 executed. Two checkout failures are recovery failures, not test failures.
12. **Docker image:** None created. Host has no Docker. Existing images untouched. IMAGE_BUILD_READY=UNKNOWN.
13. **Actual CodaBench cause:** Cannot confirm. Its internal logs and output downloads remain unavailable. No attempt to access them.
14. **Independent forecast improvement:** No evidence; UNKNOWN. No score optimization/evaluation ran.
15. **Final recommendation:** Preserve/prefer the user's existing V51-final-submission.zip. Do not request, recreate, modify or submit it. M16 is not eligible based on this work.
16. **Unresolved risks:** Incomplete local frozen commit recovery; original proxy and HTTPS restrictions; response rejection and success-receipt ambiguities; no repaired container smoke, live House success or independent-quality evidence. Safe image/source receipt does not resolve historical baseline-score identity.
17. **Next action:** In a new recovery run, restore the exact remote commit and full tree using a self-contained authenticated clone or verified commit-object import rather than shared incomplete local alternates. Check exact source before editing. Then resume transport-only repair and staged tests from the frozen PRE scope. Never rerun completed historical evaluations unnecessarily.

## Recovered facts

Remote main: e1b5cf3b3a87966e902332ef3cc5c0ed2dbffee8.
Remote M15: e53d210ccd701e0b80bb6312b4cdebca99bc3c40.
Frozen source: 361018c14bab3cb7d8da101aa332066644921bac.
Frozen recursive tree: 3069 entries, not truncated; 2759 blobs. The local tree reconstruction matched the remote tree SHA, but the shared clone still could not resolve/check out the frozen commit. Read-only diagnosis afterwards reported that commit was not a valid object in the new clone.

The checkpoint uses GitHub's authenticated Git data API, with the remote frozen tree as the base. It does not promote files from the wrong local HEAD. Existing runtime blobs therefore remain unchanged on the new branch. CLI git transport was unavailable because the bridge required credentials; no token was requested or exposed.

Python 3.13.16 was installed successfully without modifying package Python requirements. This is environment preparation, not test success.

Official current docs support lowercase and uppercase proxy variables and preserving the injected HTTP/HTTPS endpoint scheme. The current reference implementation still only accepts lowercase http_proxy and HTTP. This mismatch was documented, not repaired by guesswork.

Existing POSTDEV report was absent from the M15 remote branch (404). The previously generated local report was recovered. Its prior classification REPRODUCIBLE_FALLBACK_RISK is unchanged. Existing image receipts and strict-current-contract receipt were fetched directly from M15 HEAD. The receipts describe mocks, not live House forecast quality.

No model parameter, prompt, loading, cap, weight, frozen manifest, existing image or protected branch was modified. Development score values were not used for selection or included in new public evaluation evidence.

## Exact stop event

Command (both attempts):

```text
git checkout -b track2/moonshot-16-house-transport-repair 361018c14bab3cb7d8da101aa332066644921bac
```

Exit 128, both times:

```text
fatal: unable to read tree (361018c14bab3cb7d8da101aa332066644921bac)
```

The second attempt followed remote blob and tree restoration. No third attempt was made. Under the user-specified long-work rule, implementation, tests and image work stopped. Evidence preservation continued only through the remote tree/commit API.

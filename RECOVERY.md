## Executive summary (read this first)

M16 is stopped at source recovery, not repaired. The remote branch starts from the correct frozen M15 commit. Reuse the recovered contract and receipt evidence; do not claim the old local HEAD is the frozen source.

# Recovery

Repository: psj216/track2-forecasting-public.
Branch: track2/moonshot-16-house-transport-repair.
Parent: 361018c14bab3cb7d8da101aa332066644921bac.
Remote tree: 9c7a78e3c23078bbe7f9c50f7eb50d65451869db.
Local shared clone stayed at e53d210ccd701e0b80bb6312b4cdebca99bc3c40. Do not edit or test that checkout as M16.

The exact checkout command failed twice with `fatal: unable to read tree`. The second failure followed a hash-verified tree restoration. Subsequent read-only diagnosis: `git cat-file -p 361018c14bab3cb7d8da101aa332066644921bac` did not resolve a valid commit in the shared clone. No third checkout attempt was made.

Continuation point for a new recovery run: materialize the exact remote frozen commit with a self-contained authenticated clone or a fully verified commit-and-tree import. Avoid relying on shared alternates from the incomplete donor clone. Validate source HEAD and entire tree before implementation. Do not change the specification to accommodate the recovery failure. Resume at PHASE 0 local source validation, then PHASE 2. Existing official source blob hashes and remote receipts are in MOONSHOT16-PROVENANCE.json.

Git CLI remote read failed for lack of bridge authentication; GitHub connector reads/writes worked. Preserve remote checkpoints through the authenticated Git data API if CLI authentication remains unavailable. Python 3.13.16 was installed successfully. Docker is unavailable in this host. No secret was requested or used.

No repaired container has been built. No runtime file or assertion has changed. No model evaluation was run. Prefer the existing V5.1 safe artifact until new transport, live House and independent performance evidence justifies another candidate.

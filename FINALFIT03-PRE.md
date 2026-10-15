## Executive summary (read this first)
FINAL-FIT-03 packages the previously verified monthly adapter into a standalone image. No forecasting architecture, parameters, protected source, registry publication or submission changes are authorized.

Parent: d611cff8c2a674f962cecb8cf52f9f8f8cc91c41.
Original safe source: 47194f28d5188b87cdca1d591d86b9eeda86f7cf; tree f2f9163372ab179c3e58a0dbac00acee119a41cf.
Candidate starting source: FINALFIT02 executable 9108ba25737dc88fcdeb478d45c749dddc2bbcb0, candidate_monthly.py plus exact official_horizons.py.
Base: docker.io/jotj216/track2-f4-approved@sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874.
Official Track: b9c663d239a0e6b86ebd3f3f2d5aead88516067d.
Official common v2.6.1 tag object 99fd66565303554fbf9063140b45287e11895b8f resolves to 03c50a0036aaf72675d353aef4c7c01ca86d1fcf. Contract 1.1.0; interface 2.0. The runtime inherits immutable original dependencies; current v2.6.1 validators are tested separately, not installed over original model dependencies.

Build: FROM exact original digest; bake wrapper/helper and an official forecast launcher; USER 1000; original /opt/qfbench2_track_forecasting untouched. No runtime Python mounts. Temporary local tag only. Save image archive and OCI build/source receipts in Actions artifacts; never registry push. Read-only input/root, tmpfs /tmp, network none. Each command <=540 seconds, each forecast <=90 seconds; measured wall time/output size and peak RSS where available.

Fixed matrix: reuse FF02 five daily cases spanning F1–F4, horizons [1,2,3,4], UST/EUR/JPY/BRL/INR; four normal monthly cases, missing/conflicting mapping and missing history. Original and standalone candidate execute identical fixture bytes; positives repeat twice. Compare daily parquet bytes/numeric/grid/draws/meta/rationale. Monthly changes only from explicit step mapping.

Additional monthly boundary tests: start/end date labels for one observation month, lagged anchor, nonconsecutive target months, irregular release-lag mapping, duplicate questions, malformed mapping, duplicate observations with and without mapping, original missing/conflict, multi-horizon determinism. Reuse the four fixed FF02 semantic assertions without weakening. Run unmodified current official helper tests, which cover multiple assets, heterogeneous anchors and output orders. Multiple-assets runtime/cadence cases are tested only where canonical asset/units permit construction; a supported helper case explicitly refused by the adapter remains a release coverage failure, never a successful forecast. Mixed cadence must refuse. Different per-asset monthly grids are a known candidate limitation, not a PASS.

PIT: synthetic historical numeric inputs contain no market outcomes. Official public monthly examples are ingestion tests only; observation labels do not prove vintage availability. No target fabrication. New practice is NOT FOUND as of the recorded check, not assumed published because of a planned date. No practice scoring without actual organizer inputs/targets; never OOS claims or tuning.

Pass criteria: standalone forecast command without mounted code; source hashes exact, interface/architecture/no VOLUME/non-root valid; unchanged daily parquet; four corrected monthly semantics; required grid/sidecars/finite/deterministic outputs and current schema validation. Failure handling has explicit refusal and does not disguise a missing forecast as success. Unsupported legal monthly grids or missing new Final schemas prevent global Final compatibility and eligibility.

Allowed patch: wrapper/entrypoint/schema/cadence guard only, with RED evidence before changes. No numeric sampling/model constants, scale/prompt/weight edits. Two failures of the same execution stage => STOP it; preserve logs. PRE -> BUILD -> TEST -> RESULT checkpoints with remote verification. Full Final runtime, independent alpha and registry availability cannot be inferred from these tests.

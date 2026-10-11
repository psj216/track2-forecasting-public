# V51_SAFE_DELIVERY_CANDIDATE — validation only

Exact image: `docker.io/jotj216/track2-f4-approved@sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874`
Source: `47194f28d5188b87cdca1d591d86b9eeda86f7cf`. Common 2.4.2. Python 3.13.15.
Validated on Actions run 38124740551, commit 66a07d47e4ad5a738f0b3ec613b8f8a4a1c8af5a.
Five fixtures, 18 runs, all schema/route gates passed. Four family representatives repeated three times with byte-identical parquet, metadata and rationale and bitwise-identical numeric arrays.
No model, forecast logic, score, tuning or submission was changed/performed.

This archive is validation evidence, not a CodaBench upload ZIP. `submission.json` intentionally lacks the verified team alias and sealed descriptor digest. Obtain the team's own derived identity through the authorized official packing flow later. No example identity or Team Key is included. The current image produces the required non-scored rationale sidecar.

Historical 0.9541 remains a reference only. The validated image is not proven to be that historical uploaded artifact.

## Exact raw-fixture command

```bash
docker pull docker.io/jotj216/track2-f4-approved@sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874
docker run --rm --network=none --read-only --tmpfs /tmp:rw,nosuid,nodev,size=64m --cpus=2 --memory=8g --pids-limit=256 -e FORECAST_MODE=text-first-v5.1 -v <ABSOLUTE_RAW_UNIT>:/input:ro -v <ABSOLUTE_WRITABLE_OUTPUT>:/output docker.io/jotj216/track2-f4-approved@sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874 forecast --panels /input --text /input/text --asof <EXACT_CARD_CUTOFF> --out /output/forecast.parquet
```

Official staged bundles use `--panels /input/panels/`; the validated public raw fixtures contain root parquet panels. Do not use fixture layout as a different official interface. No network/model endpoint is needed. The image default user is `runner` (non-root).

Security: full filesystem path inventory (16,650 members), bounded application/config content scan (58 files), no findings. Pattern inspection cannot establish absence of every encoded secret.
Resources: 2 CPU/8 GiB hard runtime limits; ~2s/unit; peak RSS not sampled. Inspect recorded output sizes and image manifest.

NEXT: NEW-MECHANISM-MOONSHOT-12; not executed here.

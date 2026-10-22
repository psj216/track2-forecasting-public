## Executive summary (read this first)

Prepared for separate authorization only. No registry push has occurred. Selected image must be the exact restored FF03 archive, not a rebuild. Local image ID is not a registry manifest digest; the latter is NULL until publication and anonymous verification.

## Immutable identity

Candidate executable source: c5b8bbbd6227888b7a3dc0bbd05dc414d2d7c3f6.
Local image ID: sha256:23f226ced859978d7a3f16a23c6d1515a1a3bdb14338297f4818d114bcfa2c1c.
Image archive SHA256: df232487177cb56cb0ae945b2613fbbebbb24eff702f21712662e589d04f636c.
Archived image origin: Actions 38798442114 / artifact 12003002655.
Base image reference: docker.io/jotj216/track2-f4-approved@sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874.
Build environment: inherited FF03 GitHub ubuntu-latest Docker build; final build receipt and image config retained in FINALFIT03-IMAGE-BUILD.json. This task restores that build without rebuilding. A byte-reproducible source rebuild is NOT_RUN/UNPROVEN, since frozen-base restoration differs from reproducing timestamped image layers and transitive dependency installs.
Dependency versions and internal source hashes: FINALFIT05-SOURCE-IDENTITY.json and backtesting/finalfit05/results/source-dependencies.json when collected. Verification receipts are linked in final release gate. Architecture linux/amd64, interface 2.0; use exact config/labels in the restored image.

## Proposed fresh repository/tag

Proposed public repository: docker.io/jotj216/track2-ff03-final.
Proposed new tag: ff03-c5b8bbbd-20261022. Repository creation/permissions/tag availability are NOT VERIFIED; do not overwrite an existing tag. No request to publish is implied by these commands. A public image exposes its contained source and layers.

## Commands only after separate authorization

```bash
# In an approved Docker release environment, authenticate archive before loading.
printf '%s  %s\n' df232487177cb56cb0ae945b2613fbbebbb24eff702f21712662e589d04f636c candidate-image.tar.gz | sha256sum -c -
gzip -dc candidate-image.tar.gz | docker load
docker image inspect sha256:23f226ced859978d7a3f16a23c6d1515a1a3bdb14338297f4818d114bcfa2c1c
docker tag sha256:23f226ced859978d7a3f16a23c6d1515a1a3bdb14338297f4818d114bcfa2c1c docker.io/jotj216/track2-ff03-final:ff03-c5b8bbbd-20261022
docker push docker.io/jotj216/track2-ff03-final:ff03-c5b8bbbd-20261022
# Capture the actual registry manifest digest from push/inspect. Never substitute local image ID.
docker buildx imagetools inspect docker.io/jotj216/track2-ff03-final:ff03-c5b8bbbd-20261022
# Replace MANIFEST_HEX below with the just-observed registry digest, on a fresh anonymous machine.
mkdir -p ./anonymous-docker-config
DOCKER_CONFIG="$PWD/anonymous-docker-config" docker pull --platform=linux/amd64 docker.io/jotj216/track2-ff03-final@sha256:MANIFEST_HEX
DOCKER_CONFIG="$PWD/anonymous-docker-config" docker image inspect docker.io/jotj216/track2-ff03-final@sha256:MANIFEST_HEX
```

Then compare pulled local image ID, production hashes, wrapper hashes, labels, architecture and VOLUME against frozen receipts; run a read-only/network-none forecast by digest. Keep digest pullable until results. Do not delete or change safe images. Rollback fallback reference remains the immutable Original above, with its monthly limitation explicitly preserved; FF03 archive remains the preferred monthly-capable recovery source.

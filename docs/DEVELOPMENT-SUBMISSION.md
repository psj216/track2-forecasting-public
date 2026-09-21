## Executive summary (read this first)

First submit **f4-only**, retaining the approved F4 x0.50 route and evidence prompt v1.0.3.
Upload **submission.zip**, not this repository, a Docker tarball, or forecast.parquet.
The confirmed image destination is **docker.io/jotj216/track2-f4-approved**.
The source repository is **psj216/track2-forecasting-public**; these are separate accounts.
The image must be anonymously pullable by its digest. A draft is not a completed submission.

Runtime uses qfbench2-common **v2.4.2**. Local packaging uses **v2.4.3**.
The official House disclosure checked on 2026-09-21 is
`nvidia/nemotron-3-super-120b-a12b`, revision/version `rl-030326-fp8`, cutoff `unpublished`.
Runtime still uses injected MODEL_NAME, never that disclosure string as a hardcoded request alias.
Public proxy calibration does not establish performance against this changed House model.

Sources: the supplied T2 submission-format document and
https://github.com/Agenthon-2026/Agenthon2026-public/blob/main/docs/HOUSE-MODEL.md .

## 1. Test and publish the image

The Submission Readiness workflow can publish the same image it tested, without a second build.
Create a Docker Hub personal access token for `jotj216` with Read & Write access, then put it in
the GitHub repository's **Settings → Secrets and variables → Actions → New repository secret**
as **DOCKERHUB_TOKEN**. No username secret is needed; the confirmed username is fixed in the workflow.
Do not share the token in chat. Keep the Docker Hub repository Public.

Publishing runs only for a push whose commit message starts `publish:`, or a manual dispatch
with `publish=true`, on `track2/submission-dev-v1` in the confirmed source repository. Ordinary
commits run validation only. If the credential preflight fails, add the secret and rerun the
failed job; the rerun retains the original publish request. No merge to main is needed for this
push-triggered route. The GitHub Run workflow button may not expose a workflow absent from main.

After publication, the run artifact contains `submission-draft.json`, `image-reference.txt` and
`source-commit.txt`. That Actions artifact ZIP is **not** the CodaBench submission ZIP. Extract it,
then follow step 3 to create the team-bound submission.zip with the official packer.

For a local Docker host, the equivalent target is:

```bash
docker build --platform linux/amd64 --build-arg FORECAST_MODE=f4-only \
  -t docker.io/jotj216/track2-f4-approved:dev-f4-v1 .
docker inspect -f '{{ index .Config.Labels "qfbench2.interface_version" }}' \
  docker.io/jotj216/track2-f4-approved:dev-f4-v1
docker push docker.io/jotj216/track2-f4-approved:dev-f4-v1
```

The label must print `2.0`. Record the registry manifest digest from push, **not** the local image
ID or a base-image digest. Check `qfbench2.forecast_mode` is `f4-only`.
Run the readiness workflow's offline F1-F4 gates before publishing. A successful mock House test
proves request compatibility, not connectivity to the private organizer route.

Verify anonymous access using a fresh empty Docker configuration and that exact digest:

```bash
ANON_DOCKER_CONFIG=$(mktemp -d)
docker --config "$ANON_DOCKER_CONFIG" pull \
  docker.io/jotj216/track2-f4-approved@sha256:ACTUAL_64_HEX_DIGEST
```

Do not log out or erase your usual Docker configuration. Keep the published digest available for
organizer reruns. A tag alone is never a valid submission reference.

## 2. Make the draft locally with Python 3.13+

```bash
python3.13 -m venv .venv-pack
.venv-pack/bin/pip install \
  "qfbench2-common @ git+https://github.com/Agenthon-2026/Agenthon2026-public.git@v2.4.3#subdirectory=common"
mkdir -p submission-artifacts
.venv-pack/bin/python scripts/prepare_dev_descriptor.py \
  --repository jotj216/track2-f4-approved \
  --digest sha256:ACTUAL_64_HEX_DIGEST \
  --out submission-artifacts/submission-draft.json
```

The script validates the image reference with the official parser and uses the repository's MIT
license (the Apache-2.0 in the supplied document is an example, not this repository's license).
The draft intentionally has no team_id or descriptor_digest. The official packer fills them;
inventing a team_id in the draft would make the packer refuse it.

## 3. Team claim and ZIP

Replace YOUR_TEAM_NUMBER with the number from agenthon.net. Run this in a real local terminal:

```bash
.venv-pack/bin/qfbench2 submission pack \
  --descriptor submission-artifacts/submission-draft.json \
  --team-number YOUR_TEAM_NUMBER \
  --out submission-artifacts/submission.zip
```

Enter the Team Key only at the hidden prompt. Do not put it in chat, command arguments, a prompt
to a model, a Docker image, a GitHub commit, or logs. The official tool derives the team alias,
seals the descriptor, and binds the schema-2.0 claim to the exact descriptor bytes.
It refuses overwriting an existing ZIP unless explicitly requested; do not use `--force` by default.

The ZIP must contain exactly these two top-level members:

- `submission.json`: sealed Development descriptor referencing your real image digest.
- `team-claim.json`: schema 2.0 proof, never the raw Team Key.

Development fields are fixed: competition_id `agenthon2026-forecasting-dev`, track `forecasting`,
phase `dev`, category `api`, image_access `public`, interface_version `2.0`.
Do not edit anything inside the ZIP after packing. Repack if any image or declaration changes.

## 4. What to upload

On the registered team's CodaBench account, open T2 → My Submissions → Development and upload
`submission-artifacts/submission.zip`. Do **not** choose Final. One account must represent the team.
Verify the current portal quota before uploading; held attempts also consume quota according to
the supplied instructions. A temporary Submitted state can mean organizer dispatch is pending.

Keep the source commit, immutable image reference, ZIP SHA-256 and submission ID together. Check
reasoning metadata after the run: a Numeric fallback score does not validate the House text route.

## Deliberate separation

- The official wrapper uses MODEL_ENDPOINT origin + `/v1/chat/completions`, MODEL_TOKEN and
  MODEL_NAME. Proxy environment variables remain untouched.
- Sampling defaults to the harness-injected QFBENCH_SEED, then zero if absent; an explicit
  `--seed` remains the local override. No numeric coefficients are changed.
- The public Nemotron calibration client, replay code, coefficients and prompt are unchanged.
- The image copies the forecasting runtime and license notices only, not backtesting or keys.
- The destination is confirmed. Actual publication requires a successful workflow push and
  anonymous digest pull; creating these files alone does not establish either.

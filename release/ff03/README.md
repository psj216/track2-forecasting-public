# FF03 Final release package (Team 318)

The exact FF03 Actions archive was restored and published without rebuilding. The public image is:

```text
ghcr.io/psj216/track2-forecasting-ff03@sha256:daddaf6222ebeea0c8951643db525eb73e7d856af9c5ac23b09772f3d1b8b81c
```

The digest above is the GHCR manifest digest, not the local Docker image ID. A fresh GitHub runner anonymously pulled every layer by this digest and compared its image ID against the archive. Evidence is in `PUBLICATION-RECEIPT.json`.

## Windows CMD: prepare locally

Download this directory's `submission.json` and `prepare-submission.cmd` into the same Windows folder. Python 3.13 and Git must be available through `py -3.13` and `git`. Open CMD in that folder and run:

```cmd
prepare-submission.cmd
```

The script creates an isolated Python 3.13 environment and installs the official `qfbench2-common` v2.6.1 toolkit if needed. The official packer prompts for your Team Key without echoing it, then writes `submission.zip` locally. The command carries only team number 318 and never transmits the key to GitHub. Do not type the Team Key in a command argument or commit it.

The checked-in `submission.json` is an input draft: `team_id` and `descriptor_digest` are null on purpose. Team ID is derived from the real key and number 318, then the toolkit seals the descriptor and places the finished `submission.json` and `team-claim.json` inside the local ZIP. The checked-in draft must not be uploaded directly. This release does not create a ZIP, read a Team Key, or submit to CodaBench.

If `py -3.13` is not available, install Python 3.13 first. The required pinned toolkit command is:

```cmd
py -3.13 -m pip install "qfbench2-common @ git+https://github.com/Agenthon-2026/Agenthon2026-public.git@v2.6.1#subdirectory=common"
```

Submit only on your verified Track 2 Final CodaBench page using the team's designated account. The public source does not contain your private competition page URL.

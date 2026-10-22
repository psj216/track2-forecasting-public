## Executive summary (read this first)

Official v2.6.1 fixture and model-free resealed control pass the actual toolkit parser. The real secret-free draft intentionally contains null team_id, image manifest digest and descriptor_digest; it is not a valid submission descriptor. No Team Key was accessed, no ZIP was packed, no upload occurred. The existing Windows ZIP was not opened or modified.

## Verified contract

Toolkit v2.6.1 = 03c50a0036aaf72675d353aef4c7c01ca86d1fcf. Required 12 fields: schema_version, interface_version, competition_id, team_id, track, phase, category, image, image_access, models, license, descriptor_digest. additionalProperties=false. image is {registry, repository, digest}, digest sha256:64hex of the registry manifest, not local image ID. Actual values: competition_id=agenthon2026-forecasting-final, phase=final, track=forecasting, interface_version=2.0, category=api, image_access=public, models=[] for this forecaster (no API or language-model weights), license=MIT for participant code.

Draft: backtesting/finalfit05/release/descriptor-draft.json. Required team_id is null and rejected by SubmissionDescriptor.from_mapping. A published official fixture and a model-free control resealed via seal_descriptor_digest pass. The synthetic control contains the organizer's example image digest and team ID; it is solely a parser control, never a deployable candidate. Docker parser precheck: Actions 39733727450, results/descriptor-precheck.json. No schema or assertion was weakened.

## Team claim and package

After separately authorized publication and digest verification, a designated team operator must use their real website team number and hidden Team Key prompt. Do not send the key to this chat. The toolkit derives team_id and writes a descriptor-bound proof. It writes submission.json and team-claim.json into the package; the key itself must never be included. Sealing uses toolkit canonical digest logic, not ad-hoc json.dumps hashing. An OS/package/parser pass does not prove registry pullability or competition eligibility.

Command is documented only; NOT EXECUTED:

```bash
qfbench2 submission pack --descriptor submission.json --team-number <WEBSITE_TEAM_NUMBER> --out submission.zip
```

Validate descriptor using SubmissionDescriptor.from_mapping and seal_descriptor_digest before authorized packing; inspect package names and descriptor binding only after packing is separately authorized. This task never calls pack, alias, or team-key APIs. Current v2.6.1 release includes native Windows packing support in its release commit; the starter-pack WSL-only prose is stale. WSL remains an available workflow, not a newly invented rule.

Upload destination: the registered team's Track 2 CodaBench competition, Final + Verification phase, from its one designated account. Current official SUBMISSION_CLI.md says the exact competition page link was issued to registered teams and is in participant announcements; it is not published in the public source reviewed here. Exact competition numeric URL remains UNKNOWN and must be confirmed by the team operator; no guessed URL and no existing ZIP/secret inspection. Public website similarly refers participants to logged-in competition links.

## Authorized-next-stage checklist

1. Obtain actual registry manifest digest from exact restored image publication and verify fresh anonymous pull.
2. Insert the verified image object, derive the real team identity locally and reseal using the official toolkit.
3. Separately authorize packing, create the two-file package locally, and verify binding with no secrets inside.
4. Upload on the verified Track 2 Final page before 2026-10-26 20:59 KST; at most two uploads on different UTC dates, later one final.
5. Preserve anonymous digest availability until results; retain the old Windows ZIP unchanged.

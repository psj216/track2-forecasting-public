## Executive summary (read this first)

M15 images inherit the unchanged verified V5.1 image. Only hand-authored numerical code, prompts, fixed economic loadings and a generic regime dictionary are added. No outcome ledger, historical donor future path, neural checkpoint or answer lookup is packaged.

|Artifact|Source/version|License/provenance|Cutoff treatment|
|---|---|---|---|
|V5.1 base|47194f28d5188b87cdca1d591d86b9eeda86f7cf; image sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874|Original repository MIT; dependency licenses retained in inherited image|Reads only provided panels/text; no added historical data|
|qfbench2-common|2.4.2, dfa92d242908bba4a448218b9c10ae391238d10d|Official toolkit, original license retained|Imported validators, no scoring reimplementation|
|M15 engine/config/prompts|Frozen PRE79915f93fb4de3463a7cd66cfc133e44658a4720; image source361018c14bab3cb7d8da101aa332066644921bac|Repository MIT|No fitted data or calibration. Fixed risk caps and generic economic semantics selected before any Development score|
|House transport|Literal _house_reply function from official baselines/reasoning_agent.py; hash in house_contract_audit.json|Official public reference; source notice retained|Only injected endpoint/token and authenticated proxy, no vendor fallback|
|House model|nvidia/nemotron-3-super-120b-a12b, rl-030326-fp8|Organizer-approved House API, unpublished training cutoff|Exact approved revision disclosure; no participant task-specific training|
|Provided panels/text|Organizer unit input at runtime|Upstream per-unit manifest licenses|Panel prefix <=asof; existing text publication reader filters before opening future documents|
|Generic semantic regime dictionary|Eight hand-authored factor states|MIT, no historical donor data|D is categorical interpretation followed by fixed factor shifts, not a historical path/answer library|

No market history or text corpus is copied into an image. Synthetic proxy scripts remain outside Docker build context; they are not a runtime model fallback. House absence or invalid replies preserve the exact V5.1 parquet. The declared submission license is MIT for participant software, not an assertion that every inherited dependency or model is MIT.

Historical research reports were audited to avoid simply renaming failed residual regressions, tiny expert routers, and numeric analog retrieval. They were not used to fit M15 parameters. No local CRPS optimizer or Development score was run.

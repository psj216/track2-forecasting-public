## Executive summary (read this first)

Official Track source: `f43655cdb624a3e5e5fed772ed9313ef57a54bc5`. Shared source: `6181b9c9f45c93ee526a6692406367a4042da7ad`. Fresh notices and current schemas were retrieved before PRE; no prior 24-hour estimate is retained.

- [Track update](https://github.com/Agenthon-2026/track2-forecasting-public/issues/4#issuecomment-6150556139) and [shared correction](https://github.com/Agenthon-2026/Agenthon2026-public/issues/2#issuecomment-6150553933): whole Final 12 hours / 43,200 seconds; each unit 1,800 seconds. Pull time counts; not-reached units fail.
- Deadline October 26, 2026, 20:59 KST; one team/track Final upload. Ranked as-of October 26; target October 27–30; horizons 1–4 business days; F1–F4 retained.
- Added UST 3M/6M/1Y and EM MXN/BRL/ZAR/KRW/INR; FX source ECB; some macro-release cards. This announcement does not publish exact card/panel schemas.
- linux/amd64, interface 2.0, anonymous pull, no Docker VOLUME, restricted networking. Unit resources 16 CPUs / 128 GiB; output 64 MiB per file and overall.

Current [monthly contract](https://github.com/Agenthon-2026/track2-forecasting-public/blob/f43655cdb624a3e5e5fed772ed9313ef57a54bc5/docs/MONTHLY-HORIZONS.md) resolves monthly steps from explicit observation periods and the last available panel observation. Horizon integers remain output keys. Missing/conflicting metadata is refused; dense-daily legacy inputs have a documented exception. Publication vintage is distinct from observation month.

[ECB reference rates](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html) use EUR as base and publish around 16:00 CET on working days excluding TARGET closures. No current market values were used. It is UNKNOWN whether organizer Final panels retain raw EUR quotes or transform them to card-specific quotes; existing H.10 USD levels cannot be spliced into raw ECB levels.

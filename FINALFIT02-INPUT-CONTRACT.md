## Executive summary (read this first)

The registered daily fixtures use only existing authored identifiers: UST_2Y/5Y/10Y/30Y, EUR, JPY, INR and BRL. Units are copied from the official source cards: yields in percent_per_annum, EUR in usd_per_eur, JPY in jpy_per_usd, INR/BRL in their native per-USD units. These are not claimed to be the new ECB Final representation.

Synthetic observations end 2018-09-14; monthly synthetic CPI observations end 2018-08-01. There is no realized target. Neutral synthetic text is dated 2018-09-14. The two synthetic monthly mappings [September–December] and [October–January] deliberately map the same h keys [1,2,3,4] to different required monthly steps. They are historical contract probes, not ranked cards or economic forecasts. GUIDs are unique v4, frozen for exact A/B reuse.

Original/candidate synthetic manifests are identical for every case. Current official CPI and NFP public examples are copied from source f43655c, including their published forecast_spec monthly mappings; their complete input hash inventories are in Docker receipts. Only participant inputs are mounted, never scoring targets. These historical examples may contain current-vintage revisions; availability timestamps were not established, so they are ingestion tests and are excluded from PIT/alpha claims. Date filtering is not vintage proof.

No canonical Final UST short-maturity IDs, ECB asset/quote mappings, MXN/ZAR/KRW panel IDs or GDP/jobless-claims target schemas were recovered. Those strata remain BLOCKED rather than inventing names. Existing daily level tests do not prove ECB log-return conventions or release-date/vintage handling.

The sentinel fixture deliberately adds a fabricated historical 2018-09-17 value. Its input cutoff is invalid by design. Identical forecast parquet to the clean case proves numeric filtering only. Missing history is a separate expected nonzero exit, not a fallback success.

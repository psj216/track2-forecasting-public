## Executive summary (read this first)

The minimal M16 repair accepts equal proxy aliases, rejects conflicting grants, and supports the injected HTTPS House origin through authenticated HTTP CONNECT with verified TLS. New call receipts distinguish local send, response, schema validation, numerical adjustment and exact fallback. Forecast semantics remain frozen. Staged validation is in progress.

# Repair

Runtime scope: official_transport.py, engine.py request only, cli.py receipts only. Configuration, prompts, context, caps, loading/transform functions, seeds and weights remain unchanged. Existing assertions are unchanged.

All nonempty HTTP/HTTPS proxy aliases must be byte-equal. Matching lowercase and uppercase aliases are accepted without changing the environment. A single HTTPS_PROXY alias is accepted as the same explicit audited route. Conflicts fail before socket creation. The variable HTTPS_PROXY does not imply an HTTPS URL: HTTP proxy URLs are supported; unsupported proxy URL schemes fail closed.

Only the injected endpoint origin is used. Paths/query/credentials/fragment and overrides are rejected. HTTP uses absolute-form POST through the proxy. HTTPS requires injected origin binding and uses CONNECT; the bearer token reaches the origin and proxy authorization stays on CONNECT. Default certificate and hostname verification remain enabled. No redirect, direct fallback, NO_PROXY bypass, vendor route or retry exists.

Transport receipts record request_attempted, request_sent (true/false/unknown), response_received, http_status, response_validated and safe failure_category. request_sent means request() completed locally, not independently observed remote admission. The CLI aggregates calls, adds adjustment_applied, fallback_used and location_shift_statistics, and keeps legacy flags for compatibility. A validated all-zero transform can have adjustment_applied=false without fallback. A second E-stage failure reverts the entire parquet to exact V5.1 bytes.

The production timeout remains 60 seconds. Timeout cases in the synthetic matrix inject a 0.1-second test deadline; this does not change runtime configuration. Live House and independent forecast quality remain UNKNOWN.

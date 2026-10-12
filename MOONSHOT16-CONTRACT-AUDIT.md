## Executive summary (read this first)

Current official documentation confirms proxy aliases and origin-based House calls. The current reference implementation is narrower than that documentation. These are recovered contract findings, not M16 runtime validation. Work stopped in PHASE 0.

# M16 Contract audit

Read from current official repositories through GitHub. Source identities are in MOONSHOT16-PROVENANCE.json.

| Contract item | Published requirement | Frozen M15 / current reference finding | M16 state |
|---|---|---|---|
| MODEL_ENDPOINT | Injected origin, scheme://host:port; preserve scheme | HTTP only; accepts origin or legacy /v1 | Not changed |
| Request | POST /v1/chat/completions | Correct HTTP absolute-form path through proxy | Not retested |
| MODEL_NAME | Injected runtime alias in model field | Present | Not retested |
| MODEL_TOKEN | Authorization: Bearer injected per-unit token | Present | No actual token used |
| Proxy | http_proxy / https_proxy and uppercase HTTP_PROXY / HTTPS_PROXY, authenticated | Frozen M15 checks only lowercase http_proxy | Repair pending |
| Proxy scheme | Published proxy URL with embedded login; no arbitrary direct egress | Reference only accepts http proxy | Exact supported proxy URL schemes require further contract handling before coding |
| Endpoint scheme | Preserve injected HTTP or HTTPS scheme | Current reference _house_reply rejects HTTPS | Documentation/reference mismatch recorded; HTTPS transport repair pending |
| Proxy auth | Credential from supplied proxy URL | Basic Proxy-Authorization | No secret used |
| Request allowance | 25 admitted requests per unit | A-D one, E two; no retries | Preserve |
| Output token ceiling | 4000 per call | Frozen 4000 | Preserve |
| Thinking | API option chat_template_kwargs.enable_thinking | Frozen false | Preserve |
| Timeout | Reference transport 60 seconds; not a promised service-latency SLA | Frozen 60 seconds | Preserve unless separately justified |
| Response | OpenAI-compatible choices/message/content | Frozen strict model-content JSON and closed schema | Do not relax assertions or parser for performance |
| Network | Audited model proxy only; no market/text fetch, external fallback, redirect or direct bypass | Frozen explicit proxy path | Repair must retain restrictions |
| Output | forecast.parquet, forecast_meta.json, nonblank forecast_rationale.md | Existing M15 CLI writes all three | No new validation |

Frozen reply rejection is deliberate: malformed JSON, duplicate model-content keys, nonfinite values, schema mismatch and truncation must not be treated as an applied forecast. Outer-response receipt and validation enhancements remain pending.

The documentation/reference mismatch is not asserted to have caused the CodaBench scores. Public practice data contain no sealed answers and are not independent forecast-quality evidence. No performance evaluation was authorized by these recovered facts.

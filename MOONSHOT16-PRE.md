## Executive summary (read this first)

Freeze a transport-only M16 repair starting at the exact M15 build commit. Recovery was stopped before implementation after two identical checkout failures. This checkpoint preserves evidence and does not certify a repaired candidate.

# MOONSHOT16 PRE

Branch: `track2/moonshot-16-house-transport-repair`.
Parent: `361018c14bab3cb7d8da101aa332066644921bac`.
Remote parent tree: `9c7a78e3c23078bbe7f9c50f7eb50d65451869db`.

Allowed runtime files: moonshot15_engine/official_transport.py, engine.py, cli.py, plus minimal tests. Keep prompts, configuration, location caps, factor loadings, scenario weights and all forecast transforms frozen. No Development score selection. No new forecasting model. No CodaBench submission. No Team Key. Do not request or recreate the user's V51-final-submission.zip.

Proposed stages, all pending after recovery: proxy/endpoint/receipt repair; separate unit/parser/fallback/integration/regression tests; comparison using fixed synthetic replies; container smoke when execution is available; Final gate with live and independent performance states UNKNOWN without actual evidence.

STOP rule exercised: identical frozen-source checkout command failed twice with exit 128. Further checkout, implementation and tests were stopped. GitHub ref and tree recovery evidence may still be preserved through the authenticated GitHub Git data API without running code from the unresolved local checkout.

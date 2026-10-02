## Executive summary (read this first)

CONTEXT-01 result: **NO**. Existing text: WEAK; semantic residual: NONE; routing: WEAK. Next: **TEXT-ROUTE-AUDIT-02**. One-shot readiness: **NO**. All evidence is RESEARCH_EXPOSED_CONTEXT_SIGNAL on previously exposed proxy cards.

Branch: track2/context-01-card-semantic-location. Parent RESULT: `79083c298f8dede7f9113dbf058f4f55c3dfad3d`. Verified PRE_RESULT_CONTEXT01_SHA: `a57c11701ae2b9383882673b14680e16c8d9cdea`. RESULT SHA is recorded in the external completion receipt to avoid a self-referential commit hash.

All24cards,63cells,13single/11multi,6cards per family. B_TEXT is the frozen V5.1 text-enabled baseline. Learned forecasts only add a bounded10SD shift, preserving every centered draw, pairing, tail and covariance. No card was excluded. No embedding checkpoint was available.

Current B_TEXT residual-location oracle composite: 0.489209; multi oracle: 0.893850; multi feasible location+joint oracle: 0.468813.
Existing full text/numeric fixed composite: 0.991379; pure text location/numeric: 0.985064; purelocation capture: 0.028502310647724124. Numeric-center delta correlation Pearson 0.5625030261348521, Spearman 0.3389087061646355, sign 0.07936507936507936, slope 28.546499380978958.

|Model|Composite|Marginal|Capture|R²|Spearman|Sign|Single|Multi|Wins/24|Gate|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
|B0|1.0000|1.0000|0.0000|-0.0763|NA|0.0000|1.0000|1.0000|0|BASELINE|
|B1|1.1595|1.0839|-0.3122|-0.4596|-0.0455|0.4127|0.8561|1.6593|9|NO|
|B2|1.0985|1.0188|-0.1929|-0.1950|-0.1479|0.3810|0.8502|1.4870|7|NO|
|B3|1.0957|1.0792|-0.1874|-0.1899|-0.0502|0.4127|0.9079|1.3683|9|NO|
|B4|1.2122|1.1817|-0.4155|-0.3813|-0.1427|0.3651|0.9763|1.5656|7|NO|
|B5|1.5237|1.3468|-1.0253|-0.8443|-0.2229|0.3968|1.3078|1.8254|8|NO|
|R0|1.0000|1.0000|0.0000|-0.0763|NA|0.0000|1.0000|1.0000|0|BASELINE|
|R1|1.0029|1.0242|-0.0058|-0.1191|0.1776|0.2698|0.9154|1.1173|5|NO|
|R2|0.9801|0.9799|0.0389|-0.0631|0.2358|0.3016|0.9440|1.0246|5|NO|
|R3|1.0958|1.0405|-0.1875|-0.2585|-0.2474|0.3968|0.9540|1.2907|10|NO|

Router coverage: 28/63cells,10/24cards. R1 picks the first available fixed-priority eligible source; R2 equally averages eligible sources; R3 is exactly50/50B5/R2. Source-family models use matured continuous-history labels, never card labels. Exact unmatched horizons are not snapped; transfer targets originally used a numeric baseline and receive no card calibration.

LOCO holds each complete card out. Alpha uses inner card-blocked delta MSE. Four family holdouts use18training/6testcards. Three chronological six-card test batches use5/11/18earlier matured training cards,189BDorigin embargo and no target overlap. All are exposed-sample diagnostics. All39candidate/control/numeric/text-location variants are fully rescored on each scored card.

F1 safety: {"B0": "NO_IMPROVEMENT", "B1": "NO_IMPROVEMENT", "B2": "NO_IMPROVEMENT", "B3": "NO_IMPROVEMENT", "B4": "NO_IMPROVEMENT", "B5": "NO_IMPROVEMENT", "R0": "NO_IMPROVEMENT", "R1": "NO_IMPROVEMENT", "R2": "NO_IMPROVEMENT", "R3": "NO_IMPROVEMENT"}.

|Model|F1 FHO|F2 FHO|F3 FHO|F4 FHO|Controls clear|Whole-card95 composite|Stratified95 composite|
|---|---:|---:|---:|---:|---|---|---|
|B0|1.0000|1.0000|1.0000|1.0000|NA|[1.0, 1.0]|[1.0, 1.0]|
|B1|1.0972|1.3643|2.1145|1.0326|False|[0.9045987461191793, 1.498945445215786]|[0.9872760652867344, 1.3737461726204425]|
|B2|1.0125|1.5244|1.4490|1.0302|False|[0.858920844041568, 1.437638547538897]|[0.9168225001184998, 1.3556934431198735]|
|B3|1.0293|1.2865|2.9166|0.7211|False|[0.8964841387443074, 1.3810133802184634]|[0.9235216778154951, 1.318484715287575]|
|B4|1.2381|1.3307|1.4503|0.9149|False|[0.9631867957151116, 1.544739791290496]|[1.003981852043082, 1.4821422133577813]|
|B5|2.5019|1.0458|2.3067|0.8782|False|[1.103948793018411, 2.144758180233776]|[1.1014777284054174, 2.1352749664459916]|
|R0|1.0000|1.0000|1.0000|1.0000|NA|[1.0, 1.0]|[1.0, 1.0]|
|R1|1.0959|0.9397|1.1183|0.8787|False|[0.8863004770056284, 1.1168341403493072]|[0.8939619997492874, 1.1139555388880173]|
|R2|1.0299|0.9441|1.0152|0.9349|False|[0.9107431498870378, 1.0362031063647272]|[0.9132843996822403, 1.0355921007213067]|
|R3|1.1632|0.9925|1.3062|0.9160|False|[0.923566823805953, 1.3142095694250278]|[0.9360268976396556, 1.300423562197219]|

Bootstrap:5000whole-card and5000six-per-family resamples, seed1903, including composite/marginal/single/multi intervals. These measure exposed-sample sensitivity and do not support formal generalization intervals. Every applicable A/B/Dcontrol, plus Cforrouting, must have candidate/control upper95<1 under both resampling schemes to clear specificity. No selection, weights or taxonomy changed after outcomes.

Negative controls preserve whole cards and target structure. E/F/G/Hguard tests pass. Structural B1 has identical permutation controls, hence cannot establish semantic specificity. Wrong-expert permutation may encounter unavailable sources, so this control also changes effective availability. No-route returns exactzero. Source timestamps and maturity are guarded.

Public artifacts contain aggregate metrics and hashes only. Card truth, predictions, per-card scores, expert pickles, annotation texts and all fit logs remain in the private recovery package. The report and code import the pinned common scorer; no scoring formula was reimplemented. Main was not changed.

Deterministic context features can miss relationships; weak or absent results here do not establish that context has no forecast information. Additional independent cards are required before any submission claim.

Detailed aggregates: backtesting/context01/results/{text_effect_summary,residual_oracle_summary,semantic_crossfit_summary,routed_summary,single_summary,multi_summary,negative_controls,bootstrap_summary,final_decision}.json and family/context/topic/horizon/group/chronology CSV tables.

Reporting and recovery audit: original repository tests520passed/2skipped, common250passed, new research22passed. After runtime rollback, the exact PRE and161saved private files were restored;168expert fits reused; the four early ephemeral folds were absent and rebuilt with identical frozen rules. Research tests22passed after dependency restoration. All620model/fold disjointness assertions and66card score records were verified, covering2574variant/card component rescores. The sole post-freeze code correction converted a NumPy vector to a list for the existing reporting aggregate adapter. No forecasts or acceptance rules changed.

Existing text shifts are sparse: 5/63nonzero median shifts on 4/24cards. The five active shifts all match residual direction, but this is a tiny descriptive subset. The all-cell7.94%sign metric counts58zero forecasts as incorrect against nonzero truth. Correlation and calibration on this exposed sample cannot justify amplifying the text signal. No amplitude was retuned.

|Scope|Perfect residual location|Perfect residual marginal|Feasible location+joint on multi subset|Subset cards|
|---|---:|---:|---:|---:|
|all|0.489209|0.350649|0.46881288710537716|11|
|single|0.293763|0.225152|NA|0|
|multi|0.893850|0.591901|0.46881288710537716|11|
|T2-F1|1.706269|0.808881|0.6307485836104305|5|
|T2-F2|0.417239|0.327971|NA|0|
|T2-F3|0.450869|0.433775|0.3661161802298227|6|
|T2-F4|0.178441|0.131372|NA|0|

F1 perfect median correction itself has composite1.706269despite marginal0.808881: pure location can harm path consistency even with hindsight. Learned models do not meet the predeclared location-signal/path-required flag because their F1marginal also fails to improve. Joint-oracle subset rows above contain only multi cards; the JSON additionally retains the full group aggregate with single-card location oracle substituted.

|Model|Multi marginal|Multi joint|Multi tail|Multi composite|Single wins/13|Multi wins/11|
|---|---:|---:|---:|---:|---:|---:|
|B0|1.000000|1.000000|1.000000|1.000000|0|0|
|B1|1.657197|1.374276|1.557032|1.659341|6|3|
|B2|1.448973|1.388730|1.365388|1.486981|6|1|
|B3|1.362243|1.264098|1.245054|1.368315|8|1|
|B4|1.517662|1.477843|1.381072|1.565626|7|0|
|B5|1.529594|1.472577|1.480192|1.825365|7|1|
|R0|1.000000|1.000000|1.000000|1.000000|0|0|
|R1|1.192862|0.930066|1.014549|1.117295|3|2|
|R2|1.032778|1.024588|0.996239|1.024592|3|2|
|R3|1.217709|1.238342|1.200453|1.290709|8|2|

R2has composite0.980115and capture3.893%, below the frozen3%composite and>5%capture requirements. Multi composite1.024592fails safety; only2/4family holdouts improve; every matched control does not clear both paired uncertainty tests. Its whole-card95composite interval[0.910743,1.036203]and stratified interval[0.913284,1.035592]cross1. Thus routing is only descriptively WEAK and CONTEXT-01 remains NO. The weaker accepted gates are not met by any semantic or routed model.

Public firewall: context/topic subgroups containing exactly one card retain only counts and an explicit suppression status. Their full diagnostics are preserved privately; otherwise they would reveal a per-card score. This is publication redaction, not exclusion from evaluation. All24cards and every frozen gate remain unchanged.

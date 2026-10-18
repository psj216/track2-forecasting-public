## Executive summary (read this first)

The exact safe image runs Numeric V3 over V2.1/V1 distributions, followed by the offline v5.1 F1/F4 text sleeve. F2/F3 text routes abstain; F3 numeric rank transport is still active on multiple assets. The opt-in House/family/scenario engines are imported but are not the selected text-first-v5.1 execution path. FF03 delegates daily requests directly to this CLI. No model code is modified here.

## Actual route and identity

Frozen source47194f28d5188b87cdca1d591d86b9eeda86f7cf contains26 production Python files. New ALPHA18 source hashing matches all26 files recorded inside the FF03 Docker image. A new Python3.13.16 host run matches four archived original Docker forecast parquets and numeric value bytes. This is a host bridge, not a new container run. NumPy2.1.3, pandas2.2.3, pyarrow18.1.0 and scipy1.18.1 match image math pins; research common2.6.1 differs from image2.4.2, disclosed despite four exact bridge outputs. Full dependency/image identity is not claimed for the host.

Read paths below relative to the frozen source, not the newer research package on the branch. CLI `_forecast_mode` selects text-first-v5.1, `_draw` calls `forecast_numeric_v3`, then `apply_text_first_v5(... interpreter_version='v5.1')`. In the exact CLI `reasoning_enabled` is false in this mode, so it makes no House call. `TEXT_INTEGRATION` parses but does not become a new model architecture. No old no-text distribution cache is loaded.

## Location and 1–4BD sampling

`numeric_v1.py::forecast_numeric` uses the last eligible level as anchor; return targets instead start at zero. Dated levels are differenced with long gaps excluded; assets align on nonmissing steps. Fewer than10 overlapping rows refuses. The daily route sets observation period1. V2.1's frequency conversion applies outside daily cadence; FF03's explicit monthly mapping replaces that conversion only for declared monthly level cards.

`_drift` computes daily movement as0.20 times the weighted mean of the latest20/60/120 changes and1260-step mean, weights0.45/0.30/0.15/0.10. Each daily drift is capped at0.75 times trailing252-step SD divided by sqrt(the maximum requested horizon). It is past movement, not an observed forward expectation. A path's location is the anchor plus cumulative drift and sampled centered increments. Thus expected drift scales approximately with h; finite samples and conditioned pools can shift the empirical mean as well. Asking for a different maximum horizon can alter the cap and draw construction, so deterministic repeat on one grid does not promise bitwise invariance across different grids. All ALPHA18 forecasts use the one fixed grid[1,2,3,4].

`numeric_v2.py` and `numeric_v21.py` select state_match_share0.75 over the V1 kernel. `_state_matched_starts` compares pre-block20/120 volatility ratio and20-step momentum to the current state; eligibility excludes the most recent120-step pool and requires mature blocks. It keeps the nearest20% with a minimum20 eligible starts. This already uses volatility, momentum and analog states; proposing those same inputs again is not new information.

## Dispersion and short blocks

`_regime_diagnostics` measures20/60/120/252-step volatility, momentum and recent/long correlation differences. Fragility combines volatility0.55, momentum0.25 and correlation0.20. Recent-pool probability is clip(0.70−0.25*fragility,0.30,0.85). Each centered sampled increment is multiplied by1+0.25*fragility. The remaining draws can choose historical state-matched blocks with effective share0.75*(1−fragility); otherwise they use full history. Full history is limited to2520 changes and recent history120.

`_sample_blocks` uses a five-step configured block truncated by the maximum requested horizon and available history. At maximum4, each world uses one contiguous four-step historical block, shared across assets and intermediate horizons. Recent/full/matched pool-specific historical means are subtracted before drift is added. The law is an empirical mixture, not a Gaussian with exactly sqrt(h) SD. Autocorrelation, state selection and text sleeves can change that scaling. ALPHA18 uses SD*sqrt(h) solely as a fixed diagnostic unit; it does not modify the forecast or treat this as the true conditional variance.

An input ending before the card as-of is an additional limitation: the original daily sampler advances h changes from the last observed anchor, without explicitly simulating missing steps between that anchor and as-of. R17 vintages already have stale input dates; ALPHA18 records input-age business days and keeps those diagnostics separate from authored fresh-close cards. Apparent underdispersion under that input clock cannot automatically justify modifying fresh-close Final forecasts.

## Tail and text

The numeric tails are inherited empirical extreme blocks, mixed from recent/full/matched history and widened by fragility. There is no newly fitted extreme-value tail model. The same world supplies all horizons; no independent per-cell tail splice occurs.

`text_first_v5.py::apply_text_first_v5` leaves F2/F3 exactly unchanged at the text stage. For F1, `text_interpreter_v51.py::f1_document_delta` compares comparable dated statements and policy-language changes. For F4, `f4_current_event` distinguishes current realizations, forward scheduling/risks, historical narratives and hypotheticals, with conflict/unsupported exposure abstention. The corpus reader enforces the as-of date. These are offline deterministic interpreters, not live LLM predictions.

An admitted F1/F4 event uses pre-asof historical paths aligned with asset-direction signs and quote convention. Eligible paths lie above the75th percentile for F1 or90th for F4 of a direction-standardized terminal displacement, with minimum history180, at least10 eligible windows and3 separated episodes. A deterministic subset of draws is replaced:0.12*event strength for F1,0.18*strength for F4. This can alter location, tails and dependence together. It is not a pure mean shift. Strong past directional paths are not proof the next event follows their direction. Actual activation is read from `forecast_adjustment_applied` and the integration receipt, not inferred from a generic reasoning flag.

## Joint dependence and coherence

`numeric_v3.py` applies only to multi-asset F3. Its target correlation blends recent60 and long1260 changes, with recent weight clip(0.65−0.50*fragility,0.15,0.75), eigenvalue floor1e-6 and no identity shrinkage in selected V3. Strength0.25 blends an inverse-square-root source / square-root target correlation transport into standardized scores. Each asset/horizon reassigns its original sorted values by score rank. Sorted marginal values are exactly preserved, so marginal CRPS and univariate tail pinball cannot change solely from this transport. Variogram can change. Reordering separately by horizon does not establish a physically unique path interpolation between output endpoints. It does not prove that a more elaborate temporal copula has predictive skill.

`family_pipeline.py`, `regime_router.py`, `scenario_integration.py` provide other opt-in heads and strict route/schema/mixture gates. They are not substituted for the selected text-first path. V12/V13 and prior temporal dependence work already explored state/covariance/copula constructions; an unvalidated rank rearrangement would repeat that axis without new information.

## Official metric and interpretive limits

ALPHA18 imports `qfbench2_common.scoring.crps` from authenticated v2.6.1 and `_composite`/tail functions from official Track commit24582e957b0cbb9ea7268bec9636188a0e2c21fa under a separate package alias. It does not call the research branch's older scorer by accident. Marginal is the fair ensemble CRPS; joint is the ordered-pair variogram with power0.5; tail is mean pinball at.01/.05/.95/.99. Variogram is structurally zero on a true single-cell grid, where weights become5/7 and2/7; an energy score would not justify that substitution.

Official weighting0.5/0.3/0.2 follows per-card M0 expected-error normalization and the sealed roster. ALPHA18 has neither authoritative ranked M0 scales nor the Final roster. It reports raw components and explicitly labeled pre-asof-SD diagnostics, not an official composite. Component raw magnitudes have incompatible units and dimensions; their magnitudes cannot identify the largest contributor to official loss. Historical0.9541 identity remains UNKNOWN, and no number is compared with it.

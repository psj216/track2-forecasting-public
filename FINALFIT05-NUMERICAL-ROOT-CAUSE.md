## Executive summary (read this first)

The representative FF04 RED is reproduced exactly across AMD EPYC 7763 and EPYC 9V74: 13/2000 values differ, max 0.06308603200308704 percentage points. Both unchanged images match within each environment. NumPy SIMD-dispatched default argsort tie ordering is demonstrated; floating-point distance changes also occur but did not alter stable order in these probes. No universal cause or CPU coverage claim.

## Controlled evidence

Run 39732916469, source 258a09ef9978344937cca31d8b1832db6e210ac1. Two independent jobs restore archive df232487177cb56cb0ae945b2613fbbebbb24eff702f21712662e589d04f636c and pull Original by immutable digest. Input hashes equal; seed 17, 1000 draws, Python 3.13.15, NumPy 2.1.3, pandas 2.2.3. All ten standalone forecasts and all ten official gate/raw-score invocations pass. Four diagnostic runs per runner produce forecast parquet hashes identical to their standalone counterparts. Diagnostic tracing is not in the candidate image.

7763 default versus disabled AVX512F/AVX2/FMA3: distance arrays bit-identical; 198 exact tie groups; 265 full default-sort positions and 39 selected-pool positions differ. Stable full order identical. Eight draw values change.

9V74 default versus disabled: one distance changes by 1.1102230246251565e-16; full default sort changes 261 positions; selected pool changes 48 positions; stable full order identical. Fifteen draw values change. One feature matrix hash also changes. This is evidence of floating-point dispatch effects in addition to default tie sorting, not proof that every future near tie is safe.

Random pool-draw sequences, intermediate RNG states and final RNG states are identical across CPU-feature toggles on each runner. Selected bootstrap starts change 8 and 20 times respectively. Therefore RNG consumption order is not the observed cause. The same fixed random pool index selects another historical block when tied candidates reorder. Pool membership stays the same. Package versions are the same, so version mismatch is not needed to explain this RED. BLAS-specific causation was not isolated; the demonstrated control is NumPy CPU-feature dispatch, including its sorting path.

## Impact

Across runners: 13/2000 cells; mean changes -0.0000420574 and -0.0000946290 percentage points at horizons 1 and 3. Medians and 1/5/50/95/99% quantiles unchanged. Empirical Wasserstein-1 (mean sorted absolute sample difference) is 0.187% and 0.297% of baseline IQR. Paired RMS is 4.176% and 5.599% of IQR. Pairwise differences are not identical to marginal distribution distortion. On 7763 the toggle raw composite changes -0.04925%; on 9V74 +0.01548%. Across the two default-dispatch runners, raw composite relative change is -0.06472%. The scores are exposed Practice diagnostics, not normalized ranking scores or independent alpha evidence. No method was selected for improving these scores.

## Analysis infrastructure failure and recovery

Both jobs reached the final auxiliary analysis write, then failed with PermissionError for /results/analysis.json: parent output directory belonged to the host. Forecast and trace files were already retained in artifacts 12405747784 and 12406420225. No forecast was rerun. The failed Docker analysis step was stopped; its recorded files were analyzed offline using pyarrow 18.1.0 and a path-parameterized copy of the same analysis script. Assertions were not weakened. The Actions workflow conclusion is FAILURE and is not represented as green. Raw trace/forecast evidence remains in those artifacts; only summaries, commands and hashes are committed.

# 2025 extension and absolute-distance checks

## 2025 outcomes

The new extend-cdl-2025.yml workflow builds the same58 retained-hub exclusive polygons, validates one2025 hub-band request, then extracts all348 hub-band cells for2025 in174 jobs (two adjacent rings per job), with at most3 concurrent requests/jobs. Existing2013–2024 outputs are preserved;2025 appends only after completeness, uniqueness and composition-count consistency checks pass. Job artifacts preserve completed tasks even if another fails. Official CDL WCS is requested at30m, with verified raster resolution, global30m-snapped tile bounds, polygon masking and temporary rasters. Persistent request failures raise errors; they cannot silently become zero counts. True empty exclusive polygons keep zero-area records and missing shares.

The endpoint smoke check must succeed before the full matrix launches. An available national2025 download does not prove that this WCS endpoint serves2025. If unsupported, the smoke gate blocks rather than launching many failing requests; the national30m release is the documented fallback. A green smoke check is not completion of348 cells.

Legacy extractor07 had a persistent-request-failure branch that could record zero for a fragment. New22 removes it. This does not prove that historical outputs contain such errors; historical coverage should be reviewed separately. The new pipeline is not allowed to silently recreate that behavior.

USDA2025 release: February27,2026. Native10m and nearest-neighbor resampled30m downloads: https://data.nass.usda.gov/Research_and_Science/Cropland/Release/ . Ancillary noncrop sources changed; forest/noncrop methodological comparisons require care.

## 2025 treatment projection

code23 uses2024 capacity as the2025 pre-plant capacity proxy and applies observed approval dates throughMay1,2025. It does not use2025 capacity. The separate lcfs_2025_preplant_projection.csv is explicitly marked as incomplete approval-history coverage. It is not yet merged into regression treatment panels. Among currently mapped plants, the source-baseline projected total is5108MGY; late2024 approvals can become eligible for2025 even though they were excluded byMay1,2024. New2025 approvals are not yet included. Company-source capacity disagreements remain separate documented sensitivities.

The previous-year rule means2025 capacity first enters2026 exposure, but known2025 approvals can affect2025 eligibility for pre-existing capacity. Therefore approval-history updates still matter even without2025 capacity data. Soybean outcomes for2025 are not committed until the extraction finishes.

## Absolute weights

code21 estimates fixed absolute road-distance exponential decay at50,150,300 miles; absolute hard cutoffs100,250,500,1000 miles; and sum-to-one150-mile exponential allocation. These absolute cutoffs differ from earlier excess-distance thresholds. Absolute exponential decay has w=exp(-distance/scale), so a very distant nearest crusher receives less than1. Sum-to-one absolute exponential weights are algebraically identical to sum-to-one relative exponential weights, because the refinery-specific normalization constant cancels. They are an allocation interpretation, not independent robustness evidence.

Results use2014–2024, source-baseline capacity, all six bands, crusher/year FE, single current/lag1/lag2/lag3 models, jointcurrent+lags1–2, and crusher trends. All384 coefficients are reported. No2025 result is included. New results should not be compared on raw coefficient scale without noting exposure normalization.

Positive significant single-dose estimates occur only with the broad1000-mile hard cutoff:25–50 lag1 +0.0824 pp (p0.0420);50–75 current +0.0623 (p0.0279),lag1 +0.1041 (p0.0042),lag2 +0.1275 (p0.0058). Unitspp/100MGY weighted exposure. These are unadjusted exploratory p-values among many comparisons. The1000-mile rule counts every eligible refinery within that radius at full weight; it should not be selected as preferred solely because its coefficient is positive. Exponential and narrower-cutoff results do not show the same positive-significant single-dose pattern.

Artifacts: output/tables/absolute_distance_robustness.csv; code21 regenerates full weight/exposure panels. Code23 regenerates the provisional2025 treatment input. The capacity-history audit and company-source alternative are in exposure-identification-audit.md and code20.

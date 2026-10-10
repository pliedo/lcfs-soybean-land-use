# Distance-weighted LCFS exposure: preliminary estimates

## Dose and timing

For crusher h in growing-season year t, D_ht = sum_r w_rh C_rt / 100, where C_rt is the physical refinery's planting-aligned eligible capacity in million gallons/year. First observed soybean-pathway approval must precede or equal May 1; previous-year capacity is used as the pre-plant proxy. Retired pathways retain their historical onset, rather than imply plant closure. Aliases are consolidated before summing. Multiple refineries entering in one year contribute additively, each at its own fixed distance weight. Capacity is a policy-exposure proxy, not observed purchases or production.

Baseline weights: w_rh = exp(-(d_rh - min_h d_rh)/(150 miles)). Original road distances are treated as kilometres after geographic checks. Each refinery's closest retained crusher gets weight 1. Weights do not sum to 1, so aggregate exposure across crushers is not national refinery capacity. A sum-to-one allocation is a separate robustness specification. Distances use the reviewed physical-plant crosswalk; original Sinclair geography is retained as a sensitivity case. See physical-plant-resolution.md for unresolved location and capacity discrepancies.

The annual CDL measures crops grown in that same year. There is no mechanical requirement to shift outcomes forward one year. Additional exposure lags 1, 2 and 3, and joint lag models, test delayed responses rather than correct a raster-release lag.

## Outcomes and estimator

Six distinct exclusive bands, 0–25 through 125–150 miles. No inner-control/outer-treatment assignment. Primary outcome is soybean pixels / all valid land pixels; cropland denominator is a sensitivity case. Estimates use 2014–2024, equal crusher-year weights, crusher and year fixed effects, and crusher-clustered standard errors with finite-sample adjustment and t(G-1) intervals. Only retained elevator sites enter exposure. Zero-area polygons have undefined shares and are excluded, not coded zero. Observed hub counts are 57, 57, 54, 49, 41 and 34 by band, although geometry/exposure includes 58 hubs.

The coefficient is percentage points of soybean share per 100 million gal/year of weighted eligible capacity. It is a within-crusher association after common year effects. Linear TWFE is exploratory; continuous-treatment DiD still requires parallel-trends assumptions and additional restrictions for causal dose-response interpretations. Different refineries and years change exposure, not a single binary adoption event. Long-range decay gives nearly every crusher positive exposure once capacity is eligible; low exposure is not untreated.

## Baseline results

| Band (miles) | Coefficient (pp/100 MGY) | 95% interval | p-value | Hubs |
|---|---:|---|---:|---:|
| 0–25 | -0.0769 | [-0.1710, 0.0173] | 0.107 | 57 |
| 25–50 | -0.0952 | [-0.1594, -0.0310] | 0.004 | 57 |
| 50–75 | -0.0921 | [-0.1520, -0.0322] | 0.003 | 54 |
| 75–100 | -0.0599 | [-0.1233, 0.0035] | 0.064 | 49 |
| 100–125 | -0.0553 | [-0.1422, 0.0317] | 0.206 | 41 |
| 125–150 | -0.0612 | [-0.1455, 0.0232] | 0.150 | 34 |

These estimates do not support an expansion conclusion. All 10 baseline distance-weight rules produce negative current-dose point estimates in all six bands, although significance and magnitude vary. Excluding 2019 and 2021 leaves the two middle-band negative associations; replacing the denominator with cropland produces larger negative coefficients. Capacity-source and reviewed/original geography changes preserve the negative baseline signs.

Crucially, crusher-specific linear trends make the baseline coefficient statistically indistinguishable from zero in every band. An extra one-year lag is insignificant in five bands; the 125–150 mile band remains negative (about -0.153 pp/100 MGY, p=0.012). Joint distributed-lag estimates have mixed signs and should not be read as a stable expansion effect. Excluding 2024 makes negative current-dose coefficients larger in magnitude; estimates are sensitive to timing and trend specification. Multiple tests and spatial/shared refinery shocks require more careful inference than the provisional crusher-clustered intervals.

## Robustness and visualization

code/17_estimate_distance_dose.py produces 1,680 coefficient rows covering four capacity/site scenarios, three distance measures, ten weights and additional timing/outcome/trend specifications. Weight rules include inverse and inverse-squared relative distance; exponential scales 50, 150 and 300 miles; nearest-only; excess-distance cutoffs 100, 250 and 500 miles; and exponential weights normalized to sum to 1. Excess cutoffs are measured beyond the refinery's nearest crusher distance, not absolute distance from the refinery. Tied nearest-only weights are split across tied hubs.

code/18_visualize_continuous_exposure.py creates fixed low/medium/high exposure groups from 2024 baseline exposure, keeping hub membership identical across years and bands. These descriptive terciles are not causal treatment/control groups or a parallel-trends test. Group soybean shares are equal-hub averages; each hub share is soy pixels / valid land pixels. Multiple refineries add to exposure, never add or duplicate the soybean numerator or denominator. Pixel-pooled shares would instead sum numerator and denominator across hubs and answer a different, area-weighted question.

Baseline public panels: data/clean/crusher_year_lcfs_exposure_baseline.csv (100 MGY units, one column per weight) and refinery_crusher_weights_baseline.csv. Full scenario exposure and long-form weights are reproducibly generated by code17. All coefficients are in output/tables/continuous_dose_twfe_robustness.csv. PNG and vector PDF plots are under output/figures/results.

## Validation and remaining identification work

All six baseline coefficients and clustered standard errors independently matched full dummy-variable OLS and the full sandwich covariance to 1e-10. Nearest-normalized maxima, sum-to-one rules, and unique crusher-year joins were checked. Original ungrouped lags could cross crusher boundaries; all new lags are grouped by scenario, distance measure, weight and crusher.

Next identification work should use predetermined geographic weights, examine pre-exposure trends and weather/region shocks, assess dose validity and approval-history completeness, and improve inference for spatially correlated/shared refinery shocks. The ongoing forest classification audit remains relevant; omitting suspected break years does not establish that the outcome is free of measurement changes.

Sources: https://www.nber.org/papers/w32117 (continuous DiD identification and TWFE cautions); https://data.nass.usda.gov/Research_and_Science/Cropland/sarsfaqs2.php (annual CDL). Raw workbooks, distance matrix and physical-plant provenance are documented elsewhere in doc/.

Reproduce: install numpy pandas scipy matplotlib openpyxl; run code12, code14, code17, then code18 from the repository. No CDL downloads are needed for these regressions.

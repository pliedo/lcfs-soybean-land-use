# Joint anticipation, current and delayed exposure model

Y(h,r,t)=crusher–ring FE + ring–year FE + gamma(r,2)E(h,t+2) + gamma(r,1)E(h,t+1) + beta(r,0)E(h,t) + beta(r,1)E(h,t-1) + beta(r,2)E(h,t-2) + error. Outcome is non-water soybean share (percentage points) or direct soybean acres. Exposure is planting-aligned eligible capacity allocated by the transport-cost weights, divided by100mgy. This is a conditional capacity-stock regression, not an approval-event study. May1 eligibility and previous-year capacity are already built into exposure. Satellite publication does not add an outcome lag.

Eight existing weights and both physical-onset/crosswalk scenarios are retained. All five timing regressions (current-only, lag1-only, lag2-only, distributed0–2, full lead/lag) use the same 2016–2023 sample: two lags exclude2014–15 and two leads exclude2024–25 outcomes. Future exposures up to2025 use the provisional2025 capacity construction. There are2,336 observations and57 crusher clusters in the share model. Six ring responses are estimated jointly. The end-year restriction matters because much recent capacity growth is outside the outcome sample; do not attribute changes from previous estimates solely to adding leads.

No-anticipation tests jointly set lead1/lead2 coefficients to zero for the first two rings, first three rings and all six rings, all prespecified footprints. Delayed-response tests set lag1/lag2 coefficients to zero; post-eligibility tests set current/lag1/lag2 coefficients to zero. Covariance is clustered by crusher; all results and nominal p-values are exported without multiple-testing adjustment. Failure to reject a lead test is not proof of no anticipation or causal identification. Joint rejection of post coefficients means at least one differs from zero, not that their sum is positive significant.

## Focal normalized inverse-square share coefficients

Units are percentage points per100mgy weighted crusher exposure, conditional on the other timing terms.

| Term | 0–25 | 25–50 | 50–75 |
|---|---:|---:|---:|
| Lead2 | -.1503 | -.0457 | -.4536 |
| Lead1 | -.1853 | -.3422 | -.3689 |
| Current | -.4438 | -.5465 | -.2827 |
| Lag1 | .6112 | .7651 | .8705 |
| Lag2 | .8105 | .5860 | 1.5466 |

All three lag1 coefficients have p<.01. The lag2 third-ring coefficient has p=.0738; other current/lead/lag2 coefficients in these rings do not reach5%. Joint first-three-ring lead test p=.4174; delayed-coefficient test p=.00789; post-eligibility-coefficient test p=.01023. All-six-ring lead test p=.02562, so the no-anticipation conclusion cannot be generalized across the full150-mile footprint.

## Average100mgy addition, cumulative0–75-mile share contributions

Equal mean across16 refinery locations, using fixed2024 non-water polygon areas for acreage conversion. Individual timing contributions are not net effects at a given time after a persistent capacity increase; future, current and past exposure paths must be combined. All weighted exposures are potentially endogenous; weights are not actual procurement shares.

| Component | Share pp | Implied acres | 95% acre interval | p |
|---|---:|---:|---|---:|
| Lead2 | -.004270 | -14,352 | [-52,078,23,374] | .4492 |
| Lead1 | -.005803 | -19,505 | [-48,298,9,287] | .1802 |
| Current | -.007399 | -24,868 | [-70,252,20,517] | .2771 |
| Lag1 | .013956 | 46,907 | [18,045,75,768] | .00192 |
| Lag2 | .018516 | 62,234 | [-25,100,149,569] | .1590 |
| Current+lag1+lag2 | .025073 | 84,273 | [-27,902,196,449] | .1380 |

The direct-acreage model lag1 contribution is+32,008 [11,712,52,303], p=.00255; its current+lag1+lag2 sum is+38,979 [-88,173,166,130], p=.5416. Thus there is a conditional first-lag signal in both outcomes, but no precise positive overall post sum. Correlated stock exposures complicate individual timing interpretation.

## Weighting comparison

Normalized exponential first-three-ring lead test p=.3439; delayed-response test p=.0892. Its cumulative lag1 share contribution is+.030417pp (+102,234 implied acres), p=.0158, but total post sum p=.3434. Nearest-eligible first-three-ring lead test rejects, p=.01246, even though aggregated lead contributions can cancel; lag1 share contribution+.005627pp (+18,912 acres), p=.00106, total post sum p=.4317. No weighting rule should be selected solely for a favorable lead test or positive coefficient.

On the identical2016–2023 sample, simpler distributed0–2 share models produce imprecise total predictions under these three rules: normalized inverse-square+23,889 acres p=.2895; normalized exponential+88,433 p=.3910; nearest+3,786 p=.5691. The earlier2014–2025 distributed results are separate sample estimates, not a direct comparison.

Reproduce with code/51_estimate_joint_timing.py and code/52_plot_joint_timing.py. All2,112 coefficient rows are in nonwater_timing_coefficients.csv.gz, all2,816 location/average contrasts in nonwater_timing_contrasts.csv.gz, with readable average summaries and footprint-specific joint tests. Focal coefficients and16:9 PNG/PDF figures are also committed. No rasters are downloaded or original outcome files altered.

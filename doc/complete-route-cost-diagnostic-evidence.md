# Complete route-cost diagnostic evidence

This report summarizes a prespecified diagnostic grid; it does not select estimates for their sign or significance. Route weights measure potential exposure, not observed procurement. Nominal p-values are unadjusted and face extensive multiple testing.

## Baseline direction across route proxies and weights

Each cell summarizes baseline estimates across three route proxies and three weighting rules. Positive share is descriptive consistency, not a posterior probability. Coefficients remain in each outcome's native reported scale.

| outcome            |   ring | specification   |   models |   median_beta |   positive_share |   nominal_positive |   nominal_negative |   median_within_sd_effect |
|:-------------------|-------:|:----------------|---------:|--------------:|-----------------:|-------------------:|-------------------:|--------------------------:|
| soy_share_all_land |      1 | current         |        9 |       0.0292  |            1     |                  0 |                  0 |                   0.0385  |
| soy_share_all_land |      1 | lag1            |        9 |       0.0967  |            1     |                  2 |                  0 |                   0.0752  |
| soy_share_all_land |      2 | current         |        9 |       0.0404  |            0.889 |                  0 |                  0 |                   0.0306  |
| soy_share_all_land |      2 | lag1            |        9 |       0.129   |            1     |                  3 |                  0 |                   0.0763  |
| soy_share_all_land |      3 | current         |        9 |       0.0173  |            0.778 |                  0 |                  0 |                   0.0105  |
| soy_share_all_land |      3 | lag1            |        9 |       0.0886  |            1     |                  0 |                  0 |                   0.0553  |
| soy_share_all_land |      4 | current         |        9 |      -0.02    |            0.222 |                  0 |                  1 |                  -0.0186  |
| soy_share_all_land |      4 | lag1            |        9 |       0.0274  |            0.889 |                  0 |                  1 |                   0.0123  |
| soy_share_all_land |      5 | current         |        9 |      -0.138   |            0     |                  0 |                  7 |                  -0.123   |
| soy_share_all_land |      5 | lag1            |        9 |      -0.139   |            0     |                  0 |                  7 |                  -0.106   |
| soy_share_all_land |      6 | current         |        9 |      -0.144   |            0     |                  0 |                  6 |                  -0.144   |
| soy_share_all_land |      6 | lag1            |        9 |      -0.2     |            0     |                  0 |                  7 |                  -0.158   |
| soy_share_cropland |      1 | current         |        9 |      -0.00799 |            0.444 |                  0 |                  0 |                  -0.00933 |
| soy_share_cropland |      1 | lag1            |        9 |       0.0269  |            0.667 |                  0 |                  0 |                   0.0252  |
| soy_share_cropland |      2 | current         |        9 |      -0.344   |            0     |                  0 |                  5 |                  -0.195   |
| soy_share_cropland |      2 | lag1            |        9 |      -0.353   |            0     |                  0 |                  3 |                  -0.15    |
| soy_share_cropland |      3 | current         |        9 |      -0.547   |            0     |                  0 |                  8 |                  -0.501   |
| soy_share_cropland |      3 | lag1            |        9 |      -0.689   |            0     |                  0 |                  6 |                  -0.451   |
| soy_share_cropland |      4 | current         |        9 |      -0.641   |            0     |                  0 |                  7 |                  -0.754   |
| soy_share_cropland |      4 | lag1            |        9 |      -0.836   |            0     |                  0 |                  6 |                  -0.648   |
| soy_share_cropland |      5 | current         |        9 |      -1.03    |            0     |                  0 |                  9 |                  -1.03    |
| soy_share_cropland |      5 | lag1            |        9 |      -1.22    |            0     |                  0 |                  9 |                  -0.996   |
| soy_share_cropland |      6 | current         |        9 |      -0.91    |            0     |                  0 |                  9 |                  -1.01    |
| soy_share_cropland |      6 | lag1            |        9 |      -1.34    |            0     |                  0 |                  9 |                  -1.2     |

## Sensitivity stability

Sign reversals compare each sensitivity estimate with its exactly matched baseline. They diagnose fragility; they do not determine which estimate is correct.

| sensitivity                                 |   models |   matched |   sign_reversals |   sign_reversal_share |
|:--------------------------------------------|---------:|----------:|-----------------:|----------------------:|
| 2014_2018                                   |      432 |       432 |              156 |                0.361  |
| 2014_2024                                   |      432 |       432 |               88 |                0.204  |
| 2016_2025                                   |      432 |       432 |               24 |                0.0556 |
| 2020_2025                                   |      432 |       432 |               68 |                0.157  |
| anticipation_diagnostic                     |      864 |         0 |                0 |                0      |
| exclude2019_2021_classification_sensitivity |      432 |       432 |                5 |                0.0116 |
| fixed2014_denominator_not_fixed_pixel_mask  |       54 |         0 |                0 |                0      |
| hub_linear_trends                           |      432 |       432 |              135 |                0.312  |
| leave_one_hub_out                           |    21024 |     21024 |              289 |                0.0137 |
| leave_one_refinery_shock_out_fixed_weights  |     6912 |      6912 |              105 |                0.0152 |

## Lead and anticipation diagnostics

A significant lead would be inconsistent with a simple no-anticipation interpretation, but multiple testing and serially correlated exposure make isolated nominal significance weak evidence.

| term   |   models |   positive_share |   nominal_significant |
|:-------|---------:|-----------------:|----------------------:|
| dose   |      216 |            0.292 |                    18 |
| lead1  |      216 |            0.13  |                   101 |
| lead2  |      216 |            0.625 |                    30 |
| lead3  |      216 |            0.648 |                    38 |

## Exposure identification

| proxy                           | rule            |   exposure_sd_min |   exposure_sd_max |   lag_correlation_min |   lag_correlation_max |   within_covariance_min |   within_covariance_max |
|:--------------------------------|:----------------|------------------:|------------------:|----------------------:|----------------------:|------------------------:|------------------------:|
| direct_rail                     | exp100_sum1     |             0.356 |             0.401 |                 0.888 |                 0.899 |               -0.000497 |               -0.000245 |
| direct_rail                     | inverse50       |             2.43  |             2.59  |                 0.903 |                 0.908 |               -0.00321  |               -0.00144  |
| direct_rail                     | relative_exp100 |             3.59  |             3.8   |                 0.853 |                 0.86  |               -0.00562  |               -0.00313  |
| direct_truck                    | exp100_sum1     |             1.57  |             2.02  |                 0.909 |                 0.91  |               -0.00203  |               -0.000115 |
| direct_truck                    | inverse50       |             0.894 |             1.1   |                 0.93  |                 0.934 |               -0.00109  |               -0.000405 |
| direct_truck                    | relative_exp100 |             1.72  |             2.21  |                 0.899 |                 0.9   |               -0.00218  |               -0.000151 |
| lowest_supported_mode_candidate | exp100_sum1     |             0.375 |             0.436 |                 0.889 |                 0.903 |               -0.000556 |               -0.000264 |
| lowest_supported_mode_candidate | inverse50       |             2.44  |             2.62  |                 0.902 |                 0.908 |               -0.00336  |               -0.00163  |
| lowest_supported_mode_candidate | relative_exp100 |             3.38  |             3.72  |                 0.824 |                 0.842 |               -0.00489  |               -0.00273  |

There are 31,878 estimated diagnostic coefficient rows and 432 unidentified specifications. Lag-1/lag-2 exposure correlations are high, so separate lag coefficients and distributed-lag components are difficult to interpret independently. Identifying variation is differential within-hub change after hub and year fixed effects, not the national soybean trend.

## Interpretation boundary

Closer-ring share estimates are often positive but imprecise, while outer-ring estimates are more often negative. Period, hub-trend, leave-one-hub and leave-one-refinery checks show meaningful sign instability in portions of the grid. The current evidence therefore does not establish that LCFS-linked capacity caused either an increase or decrease in soybean planting. Full coefficient files retain positive, negative and unidentified results. Empty exclusive polygons are excluded from acreage regressions rather than coded as zero production. Fixed valid-pixel counts are not proof of a fixed pixel mask; the separate six-band forest/classification audit remains the relevant validation.

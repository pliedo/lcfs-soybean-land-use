# Paired 2018–2019 CDL forest-classification audit

The audit aligns the 2019 CDL raster to each 2018 reference grid and compares identical common-valid pixels inside all 348 exclusive hub–ring polygons (58 hubs × six rings). Failed downloads raise errors; missing coverage is not coded as a land class.

## Ring-level evidence

|   ring_index |   common_pixels |   soy_2018 |   soy_2019 |   soy_change_pixels |   soy_change_pp |   forest_2018 |   forest_2019 |   forest_change_pixels |   forest_change_pp |   forest_to_soy |   soy_to_forest |   net_forest_to_soy |   mixed_forest_change_pp |   deciduous_forest_change_pp |
|-------------:|----------------:|-----------:|-----------:|--------------------:|----------------:|--------------:|--------------:|-----------------------:|-------------------:|----------------:|----------------:|--------------------:|-------------------------:|-----------------------------:|
|            1 |       2.933e+08 |  7.232e+07 |  6.459e+07 |          -7.73e+06  |         -2.635  |     3.684e+07 |     4.098e+07 |              4.148e+06 |              1.414 |       1.585e+05 |       6.782e+04 |           9.07e+04  |                   0.9564 |                      -0.1619 |
|            2 |       6.062e+08 |  1.246e+08 |  1.098e+08 |          -1.48e+07  |         -2.442  |     1.098e+08 |     1.199e+08 |              1.004e+07 |              1.657 |       3.771e+05 |       1.437e+05 |           2.334e+05 |                   1.63   |                      -0.7187 |
|            3 |       6.494e+08 |  9.502e+07 |  8.099e+07 |          -1.403e+07 |         -2.161  |     1.633e+08 |     1.748e+08 |              1.158e+07 |              1.783 |       4.095e+05 |       1.207e+05 |           2.889e+05 |                   2.764  |                      -2.025  |
|            4 |       5.943e+08 |  5.512e+07 |  4.473e+07 |          -1.039e+07 |         -1.748  |     1.82e+08  |     1.924e+08 |              1.041e+07 |              1.751 |       2.804e+05 |       7.392e+04 |           2.065e+05 |                   3.324  |                      -2.615  |
|            5 |       5.325e+08 |  2.97e+07  |  2.223e+07 |          -7.466e+06 |         -1.402  |     1.833e+08 |     1.907e+08 |              7.436e+06 |              1.396 |       1.627e+05 |       4.024e+04 |           1.224e+05 |                   3.65   |                      -3.174  |
|            6 |       4.701e+08 |  1.873e+07 |  1.409e+07 |          -4.64e+06  |         -0.9871 |     1.509e+08 |     1.562e+08 |              5.307e+06 |              1.129 |       8.585e+04 |       2.36e+04  |           6.225e+04 |                   3.52   |                      -3.414  |

Across the six bands, net soybean change is -59,062,961 pixels. Net forest-to-soy switching (forest→soy minus soy→forest) is 1,004,089 pixels. Therefore forest reassignment cannot mechanically explain the aggregate soybean decline if the latter is negative. The separate mixed-forest and deciduous-forest columns expose within-forest relabeling that would be hidden by an aggregate forest category.

## Largest destinations of pixels leaving soybeans

|   ring_index | to_2019        |   pixels |   share_of_soy_loss |
|-------------:|:---------------|---------:|--------------------:|
|            1 | corn           | 47736415 |             0.7878  |
|            1 | fallow_idle    |  5766647 |             0.09516 |
|            1 | other_cropland |  5460797 |             0.09012 |
|            2 | corn           | 77122005 |             0.7542  |
|            2 | other_cropland | 11355060 |             0.1111  |
|            2 | fallow_idle    | 10776860 |             0.1054  |
|            3 | corn           | 49998674 |             0.6722  |
|            3 | other_cropland | 12894366 |             0.1734  |
|            3 | fallow_idle    |  8813572 |             0.1185  |
|            4 | corn           | 22434736 |             0.5583  |
|            4 | other_cropland |  9828003 |             0.2446  |
|            4 | fallow_idle    |  5974464 |             0.1487  |
|            5 | corn           | 11376025 |             0.5212  |
|            5 | other_cropland |  5309571 |             0.2433  |
|            5 | fallow_idle    |  3892752 |             0.1783  |
|            6 | corn           |  7768193 |             0.5392  |
|            6 | other_cropland |  3554415 |             0.2467  |
|            6 | fallow_idle    |  2187770 |             0.1519  |

## Interpretation

This is a paired classification diagnostic, not evidence that every annual series uses a permanently fixed pixel mask. A pixel transition may reflect real land-use change or classification error. The broad, coordinated 2019 increase in mixed forest alongside a decline in deciduous forest is consistent with a classification-input break, so forest subtypes should not be interpreted as ecological conversion without external validation. The soybean outcome is less mechanically vulnerable to that particular within-forest relabeling, but its 2019 movement may still reflect weather, trade conditions, crop rotation and classification error. Regression checks that omit 2019 and 2021 are retained as sensitivities rather than preferred estimates.

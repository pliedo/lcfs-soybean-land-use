# Pooled ring capacity scenarios

Pooled model: outcome at crusher h, ring r, year t equals crusher–ring FE plus ring–year FE plus six ring-specific exposure slopes. Exposure is the sum of planting-aligned eligible physical-refinery capacity times route-cost weights, divided by 100 million gallons/year. Cluster covariance is computed at crusher level, preserving cross-ring correlation. Valid-land-zero polygons are excluded, leaving 57 observed crushers; empty polygons are not zero-acre soybean observations.

All seven existing weighting rules and both crosswalk scenarios are retained. Current, single lags 1–3, distributed current/lag1/lag2, and joint current/leads1–3 models are estimated. Lagged exposure already follows the planting-aligned policy timing; a pathway approved today may only enter eligible exposure for the following planting season. Coefficients do not isolate pathway approval from refinery construction and other contemporaneous changes. No lag or weight is selected for its sign or significance. Nominal tests are not adjusted for multiple testing.

## Aggregate 100-million-gallon/year additions

Each scenario adds persistent eligible capacity at an existing refinery location, using its existing mode-constrained linehaul-cost proxy weights. These are potential exposure weights, not observed procurement shares. California and Texas scenarios can differ in modes as well as location. They are not a controlled relocation of an otherwise identical refinery. Single-lag results give the predicted response at that lag; distributed results give the response after all three capacity additions enter their respective regressors.

Share regressions are converted to acres using each polygon's 2024 valid-land or cropland acres, and predictions are summed across exclusive polygons. Direct-acreage regressions are aggregated separately. Full coefficient covariance is used for the aggregate confidence interval; uncertainties are not added as if rings were independent. Log-acre coefficients are reported but not converted to aggregate acres without a nonlinear uncertainty calculation. Observed 2024 soybean acres total 81,803,903.54 and valid land totals 699,662,184.19 acres. This is the measured crusher catchment footprint, not an independently validated national acreage total. Actual observed annual land support is used during estimation; the scenario baseline fixes 2024 denominators, not every historical pixel mask.

## Findings

For the focal lowest-supported-mode proxy and relative exponential decay (100 truck-equivalent km), main physical-onset capacity scenario, lag1 all-land share model: Rodeo predicts +16,233.60 acres, 95% CI [-89,280.14,121,747.33]; Port Arthur +23,116.13 [-103,981.90,150,214.17]; Dickinson +49,878.71 [-81,171.18,180,928.61]. All are uncertain. Direct acres estimates for the same scenarios are respectively -90,271.19, -108,067.85 and -144,015.86 acres, also not significant at 5%.

Across all 3,360 aggregate scenario rows, none is both positive and nominally significant at 5%. This does not establish no effect; it does not support selecting a positive significant aggregate LCFS planting claim.

The focal lag1 all-land-share slope is significantly larger on average in 0–75-mile rings than 75–150-mile rings: difference +0.155735 pp per 100 mgy weighted exposure, p=0.000327. This is a spatial contrast, not an aggregate increase. Positive inner coefficients and negative outer coefficients can partly offset in aggregate, with larger land areas influencing the sum. The saturation mechanism is a hypothesis, not tested by this contrast alone.

Joint lead test (all 18 lead–ring interactions): all-land share p=0.2202; cropland share p=0.004815; acres p=1.59e-12; log acres p=1.22e-10. Failure to reject the all-land-share test does not establish absence of anticipation or validate causal identification, especially with correlated future exposure. Pooled lead sign/magnitude summaries and all coefficients are exported. Do not compare raw coefficient magnitudes across differently scaled weighting rules.

Reproduce: `OPENBLAS_NUM_THREADS=1 python code/40_pooled_ring_capacity_scenarios.py`. Outputs: pooled_ring_capacity_coefficients.csv, pooled_100mgy_refinery_scenarios.csv, pooled_ring_capacity_joint_tests.csv and pooled_lead_sign_magnitude_summary.csv in output/tables.

## Cumulative footprint sensitivity

All six cumulative cutoffs (0–25 through 0–150 miles) are retained for every location, weight, lag, crosswalk scenario and share/acre outcome: 20,160 scenario rows. Full results are in pooled_100mgy_cumulative_scenarios.csv.gz; the preexisting focal rule and main crosswalk scenario are also in pooled_100mgy_cumulative_focal.csv. A sourcing-radius-based primary cutoff can be justified independently; the last significant cutoff must not be chosen retrospectively as a confirmatory specification.

For Rodeo, focal lag1 all-land-share predictions: 0–25 +7,991 acres (p=.0830); 0–50 +33,386 (.0707); 0–75 +50,702 (.0884); 0–100 +58,189 (.1379); 0–125 +38,090 (.3921); 0–150 +16,234 (.7591). At 0–75 the 95% interval is [-7,875,109,278] acres and direct-acreage estimate is +1,739 [-60,421,63,900], p=.9555. Some alternative rules and lags yield positive nominal significance: e.g. Rodeo 0–75 nearest-eligible lag3 direct acres +6,818 [1,894,11,743], p=.007515. This assumes all refinery exposure goes to the lowest-cost eligible crusher (ties split); it is a sensitivity, not measured procurement or evidence for preferring lag3. Multiple testing and timing concerns remain.

Validation: focal pooled lag1 slopes match an independent explicit fixed-effect dummy least-squares regression within 1.4e-13; scenario keys are unique and numeric outputs finite.

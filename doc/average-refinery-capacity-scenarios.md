# Average refinery addition and location scenarios

The average scenario is a hypothetical persistent addition of 100 million gallons/year of eligible capacity, placed with equal probability at each of the 16 existing physical refinery sites. It is not the average observed refinery size, a population-weighted national effect, or a causal effect isolated from refinery opening. Mode assumptions remain site-specific. Equal-location mean weights are applied to the estimated ring coefficients; the full crusher-cluster covariance is applied to this average contrast. Location estimates share coefficients and must not be treated as 16 independent estimates whose standard errors shrink by sqrt(16).

All seven weighting rules and both capacity/crosswalk scenarios are retained. The user-facing summary restricts lags to current, 1, 2 and distributed current/1/2, and footprints to 0–50 and 0–75 miles. Point estimates use the pooled ring model; fixed 2024 acreage denominators translate shares to acres. Confidence intervals reflect sampling uncertainty of coefficients, not uncertainty in transport costs, procurement weights or capacity measurement.

| Model | Timing | Area | Average acres change | 95% interval | Relative change in baseline soybean acres | p |
|---|---|---|---:|---|---:|---:|
| Nearest eligible; direct acres | lag2 | 0–50 | 3,118 | [684,5,552] | 0.00745% | .0130 |
| Nearest eligible; direct acres | lag2 | 0–75 | 4,499 | [45,8,952] | 0.00730% | .0478 |
| Inverse-square cost; all-land share converted to acres | distributed0–2 | 0–50 | 7,767 | [2,772,12,762] | 0.01856% | .0029 |
| Inverse-square cost; all-land share converted to acres | distributed0–2 | 0–75 | 12,696 | [4,933,20,458] | 0.02061% | .0018 |
| Relative exponential; all-land share converted to acres | lag1 | 0–50 | 50,126 | [-4,333,104,584] | 0.11980% | .0705 |
| Relative exponential; all-land share converted to acres | lag1 | 0–75 | 73,211 | [-10,686,157,108] | 0.11884% | .0859 |

The inverse-square direct-acreage distributed totals are +4,919 [-1,758,11,596] and +6,145 [-5,186,17,476], respectively, and are not nominally significant. Cropland-share predictions are generally negative under these same concentrated methods. The five other weighting rules have no positive nominally significant average cumulative prediction for the stated footprints and lags. Multiple testing is not adjusted; highlighted results must be read alongside the full 168-row summary.

Nearest-eligible direct-acreage totals are identical across all refinery locations because weights sum to one and ring responses are common across hubs. Their locations identify different receiving crushers, but aggregate direct acres cannot show location heterogeneity in this model. Relative exponential weights permit different aggregate predictions; the map shows the all-land-share-derived lag1 0–75 prediction: Norco +43,592 [-6,878,94,063], Rodeo +50,702 [-7,875,109,278], Dickinson +77,029 [-10,919,164,977]. None is nominally significant at 5%. The accompanying direct-acreage figure exposes the uncertainty and method dependence.

The map uses crusher points, not exclusive polygon boundaries. Crusher coordinates are reconstructed exactly from the existing 16 great-circle distances and refinery crosswalk coordinates; all 58 coordinates reproduce those distances within 1e-5 km. This recovers original distance inputs, not independent coordinate validation. USA coastline is an illustrative low-resolution outline from https://github.com/johan/world.geo.json/blob/master/countries/USA.geo.json. Dickinson, North Dakota represents the Northern Plains/Midwest example; it is not a generic central-Midwest refinery. The map uses common color limits across three actual-site scenarios. Access/mode assumptions differ by site, so these are not controlled relocations of identical routing networks.

Correction to an earlier conversational percentage: +3,118 acres within 0–50 miles is +0.00745% of the 41.84-million-acre baseline, not +0.0118%. The latter was a conversion error; the acreage coefficient is unchanged.

Reproduce: run code/42_average_refinery_scenarios.py, then code/43_plot_refinery_location_scenarios.py. Both figure types are 16:9 PNG and vector PDF. Full average estimates are output/tables/pooled_average_100mgy_refinery.csv; focused summary is average_refinery_lags_0_2_summary.csv.

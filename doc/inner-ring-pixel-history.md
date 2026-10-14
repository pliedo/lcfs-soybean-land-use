# Descriptive spatial audit: exclusive 0–25-mile catchments

Requested October 13, 2026. This is separate from the seminar slide deck.
No exposure regressions or causal claims enter this audit.

## Full-period procedure

Use the exact study polygons rebuilt by the existing spatial-zone script,
stopping before unrelated overlap diagnostics. Process all nonempty inner
catchments for 2013–2025. Raster requests use EPSG:5070, a common 30 m grid,
and 30 km tiles. Verify identical transforms and shapes across all 13 years.
Count pixel centers inside the exclusive polygons. Never recode a failed
download as zero coverage. Validate the 13-year smoke tile before the hub batch.

Outputs include annual exact-code transition matrices, first/last transitions,
soybean frequency across all 13 years, first observed soybean occurrence,
soybean entry counts, and forest gain/loss origins and destinations. Forest
subtype changes remain visible separately. Pure soybean is CDL class 5;
double-cropped soybean classes remain separate rather than silently altering
the baseline definition.

For each hub, select its highest soybean-share year from the existing annual
nonwater panel, breaking ties toward the earlier year. Follow that year's
soybean cohort backward and forward through all years. Report the original
CDL code in each year. Peak-year selection is descriptive and does not identify
policy effects.

Annual transitions use pairwise valid coverage. Persistence, peak cohorts and
endpoints use complete-series valid coverage. Also report persistence on a
fixed nonwater mask that excludes any pixel labeled water in any year.
Exclude background 0 and cloud/no-data 81 from valid observations. Preserve
water as a transition category, so water/land relabeling can be diagnosed.
Report annual, complete-series and fixed-nonwater denominators separately.

An always-soybean pixel is class 5 in all 13 observations. An intermittently
soybean pixel is not automatically expansion: corn/soybean rotation is common.
First observed soybean is not proof of first-ever soybean cultivation.
Endpoint changes and full histories distinguish net expansion from turnover.
Changed forest labels do not prove tree growth or clearing. Investigate source
updates and spatial concentration before assigning physical meanings.

Memory scales with one tile times 13 years, not the national raster stack.
Successful tile counters and georeferenced history maps are checkpointed.
GitHub caches retain checkpoints after failed jobs. Three simultaneous hub
jobs limit pressure on the USDA service. Per-hub artifacts remain available
before the final merge. Final tables are committed only after complete-hub and
accounting checks. Existing outcome CSVs and prior diagnostics are untouched.

History GeoTIFF bands: (1) soybean-year count, (2) nonsoy-to-soy entry count,
(3) first/last forest status: 0 unchanged, 1 loss, 2 gain. Value 255 is outside
complete-series support. Counters retain exact classes for detailed analysis.

## Other LCFS pathways and comparison with Miao, Li and Khanna

The current treatment measures approved soybean-pathway capacity, not every
LCFS incentive affecting soybean markets. Other vegetable-oil pathways can
affect soybean demand through substitution, competing acreage and broader
oil-market prices. The sign is not predetermined: a cheaper substitute can
displace soybean oil, whereas demand across linked oil markets can raise
soybean oil prices. Used oils and animal fats can substitute at refineries
without directly increasing oilseed acreage.

This is a hypothesis for future checks, not an established explanation for a
smaller coefficient. Correlated omitted pathway exposure can bias estimates
in either direction. A common national price response can be absorbed by year
effects, so the current coefficient measures differential local exposure rather
than the entire national policy response.

Future controls should separate soybean, other vegetable oil, and fats/waste
pathway eligibility by physical refinery and year. Multiple pathway approvals
at the same refinery must not duplicate its capacity. Feedstock-specific fuel
volumes would be preferable where available; without them, retain eligibility
indicators rather than inventing shares of capacity assigned to each feedstock.

Miao, Li and Khanna examine soybean-based biofuel production and crushing over
2011–2020, county acreage, price channels and IV/dynamic specifications. Our
exercise uses approved capacity, a different period and local ring outcomes.
Capacity utilization and soybean feedstock shares are unobserved. They can
weaken the demand proxy, but constant proportional utilization alone does not
automatically explain a smaller percentage elasticity. These estimands are not
directly comparable and no particular coefficient gap has been attributed.

Sources:
- https://onlinelibrary.wiley.com/doi/10.1002/aepp.70005
- https://afdc.energy.gov/fuels/renewable-diesel
- https://content.govdelivery.com/accounts/CARB/bulletins/4180c3a
- Existing doc/forest-classification-evidence.md for forest input changes.

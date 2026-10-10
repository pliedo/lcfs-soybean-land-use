# 2019 measurement and LCFS source audit

## Confirmed measurement changes

USDA Iowa 2018 metadata identifies NLCD 2011 as non-agricultural training and
validation data; 2019 metadata identifies NLCD 2016. This establishes a source
break, not the fraction of soybean changes caused by that break.

- https://www.nass.usda.gov/Research_and_Science/Cropland/metadata/metadata_ia18.htm
- https://www.nass.usda.gov/Research_and_Science/Cropland/metadata/metadata_ia19.htm

The 2019 metadata also documents agricultural-training inward buffers changing
from 30 to 15 metres. Non-agricultural CDL classes should not alone establish
annual forest conversion.

## Completed marginal audit

Run `python code/10_audit_2019_and_treatment.py`. Every hub-ring has identical
valid-pixel counts in 2018 and 2019. Across all rings the forest-class shares
change substantially; this does not establish where any particular soybean
pixel went. Source data and aggregate diagnostics remain unchanged.

## Paired raster check

Workflow `audit-2019.yml` first checks one hub, then the remaining hubs' 0–25-mile
exclusive polygons. It downloads aligned 30-metre windows for 2018 and 2019,
asserts equal grids, and compares only pixels valid in both years. Outputs
separate soybean, corn, fallow, other cropland, forest, wetlands and other
non-crop transitions. Download failures fail the audit; they are never zeros.
This is an inner-ring audit, not a completed validation of all outer bands.

## Interpretation and follow-up

Keep the all-land denominator fixed; report 2019 separately and run estimated
effects with and without 2019 when the treatment panel is resolved. Annual
cropland share is available now but is not a fixed agricultural-land mask.
A fixed mask requires aligned multiyear pixel identities and an explicit
pre-treatment eligibility rule. Do not call a denominator made from aggregate
2018 cropland counts a fixed-mask analysis.

## LCFS inputs recovered

Original uploaded `rd_pathways_ca_lcfs.xlsx` and `hefa_capacity.xlsx` are retained
unchanged under data/raw. Pathway sheet has 44 rows, 18 CARB keys, and 22 rows
flagged retired. All pathway keys match capacities and locations. Certification
date headers have leading whitespace; the R reader now trims headers.

Two pairs of CARB keys share standardized physical name/location and identical
capacity histories: Wynnewood (83001, 82420) and Sinclair (83388, 82441).
These are possible facility aliases and must not automatically contribute
capacity twice. If verified aliases, define one physical plant, carry its
capacity once, and use the earliest qualifying approval across its keys.
Wynnewood approval dates differ (2023-06-28 and 2024-06-19).

Approval is certification eligibility, not an observed soybean-oil purchase
or actual credit volume. Missing retirement dates prevent reconstructing
historical active pathway status. A first approval in this snapshot may not
be the plant's first-ever approval; audit archival coverage before interpreting
it as an exogenous event. Capacity units/timing and RD versus total HEFA
capacity need source reconciliation before final treatment estimation.

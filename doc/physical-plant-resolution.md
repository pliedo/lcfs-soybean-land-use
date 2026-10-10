# Physical refinery mapping and approval-onset sensitivity

Run `python code/12_build_physical_plant_treatment.py` (pandas, openpyxl).
Raw workbooks remain unchanged. All CARB keys/pathways are retained in history;
capacities are counted once per mapped physical plant, not once per pathway.

## Wynnewood

CARB's 2023 public-comment list places key 82420 in Wynnewood, Oklahoma, and
the 2024 list places key 83001 in Wynnewood with essentially the same soybean
pathway description. CVR's 2024 results describe one Wynnewood RDU and its
feedstock pretreater. Combined with nearly identical workbook coordinates,
this supports treating the two records as one physical site for capacity.
First observed soybean approval across those keys: 2023-06-28, from workbook.
The 2024 approval is retained as an event, but not a second plant's capacity.

- https://ww2.arb.ca.gov/resources/documents/2023-lcfs-pathways-requiring-public-comments
- https://ww2.arb.ca.gov/resources/documents/2024-lcfs-pathways-requiring-public-comments
- https://investors.cvrenergy.com/news/news-details/2025/CVR-Energy-Reports-Fourth-Quarter-and-Full-Year-2024-Results-02-18-2025/default.aspx

## Sinclair and the misplaced coordinate

CARB explicitly places key 82441 at Sinclair, Wyoming. Its workbook coordinate
(41.1255,-104.7971) is in the Cheyenne area and is inconsistent with that record.
Use the workbook's Sinclair-area point (41.7804,-107.1096) as a representative
point in derived outputs only. Its exact within-site location is unverified.
Cheyenne has a separate workbook key F00494 and separate capacity; do not merge
Cheyenne with Sinclair.

### Researcher's original location review

Pedro reports that, during his original crosswalk and detail inspection, he
found the Cheyenne location and did not find the alternative Sinclair location
to be clearly present. This is retained as conflicting prior evidence, not
discarded as a data-entry mistake. The current derived Sinclair point is
provisional. CARB's later description locates key 82441 in Sinclair, but does
not independently verify the exact coordinates used here or identify 83388's
physical site. Original coordinates remain available in the crosswalk and raw
workbook. The exclusion scenarios preserve a way to assess this uncertainty.

Key 83388 shares standardized name/location, capacity history and 2019 approval
date with 82441. Its alias mapping to Sinclair remains PROVISIONAL: an official
record independently locating that key has not been found. An alternative
scenario excludes 83388 entirely. It produces the same onset/capacity totals
here because 82441 carries the same initial approval date and capacity history.

- https://ww2.arb.ca.gov/resources/documents/2024-lcfs-pathways-requiring-public-comments
- https://www.hfsinclair.com/operations/facilities/us/sinclair-wy-parco/default.aspx
- https://www.hfsinclair.com/operations/facilities/us/cheyenne-wy/default.aspx

## Capacity sources are not identical

Farmdoc November 6, 2024 lists Sinclair at 117 MGPY in 2020–2024. The uploaded
NREL table and HF Sinclair's 2024 SEC filing give 153 MGPY, agreeing with the
compiled LCFS workbook. Preserve both as alternatives, not an additive total.
The source disagreement is not yet explained by a verified unit conversion or
capacity definition. Wynnewood is 121 in farmdoc and 100 in the uploaded NREL
table; the compiled workbook uses 121. These source rows are retained unchanged.
The targeted farmdoc scenario overrides only Sinclair/Wynnewood for 2020–2024;
it is NOT a fully farmdoc-sourced history for every refinery or pre-2020 year.
Farmdoc capacities are end-of-year estimates; they need not have been available
at spring planting. Date-sensitive operational capacity needs further audit.

- https://farmdocdaily.illinois.edu/2024/11/updated-estimates-of-the-production-capacity-of-u-s-renewable-diesel-plants-through-2026.html
- https://www.sec.gov/Archives/edgar/data/1915657/000191565724000063/dino-20240331_d2.htm
- Uploaded hefa_capacity.xlsx, nrel and farmdoc sheets

## Treatment interpretation

Retired pathways remain in approval-onset history. Snapshot retirement does not
erase their historical eligibility shock. Later approvals do not reintroduce
the entire plant capacity. No historical active-status claim is made without
retirement dates. First observed approval may not be first-ever approval.

Outputs include calendar-year, May 1 planting cutoff (placeholder), and next-year
eligibility doses. These are eligible capacity, not observed credits, purchases,
or production. Four scenarios: physical site mapping with original compiled
capacity; targeted farmdoc capacity; exclude unverified 83388; exclude both
disputed sites. The main provisional mapping has 16 physical plants from 18
CARB keys. In 2024, 5108 MGPY versus 5382 MGPY if every original key were summed;
the 274 difference is one extra 121 Wynnewood and one extra 153 Sinclair row.
Original key totals are a diagnostic, not a defensible alternative exposure.

Do not interpret these refinery-level doses as a completed crusher exposure
panel. Distance weighting and policy credit value remain to be applied under
the specified research design. No regression results are created by this script.

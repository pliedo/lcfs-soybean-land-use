# Data sources and audit log

This document records the source URL, retrieval date, version, unit, coverage, and processing rule for every input. A source is not final until the entries marked **needs confirmation** are resolved.

## Core causal-data pipeline

| Component | Current file / source | Provenance status | Required action |
|---|---|---|---|
| LCFS certified pathways | `rd_pathways_ca_lcfs.xlsx`, `pathways` sheet; [CARB certified pathway table](https://ww2.arb.ca.gov/resources/documents/lcfs-pathway-certified-carbon-intensities) | Source confirmed. The workbook starts from CARB pathways and filters soybean/soybean-oil feedstocks. | Archive a dated CARB download; preserve the filtering and standardized facility-key code. |
| LCFS credit prices | `rd_pathways_ca_lcfs.xlsx`, `credit_price` sheet; [CARB monthly transfer reports](https://ww2.arb.ca.gov/resources/documents/monthly-lcfs-credit-transfer-activity-reports) | Source confirmed. | Preserve a dated downloaded report/spreadsheet and document monthly-to-annual aggregation. |
| LCFS CI benchmark | `rd_pathways_ca_lcfs.xlsx`, `benchmark` sheet; [17 CCR §95484](https://www.law.cornell.edu/regulations/california/17-CCR-95484); [2025 final rulemaking order](https://ww2.arb.ca.gov/sites/default/files/2025-08/2025_lcfs_fro_oal-approved_unofficial_08112025.pdf) | Source confirmed. The historical series used in the legacy workbook is the pre-2025 benchmark schedule in §95484. The 2025 final rulemaking order is archived for subsequent updates. | Transcribe the exact historical diesel / biomass-based-diesel benchmark series used in the capacity-credit calculation and retain the regulation version date. |
| Renewable-diesel capacity | `hefa_capacity.xlsx`: [Farmdoc 2024 capacity estimates](https://farmdocdaily.illinois.edu/2024/11/updated-estimates-of-the-production-capacity-of-u-s-renewable-diesel-plants-through-2026.html), Table 1; [NREL HEFA report](https://www.nrel.gov/docs/fy24osti/87803.pdf), Appendix B, Table B-1 | Sources confirmed. The workbook harmonizes names and locations across the two sources. | Build a transparent facility-year capacity crosswalk that records source-specific values, the selected value, and any reconciliation decision. |
| Processor-location universe | `soy_crushing_facilities.xlsx`; [Soy Meal Info Center processor map](https://www.soymeal.org/processors/) | Source confirmed; location classification was manually inspected. 59 records were classified as `elevator`, 3 as `office`, and 1 as `no plant`; one record has a bankruptcy flag. | Treat the current 59 locations as **candidate local soybean-handling/processing hubs**, not automatically as verified crushers. Create an auditable facility-level review of plant status, coordinates, and source evidence. |
| Refinery--processor road distance | `road_distance_matrix_km.csv`; generated using OSRM | Derived data. | Rebuild from documented coordinates and OSRM settings; record run date and routing profile. |
| Crop outcomes | USDA NASS [Cropland Data Layer / CropScape](https://www.nass.usda.gov/Research_and_Science/Cropland/SARS1a.php) | Source confirmed. | Cache raw zonal-stat responses and record CDL release year/version. |

## Supporting descriptive inputs

| File | Likely source | Role | Status |
|---|---|---|---|
| `OilCropsAllTables.xlsx` | [USDA ERS Oil Crops Yearbook](https://www.ers.usda.gov/data-products/oil-crops-yearbook) | national soybean/crush context | official source identified |
| `export_import_us.xlsx` | USDA trade / FATUS-style export-import tables | descriptive trade context | exact download page needed |
| Census state and Illinois county shapefiles | U.S. Census TIGER/Line or cartographic boundary files | maps / example code | replace with a scripted official download if used |

## Outcome definitions to implement

For each 25-mile annulus around a facility, the project will calculate from the **same CDL category-count response**:

1. **Soy share of all mapped land**: soybean pixels divided by all valid CDL pixels.
2. **Soy share of cropland**: soybean pixels divided by a documented cropland denominator.

The recommended initial definition treats grassland/pasture as a separate outcome, not as part of the cropland denominator. The final code will explicitly map every relevant CDL category.

## Spatial overlap protocol

Before crop outcomes are estimated, construct every 0--25, 25--50, 50--75, 75--100, 100--125, and 125--150 mile annulus in an equal-area projection. For each focal facility-ring, record:

- overlap area and overlap share with every other facility-ring;
- overlap with the same versus a different distance band;
- the share overlapping the **union** of all other rings;
- number of neighboring facilities and the fraction of unambiguous area.

No pixel will be silently counted twice in the preferred estimation outcome. The **pre-specified primary rule** assigns every location to its **nearest candidate processing hub in straight-line distance** (a clipped Voronoi / exclusive-catchment version of each ring). This handles both cases consistently: when bands differ and when two facilities have the same band. It is preferred to automatically favoring the innermost ring, which would not reflect which hub is geographically closer. Full untrimmed rings and a low-overlap subsample will be reported as robustness checks after the overlap distribution is inspected.

## Open questions

1. What is the original source for the CI benchmark table in `rd_pathways_ca_lcfs.xlsx`?
2. The existing processor list is a manual sample from the Soy Meal Info Center map. **Decision: reconstruct a transparent facility-by-facility review** using the original map entry, satellite/street imagery where available, company/location source, operating status, and an evidence URL or note. The legacy classifications remain preserved as the starting point, not overwritten.
3. The initial spatial extent is fixed at 0--150 miles in six 25-mile bands.

## Audit rule

No construction decision is final until its raw source and transformation are documented here or in a linked metadata file.

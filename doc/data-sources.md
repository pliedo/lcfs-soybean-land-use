# Data sources and audit log

This document records the source URL, retrieval date, version, unit, coverage, and processing rule for every input. A source is not final until the entries marked **needs confirmation** are resolved.

## Core causal-data pipeline

| Component | Current file / source | Provenance status | Required action |
|---|---|---|---|
| LCFS certified pathways | `rd_pathways_ca_lcfs.xlsx`, `pathways` and `soy_pathways` sheets; [CARB certified pathway table](https://ww2.arb.ca.gov/resources/documents/lcfs-pathway-certified-carbon-intensities) | Official source identified; workbook snapshot date and manual edits unknown | Re-download and archive a dated source copy; document the soybean-feedstock filter and facility crosswalk |
| LCFS credit prices | `rd_pathways_ca_lcfs.xlsx`, `credit_price` sheet; [CARB monthly transfer reports](https://ww2.arb.ca.gov/resources/documents/monthly-lcfs-credit-transfer-activity-reports) | Official source identified | Preserve a dated downloaded report/spreadsheet and document monthly-to-annual aggregation |
| LCFS CI benchmark | `rd_pathways_ca_lcfs.xlsx`, `benchmark` sheet | Likely derived from the LCFS regulation / CARB materials | Identify exact source table and any manual transcription |
| Renewable-diesel capacity | `rd_pathways_ca_lcfs.xlsx`, `capacities` sheet; `hefa_capacity.xlsx` with Farmdoc and NREL tabs | **Needs confirmation**: curated compilation rather than a single raw source | Build a facility-year capacity crosswalk with source URL, source date, capacity, start year, and note for every facility |
| Crusher / elevator locations | `soy_crushing_facilities.xlsx` | **Needs confirmation**: source and classification method unknown | Establish source for each facility, geocode method/date, and meaning of `type` |
| Refinery--crusher road distance | `road_distance_matrix_km.csv`; generated using OSRM | Derived data | Rebuild from documented coordinates and OSRM settings; record run date and routing profile |
| Crop outcomes | USDA NASS [Cropland Data Layer / CropScape](https://www.nass.usda.gov/Research_and_Science/Cropland/SARS1a.php) | Official source identified | Cache raw zonal-stat responses and record CDL release year/version |

## Supporting descriptive inputs

| File | Likely source | Role | Status |
|---|---|---|---|
| `OilCropsAllTables.xlsx` | [USDA ERS Oil Crops Yearbook](https://www.ers.usda.gov/data-products/oil-crops-yearbook) | national soybean/crush context | official source identified |
| `export_import_us.xlsx` | USDA trade / FATUS-style export-import tables | descriptive trade context | exact download page needed |
| Census state and Illinois county shapefiles | U.S. Census TIGER/Line or cartographic boundary files | maps / example code | replace with a scripted official download if used |
| `hefa_capacity.xlsx` | Farmdoc and NREL compilation | capacity audit input | exact references and retrieval date needed |

## Outcome definitions to implement

For each 25-mile annulus around a crusher, the project will calculate from the **same CDL category-count response**:

1. **Soy share of all mapped land**: soybean pixels divided by all valid CDL pixels.
2. **Soy share of cropland**: soybean pixels divided by a documented cropland denominator.

The cropland definition will be finalized before estimation. It must specify how annual cropland, double crop, fallow, pasture/grass, forest, developed, water, and unclassified CDL pixels are treated.

## Open questions for Pedro

1. What is the original source of `soy_crushing_facilities.xlsx`? In particular, does `type = elevator` mean an actual soybean crusher, a grain elevator, or a location category?
2. Did you manually create the `soy_pathways`, `facilities`, and `capacities` sheets in `rd_pathways_ca_lcfs.xlsx`? If so, where did each capacity observation come from?
3. Which exact Farmdoc and NREL sources did you use for `hefa_capacity.xlsx`? Are those sources already among the PDFs you uploaded, or elsewhere in the old folder?
4. Should the first spatial-response design end at 100 miles: 0--25, 25--50, 50--75, and 75--100? Or do you want a fifth 100--125 mile band?
5. For the cropland denominator, should grassland/pasture be considered potential agricultural land, or should it remain outside cropland and be a separate land-use outcome?

## Audit rule

No construction decision is final until its raw source and transformation are documented here or in a linked metadata file.

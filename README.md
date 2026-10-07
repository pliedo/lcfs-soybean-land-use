# LCFS and soybean land use

This project studies how California's Low Carbon Fuel Standard (LCFS) may affect U.S. soybean planting through renewable-diesel facilities, soybean crushers, and spatial supply-chain exposure.

## Research design

The working design is a continuous-treatment difference-in-differences framework. Crusher-year LCFS exposure is constructed from refinery-level pathway eligibility and capacity, mapped to crushers using alternative refinery--crusher allocation rules. Crop responses are estimated across multiple distance bands around crushers.

The project will separately document:

1. pathway eligibility, timing, and facility capacity;
2. refinery--crusher distance and exposure construction;
3. Cropland Data Layer outcome construction;
4. treatment timing and estimating equations;
5. robustness to spatial allocation rules and distance-band definitions.

## Repository layout

- `R/`: modular data construction, estimation, and figure code.
- `data/raw/`: downloaded public source data (not versioned).
- `data/derived/`: regenerable intermediate datasets (not versioned).
- `data/metadata/`: tracked source notes, crosswalks, and audit decisions.
- `docs/`: research design and reproducibility documentation.
- `output/`: regenerable figures, tables, and diagnostics.

## Status

This repository starts from a clean redesign of the project. The first milestone is an auditable refinery/pathway/capacity panel, followed by multiple-band crop outcomes and a spatial-response figure for presentation at CIDE.

## Reproducibility

The repository will use `renv` to pin R package versions and `targets` to run the full workflow. The initial setup will be added after the raw-input audit establishes the required packages and data sources.

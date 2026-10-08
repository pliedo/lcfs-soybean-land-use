# LCFS and soybean land use

This project studies how California's Low Carbon Fuel Standard (LCFS) may affect U.S. soybean planting through renewable-diesel facilities, soybean crushers, and spatial supply-chain exposure.

## Research design

The working design is a continuous-treatment difference-in-differences framework. Crusher-year LCFS exposure is constructed from refinery-level pathway eligibility and capacity, mapped to crushers using alternative refinery--crusher allocation rules. Crop responses are estimated across multiple distance bands around crushers.

## Project structure

- `data/raw/`: original, unmodified data.
- `data/clean/`: cleaned and analysis-ready data.
- `code/`: R scripts and other source code.
- `output/`: generated results, tables, figures, and diagnostics.
- `doc/`: project documentation, source notes, and design decisions.

## Status

This repository starts from a clean redesign. The first milestone is an auditable refinery/pathway/capacity panel, followed by multiple-band crop outcomes and a spatial-response figure for presentation at CIDE.

## Reproducibility

The project will use `renv` to pin R package versions and `targets` to run the full workflow. Those files will be added when the raw-input audit establishes the required packages and sources.

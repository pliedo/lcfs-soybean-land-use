# Treatment-data audit

## Objective

Construct a facility-year measure of LCFS-linked renewable-diesel capacity that is transparent about pathway eligibility, capacity timing, and planting timing.

## Baseline source

`data/raw/rd_pathways_ca_lcfs.xlsx`

The initial code uses the workbook's `soy_pathways`, `capacities`, and `facilities` sheets.

## Key improvement over the previous workflow

The earlier code matched a pathway's approval year to capacity and then carried that value forward. The new module uses the entire observed **facility-year capacity series**. A facility's exposure can therefore change when capacity expands after its initial pathway approval.

## Produced timing measures

- `dose_capacity_calendar_mgy`: capacity is active in its certification year.
- `dose_capacity_planting_mgy`: capacity is active only if the facility had a qualifying pathway by the May 1 cutoff in that crop year.
- `dose_capacity_next_year_mgy`: capacity begins in the planting year after certification.

The data do not yet establish a single correct cutoff for every soybean-growing area. The empirical work will show results under all three timing conventions and document the preferred one.

## Retirement and pathway status

The workbook flags some pathways as retired but does not provide a retirement date in the current input. The first module preserves this flag and does not infer a shutdown date. Before final estimation, the path of retired pathways and facility operations must be audited.

## Outputs

- `data/clean/lcfs_pathways_soy.csv`
- `data/clean/lcfs_facility_year_treatment.csv`
- `output/treatment_audit_summary.csv`

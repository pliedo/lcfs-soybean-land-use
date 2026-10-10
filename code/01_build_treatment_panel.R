# Build audited LCFS pathway and capacity panel
#
# Input:
#   data/raw/rd_pathways_ca_lcfs.xlsx
#
# Outputs:
#   data/clean/lcfs_pathways_soy.csv
#   data/clean/lcfs_facility_year_treatment.csv
#   output/treatment_audit_summary.csv
#
# Run this script from the repository root.

suppressPackageStartupMessages({
  library(readxl)
  library(dplyr)
  library(tidyr)
  library(lubridate)
  library(readr)
  library(stringr)
})

raw_file <- file.path("data", "raw", "rd_pathways_ca_lcfs.xlsx")
clean_dir <- file.path("data", "clean")
output_dir <- "output"

if (!file.exists(raw_file)) {
  stop(
    "Missing input file: ", raw_file,
    "\nPlace the LCFS workbook in data/raw/ and run again.",
    call. = FALSE
  )
}

dir.create(clean_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

require_columns <- function(data, columns, sheet) {
  missing <- setdiff(columns, names(data))
  if (length(missing) > 0) {
    stop(
      "Sheet '", sheet, "' is missing: ",
      paste(missing, collapse = ", "),
      call. = FALSE
    )
  }
}

# ---- 1. Read and standardize raw inputs -------------------------------------

pathways_raw <- read_excel(raw_file, sheet = "soy_pathways") %>% rename_with(str_trim)
capacities_raw <- read_excel(raw_file, sheet = "capacities") %>% rename_with(str_trim)
facilities_raw <- read_excel(raw_file, sheet = "facilities") %>% rename_with(str_trim)

require_columns(
  pathways_raw,
  c("key", "Feedstock", "Certification Date", "Current Certified CI", "Retired Pathway"),
  "soy_pathways"
)
require_columns(capacities_raw, "key", "capacities")
require_columns(facilities_raw, c("key", "coordinates"), "facilities")

# The source workbook's soy_pathways sheet is the initial eligibility universe.
# Keep the feedstock text so that this rule can be audited or revised later.
pathways_soy <- pathways_raw %>%
  transmute(
    facility_id = as.character(key),
    feedstock = as.character(Feedstock),
    approval_date = as.Date(`Certification Date`),
    ci_score = as.numeric(`Current Certified CI`),
    pathway_description = as.character(`Pathway Description`),
    retired_flag = !is.na(`Retired Pathway`) & str_trim(as.character(`Retired Pathway`)) != "",
    soybean_feedstock_flag = str_detect(str_to_lower(feedstock), "soy")
  ) %>%
  filter(!is.na(facility_id), !is.na(approval_date)) %>%
  arrange(facility_id, approval_date)

# Annual facility-level nameplate capacity. This deliberately uses the full
# facility-year history, rather than freezing capacity at a pathway's approval year.
capacity_year <- capacities_raw %>%
  select(key, matches("^\\d{4}$")) %>%
  pivot_longer(
    cols = matches("^\\d{4}$"),
    names_to = "year",
    values_to = "capacity_mgy"
  ) %>%
  transmute(
    facility_id = as.character(key),
    year = as.integer(year),
    capacity_mgy = as.numeric(capacity_mgy)
  ) %>%
  filter(!is.na(facility_id), !is.na(year)) %>%
  distinct()

facility_locations <- facilities_raw %>%
  transmute(
    facility_id = as.character(key),
    coordinates_raw = as.character(coordinates)
  ) %>%
  distinct()

# ---- 2. Build auditable treatment timing ------------------------------------

facility_approval <- pathways_soy %>%
  filter(soybean_feedstock_flag) %>%
  group_by(facility_id) %>%
  summarise(
    first_soy_approval = min(approval_date),
    n_soy_pathways = n(),
    any_retired_pathway = any(retired_flag),
    .groups = "drop"
  )

# May 1 is intentionally a transparent placeholder for the baseline
# planting-information cutoff. The regression stage will test alternatives.
planting_cutoff_month <- 5L
planting_cutoff_day <- 1L

facility_year_treatment <- capacity_year %>%
  left_join(facility_approval, by = "facility_id") %>%
  left_join(facility_locations, by = "facility_id") %>%
  mutate(
    capacity_mgy = coalesce(capacity_mgy, 0),
    approval_year = year(first_soy_approval),
    planting_cutoff = as.Date(sprintf(
      "%d-%02d-%02d", year, planting_cutoff_month, planting_cutoff_day
    )),
    eligible_calendar_year = !is.na(first_soy_approval) & year >= approval_year,
    eligible_by_planting = !is.na(first_soy_approval) &
      first_soy_approval <= planting_cutoff,
    eligible_next_planting_year = !is.na(first_soy_approval) &
      year >= approval_year + 1L,
    dose_capacity_calendar_mgy = if_else(
      eligible_calendar_year, capacity_mgy, 0
    ),
    dose_capacity_planting_mgy = if_else(
      eligible_by_planting, capacity_mgy, 0
    ),
    dose_capacity_next_year_mgy = if_else(
      eligible_next_planting_year, capacity_mgy, 0
    )
  ) %>%
  arrange(facility_id, year)

# ---- 3. Save clean datasets and audit summaries -----------------------------

write_csv(pathways_soy, file.path(clean_dir, "lcfs_pathways_soy.csv"))
write_csv(
  facility_year_treatment,
  file.path(clean_dir, "lcfs_facility_year_treatment.csv")
)

audit_summary <- facility_year_treatment %>%
  group_by(year) %>%
  summarise(
    facilities_in_capacity_data = n_distinct(facility_id),
    facilities_calendar_eligible = n_distinct(
      facility_id[eligible_calendar_year]
    ),
    facilities_planting_eligible = n_distinct(
      facility_id[eligible_by_planting]
    ),
    total_capacity_mgy = sum(capacity_mgy, na.rm = TRUE),
    calendar_eligible_capacity_mgy = sum(
      dose_capacity_calendar_mgy, na.rm = TRUE
    ),
    planting_eligible_capacity_mgy = sum(
      dose_capacity_planting_mgy, na.rm = TRUE
    ),
    next_year_eligible_capacity_mgy = sum(
      dose_capacity_next_year_mgy, na.rm = TRUE
    ),
    .groups = "drop"
  )

write_csv(audit_summary, file.path(output_dir, "treatment_audit_summary.csv"))

message(
  "Created clean treatment inputs:\n",
  "  - data/clean/lcfs_pathways_soy.csv\n",
  "  - data/clean/lcfs_facility_year_treatment.csv\n",
  "  - output/treatment_audit_summary.csv"
)

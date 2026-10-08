# Retrieve annual USDA NASS Cropland Data Layer statistics for exclusive hub catchments.
#
# This script queries CropScape's official GetCDLStat service for cumulative
# 25-mile buffers inside each hub's exclusive nearest-hub catchment, caches the
# raw CSV response, and differences adjacent cumulative buffers into true rings.
#
# Default is a small, safe test: hub 1 in 2023.
# Full run (PowerShell):
#   $env:CDL_MODE="full"; Rscript code/03_extract_cdl_outcomes.R
#
# Optional:
#   $env:CDL_YEARS="2019,2020"; $env:CDL_HUBS="1,5,12"
#
# Inputs:
#   output/facility_rings_exclusive.gpkg (created by 02_build_spatial_zones.R)
#
# Outputs (all regenerable):
#   data/raw/cdl_cache/                raw CropScape CSV responses; not versioned
#   data/clean/cdl_category_counts.csv category-level ring statistics
#   data/clean/crop_outcomes_exclusive.csv
#   output/diagnostics/cdl_run_manifest.csv

required_packages <- c("sf", "dplyr", "readr", "stringr", "httr", "tidyr")
missing_packages <- required_packages[!vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing_packages) > 0) {
  stop("Install required packages first: ", paste(missing_packages, collapse = ", "), call. = FALSE)
}

library(sf)
library(dplyr)
library(readr)
library(stringr)
library(httr)
library(tidyr)

rings_file <- "output/facility_rings_exclusive.gpkg"
if (!file.exists(rings_file)) {
  stop(
    "Missing ", rings_file,
    ". Run code/02_build_spatial_zones.R first.",
    call. = FALSE
  )
}

cache_dir <- "data/raw/cdl_cache"
clean_dir <- "data/clean"
diagnostic_dir <- "output/diagnostics"
dir.create(cache_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(clean_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(diagnostic_dir, recursive = TRUE, showWarnings = FALSE)

mode <- Sys.getenv("CDL_MODE", unset = "test")
parse_int_env <- function(name, default) {
  x <- Sys.getenv(name, unset = "")
  if (identical(x, "")) return(default)
  as.integer(strsplit(x, ",", fixed = TRUE)[[1]])
}

if (identical(mode, "full")) {
  years <- parse_int_env("CDL_YEARS", 2013:2024)
  requested_hubs <- parse_int_env("CDL_HUBS", integer())
} else {
  years <- parse_int_env("CDL_YEARS", 2023L)
  requested_hubs <- parse_int_env("CDL_HUBS", 1L)
}

rings <- st_read(rings_file, quiet = TRUE) |>
  st_make_valid()

if (length(requested_hubs) == 0) requested_hubs <- sort(unique(rings$hub_id))
rings <- rings |> filter(hub_id %in% requested_hubs)
if (nrow(rings) == 0) stop("No requested hub IDs are present in the exclusive-ring file.", call. = FALSE)

# CropScape's documented Albers coordinate system.
cropscape_crs <- paste(
  "+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96",
  "+x_0=0 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs"
)

# CDL crop-class rule, version 1. Codes 1--61, 66--77, and 204--254 are
# agricultural crop classes; grass/pasture (176) is explicitly excluded.
is_cropland_code <- function(value) {
  value %in% c(1:61, 66:77, 204:254)
}

cache_path <- function(year, hub_id, outer_miles, component) {
  file.path(
    cache_dir,
    as.character(year),
    sprintf("hub_%03d_outer_%03d_component_%02d.csv", hub_id, outer_miles, component)
  )
}

extract_return_url <- function(text) {
  match <- str_match(text, "<returnURL>([^<]+)</returnURL>")[, 2]
  if (is.na(match)) stop("CropScape response did not contain a returnURL.", call. = FALSE)
  match
}

request_component <- function(geometry, year, hub_id, outer_miles, component) {
  path <- cache_path(year, hub_id, outer_miles, component)
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)

  if (!file.exists(path)) {
    polygon <- st_transform(st_sfc(geometry, crs = st_crs(rings)), cropscape_crs)
    xy <- st_coordinates(polygon)[, 1:2, drop = FALSE]

    # CropScape accepts one simple closed polygon at a time.
    points <- paste(as.vector(t(xy)), collapse = ",")
    request_url <- paste0(
      "https://nassgeodata.gmu.edu/axis2/services/CDLService/GetCDLStat?year=", year,
      "&points=", URLencode(points, reserved = TRUE),
      "&format=csv"
    )

    response <- NULL
    for (attempt in 1:4) {
      response <- try(GET(request_url, timeout(180)), silent = TRUE)
      if (!inherits(response, "try-error") && status_code(response) == 200) {
        response_text <- content(response, "text", encoding = "UTF-8")
        return_url <- try(extract_return_url(response_text), silent = TRUE)
        if (!inherits(return_url, "try-error")) {
          csv_response <- try(GET(return_url, timeout(180)), silent = TRUE)
          if (!inherits(csv_response, "try-error") && status_code(csv_response) == 200) {
            writeBin(content(csv_response, "raw"), path)
            break
          }
        }
      }
      Sys.sleep(2 ^ attempt)
    }
  }

  if (!file.exists(path)) {
    stop(
      "CropScape request failed after retries for hub ", hub_id,
      ", year ", year, ", outer distance ", outer_miles, ".",
      call. = FALSE
    )
  }

  read_csv(path, show_col_types = FALSE, name_repair = "minimal") |>
    rename_with(~ str_trim(.x)) |>
    transmute(
      value = as.integer(Value),
      category = as.character(Category),
      count = as.numeric(Count),
      acreage = as.numeric(Acreage)
    )
}

# A cumulative catchment (exclusive area within 0--d miles) has no annular hole,
# unlike an individual ring. Adjacent cumulative counts are differenced below.
cumulative_components <- function(hub_rings, ring_index) {
  cumulative <- hub_rings |>
    filter(.data$ring_index <= ring_index) |>
    summarise(geometry = st_union(geometry), .groups = "drop") |>
    st_make_valid()

  st_cast(st_geometry(cumulative), "POLYGON", warn = FALSE)
}

records <- list()
manifest <- list()
counter <- 1L

for (hub in sort(unique(rings$hub_id))) {
  hub_rings <- rings |> filter(hub_id == hub) |> arrange(ring_index)

  for (outer_index in sort(unique(hub_rings$ring_index))) {
    outer_miles <- hub_rings |> filter(ring_index == outer_index) |> pull(outer_miles) |> unique()
    components <- cumulative_components(hub_rings, outer_index)

    for (year in years) {
      component_stats <- lapply(seq_along(components), function(component) {
        request_component(components[[component]], year, hub, outer_miles, component) |>
          mutate(component = component)
      })

      records[[counter]] <- bind_rows(component_stats) |>
        group_by(value, category) |>
        summarise(
          count = sum(count),
          acreage = sum(acreage),
          components = n_distinct(component),
          .groups = "drop"
        ) |>
        mutate(
          hub_id = hub,
          year = year,
          outer_miles = outer_miles,
          ring_index = outer_index
        )
      manifest[[counter]] <- tibble(
        hub_id = hub,
        year = year,
        outer_miles = outer_miles,
        components = length(components),
        completed_at_utc = format(Sys.time(), tz = "UTC", usetz = TRUE)
      )
      counter <- counter + 1L
      Sys.sleep(1)
    }
  }
}

cumulative_stats <- bind_rows(records)
category_counts <- cumulative_stats |>
  group_by(hub_id, year, value, category) |>
  arrange(ring_index, .by_group = TRUE) |>
  mutate(
    count = count - lag(count, default = 0),
    acreage = acreage - lag(acreage, default = 0)
  ) |>
  ungroup() |>
  mutate(
    is_soy = str_detect(str_to_lower(category), "soybeans"),
    is_cropland = is_cropland_code(value)
  ) |>
  left_join(
    rings |> st_drop_geometry() |> select(hub_id, ring_index, inner_miles, outer_miles),
    by = c("hub_id", "ring_index", "outer_miles")
  )

outcomes <- category_counts |>
  group_by(hub_id, year, ring_index, inner_miles, outer_miles) |>
  summarise(
    soy_acres = sum(acreage[is_soy], na.rm = TRUE),
    all_valid_acres = sum(acreage[value != 0], na.rm = TRUE),
    cropland_acres = sum(acreage[is_cropland], na.rm = TRUE),
    soy_share_all_land = soy_acres / all_valid_acres,
    soy_share_cropland = soy_acres / cropland_acres,
    .groups = "drop"
  )

write_csv(category_counts, file.path(clean_dir, "cdl_category_counts.csv"))
write_csv(outcomes, file.path(clean_dir, "crop_outcomes_exclusive.csv"))
write_csv(bind_rows(manifest), file.path(diagnostic_dir, "cdl_run_manifest.csv"))

message(
  "Finished ", nrow(outcomes), " hub-year-ring outcomes for ",
  length(unique(outcomes$hub_id)), " hub(s) and ",
  length(unique(outcomes$year)), " year(s)."
)

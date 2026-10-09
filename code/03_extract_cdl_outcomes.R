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

required_packages <- c("sf", "dplyr", "readr", "stringr", "httr", "tidyr", "jsonlite")
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
library(jsonlite)

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
max_outer_index <- as.integer(Sys.getenv("CDL_MAX_OUTER", unset = "6"))
if (!max_outer_index %in% 1:6) stop("CDL_MAX_OUTER must be an integer from 1 to 6.", call. = FALSE)

# Set CDL_RING_INDEX to build exactly one band across all requested hubs. For
# band k>1 we request cumulative k and k-1, then difference them locally.
ring_index_env <- Sys.getenv("CDL_RING_INDEX", unset = "")
target_ring_indices <- if (identical(ring_index_env, "")) {
  seq_len(max_outer_index)
} else {
  as.integer(strsplit(ring_index_env, ",", fixed = TRUE)[[1]])
}
if (any(is.na(target_ring_indices)) || any(!target_ring_indices %in% 1:6)) {
  stop("CDL_RING_INDEX must contain integers from 1 to 6.", call. = FALSE)
}
query_ring_indices <- sort(unique(c(target_ring_indices, target_ring_indices - 1L)))
query_ring_indices <- query_ring_indices[query_ring_indices >= 1L]

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

# Official USDA CroplandCROS CDL image service. It computes a histogram inside
# a supplied polygon and calendar year; unlike the legacy CropScape endpoint,
# it does not queue a separate server-side job per request.
cdl_image_server <- "https://pdi.scinet.usda.gov/image/rest/services/CDL_WM/ImageServer/computeHistograms"
cdl_pixel_acres <- 30 * 30 / 4046.8564224

as_esri_polygon <- function(geometry) {
  projected <- st_transform(st_sfc(geometry, crs = st_crs(rings)), 3857)
  xy <- st_coordinates(projected)
  ring_columns <- intersect(c("L1", "L2"), colnames(xy))
  ring_key <- if (length(ring_columns) == 0) {
    rep(1, nrow(xy))
  } else {
    interaction(as.data.frame(xy[, ring_columns, drop = FALSE]), drop = TRUE)
  }
  ring_rows <- split(seq_len(nrow(xy)), ring_key)
  rings <- lapply(ring_rows, function(i) {
    lapply(i, function(j) unname(as.numeric(xy[j, 1:2])))
  })
  toJSON(
    list(rings = rings, spatialReference = list(wkid = 3857)),
    auto_unbox = TRUE, digits = 15
  )
}

request_component <- function(geometry, year, hub_id, outer_miles, component) {
  path <- cache_path(year, hub_id, outer_miles, component)
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)

  if (!file.exists(path)) {
    pause <- as.numeric(Sys.getenv("CDL_REQUEST_PAUSE_SECONDS", unset = "5"))
    if (!is.na(pause) && pause > 0) Sys.sleep(pause)

    request <- list(
      f = "json",
      geometryType = "esriGeometryPolygon",
      geometry = as_esri_polygon(geometry),
      time = as.numeric(as.POSIXct(sprintf("%d-01-01", year), tz = "UTC")) * 1000
    )

    answer <- NULL
    last_problem <- NULL
    for (attempt in seq_len(5)) {
      response <- try(GET(cdl_image_server, query = request, timeout(90)), silent = TRUE)
      if (!inherits(response, "try-error") && status_code(response) == 200) {
        parsed <- try(content(response, "parsed", type = "application/json"), silent = TRUE)
        if (!inherits(parsed, "try-error") && length(parsed$histograms) > 0) {
          answer <- parsed
          break
        }
        last_problem <- if (!inherits(parsed, "try-error")) {
          if (!is.null(parsed$error$message)) parsed$error$message else "missing histogram"
        } else {
          as.character(parsed)
        }
      } else if (!inherits(response, "try-error")) {
        last_problem <- paste("HTTP", status_code(response))
      } else {
        last_problem <- as.character(response)
      }
      Sys.sleep(5 * attempt)
    }
    if (is.null(answer)) {
      stop(
        "USDA ImageServer did not return a histogram for hub ", hub_id,
        ", year ", year, ", outer distance ", outer_miles,
        ". Last response: ", last_problem, call. = FALSE
      )
    }
    writeLines(toJSON(answer, auto_unbox = TRUE), path, useBytes = TRUE)
  }

  result <- fromJSON(path, simplifyVector = FALSE)
  histogram <- result$histograms[[1]]
  start_value <- round(as.numeric(histogram$min) + 0.5)
  values <- start_value + seq_along(histogram$counts) - 1L
  tibble(
    value = as.integer(values),
    category = if_else(values == 5L, "Soybeans", paste0("CDL_", values)),
    count = as.numeric(unlist(histogram$counts)),
    acreage = count * cdl_pixel_acres
  ) |>
    filter(count > 0)
}

# A cumulative catchment (exclusive area within 0--d miles) has no annular hole,
# unlike an individual ring. Adjacent cumulative counts are differenced below.
cumulative_components <- function(hub_rings, target_ring_index) {
  selected <- hub_rings |> filter(.data$ring_index <= target_ring_index)
  cumulative <- st_sf(
    geometry = st_union(st_geometry(selected))
  ) |>
    st_make_valid()

  st_cast(st_geometry(cumulative), "POLYGON", warn = FALSE)
}

# Each task is one hub-year-outer-boundary query. Default concurrency is one
# because CropScape is a public, server-side geoprocessing service.
workers <- suppressWarnings(as.integer(Sys.getenv("CDL_WORKERS", unset = "1")))
if (is.na(workers) || workers < 1) workers <- 1L
if (.Platform$OS.type == "windows") workers <- 1L

task_grid <- tidyr::crossing(
  hub = sort(unique(rings$hub_id)),
  year = years
) |>
  inner_join(
    rings |>
      st_drop_geometry() |>
      distinct(hub_id, ring_index, outer_miles) |>
      filter(ring_index %in% query_ring_indices),
    by = c("hub" = "hub_id")
  ) |>
  arrange(hub, year, ring_index)

run_task <- function(task_row) {
  hub <- task_row$hub[[1]]
  year <- task_row$year[[1]]
  outer_index <- task_row$ring_index[[1]]
  outer_miles <- task_row$outer_miles[[1]]
  hub_rings <- rings |> filter(hub_id == hub) |> arrange(ring_index)
  components <- cumulative_components(hub_rings, outer_index)

  component_stats <- lapply(seq_along(components), function(component) {
    request_component(components[[component]], year, hub, outer_miles, component) |>
      mutate(component = component)
  })

  list(
    record = bind_rows(component_stats) |>
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
      ),
    manifest = tibble(
      hub_id = hub,
      year = year,
      outer_miles = outer_miles,
      components = length(components),
      completed_at_utc = format(Sys.time(), tz = "UTC", usetz = TRUE)
    )
  )
}

task_rows <- split(task_grid, seq_len(nrow(task_grid)))
if (workers > 1L && .Platform$OS.type != "windows") {
  message("Running ", length(task_rows), " CDL tasks with ", workers, " workers.")
  task_results <- parallel::mclapply(
    task_rows, run_task,
    mc.cores = workers,
    mc.preschedule = FALSE
  )
} else {
  task_results <- lapply(task_rows, run_task)
}

records <- lapply(task_results, `[[`, "record")
manifest <- lapply(task_results, `[[`, "manifest")
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
  ) |>
  filter(ring_index %in% target_ring_indices)

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

# Keep only the requested bands in every output. This lets the workflow commit
# each completed band immediately and combine bands incrementally.
category_counts <- category_counts |> filter(ring_index %in% target_ring_indices)

write_csv(category_counts, file.path(clean_dir, "cdl_category_counts.csv"))
write_csv(outcomes, file.path(clean_dir, "crop_outcomes_exclusive.csv"))
write_csv(bind_rows(manifest), file.path(diagnostic_dir, "cdl_run_manifest.csv"))

message(
  "Finished ", nrow(outcomes), " hub-year-ring outcomes for ",
  length(unique(outcomes$hub_id)), " hub(s) and ",
  length(unique(outcomes$year)), " year(s)."
)

# Build mutually exclusive 25-mile spatial rings and quantify overlap.
#
# Input:
#   data/raw/soy_crushing_facilities.xlsx
#
# Outputs:
#   data/clean/candidate_hubs_clean.csv
#   data/clean/facility_review_template.csv
#   output/facility_ring_overlap_pairs.csv
#   output/facility_ring_overlap_summary.csv
#   output/facility_rings_full.gpkg
#   output/facility_rings_exclusive.gpkg
#
# The raw spreadsheet reverses the usual longitude/latitude labels:
#   lon = latitude; lat = longitude. This script corrects that explicitly.

required_packages <- c("sf", "dplyr", "readxl", "readr", "stringr", "units")
missing_packages <- required_packages[!vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing_packages) > 0) {
  stop(
    "Install required packages first: ",
    paste(missing_packages, collapse = ", "),
    call. = FALSE
  )
}

library(sf)
library(dplyr)
library(readxl)
library(readr)
library(stringr)
library(units)

raw_file <- "data/raw/soy_crushing_facilities.xlsx"
dir.create("data/clean", recursive = TRUE, showWarnings = FALSE)
dir.create("output", recursive = TRUE, showWarnings = FALSE)

if (!file.exists(raw_file)) {
  stop(
    "Missing ", raw_file,
    ". Copy the legacy workbook into data/raw and remove the '(1)' from its name.",
    call. = FALSE
  )
}

# ---- Parameters fixed before inspecting overlap results ----
ring_width_miles <- 25
max_distance_miles <- 150
analysis_crs <- 5070 # NAD83 / Conus Albers, equal-area, metres
mile_to_metre <- 1609.344
ring_breaks <- seq(0, max_distance_miles, by = ring_width_miles)
stopifnot(tail(ring_breaks, 1) == max_distance_miles)

# ---- Read and standardize candidate hub locations ----
hubs_raw <- read_excel(raw_file)
# Keep the legacy column spelling (including `Adress`) explicit for provenance.

# In the source file, lon is latitude and lat is longitude.
hubs <- hubs_raw |>
  transmute(
    hub_id = as.integer(.data[["number"]]),
    company = as.character(.data[["Company"]]),
    address = as.character(.data[["Adress"]]),
    latitude = as.numeric(.data[["lon"]]),
    longitude = as.numeric(.data[["lat"]]),
    type = str_to_lower(str_trim(as.character(.data[["type"]]))),
    railfront = as.integer(.data[["railfront"]]),
    riverfront = as.integer(.data[[grep("^riverfront", names(hubs_raw), value = TRUE)]]),
    oceanfront = as.integer(.data[["oceanfront"]]),
    bankrupt = as.integer(.data[["bankrupt"]])
  ) |>
  mutate(
    hub_status = case_when(
      type == "elevator" & (is.na(bankrupt) | bankrupt == 0L) ~ "candidate_hub",
      type == "office" ~ "office",
      type == "no plant" ~ "no_plant",
      bankrupt == 1L ~ "bankrupt",
      TRUE ~ "review"
    )
  )

if (anyDuplicated(hubs$hub_id)) stop("hub_id must be unique.", call. = FALSE)
if (any(!is.finite(hubs$longitude) | !is.finite(hubs$latitude))) {
  stop("At least one coordinate is missing or invalid.", call. = FALSE)
}

# Primary spatial universe: the sites originally treated as elevators.
# This does not assert that each site is a verified crushing plant.
hubs_primary <- hubs |> filter(hub_status == "candidate_hub")
write_csv(hubs, "data/clean/candidate_hubs_clean.csv")

review_template <- hubs |>
  transmute(
    hub_id, company, address, latitude, longitude,
    legacy_type = type, legacy_bankrupt = bankrupt,
    review_status = "unreviewed",
    site_role = NA_character_,
    evidence_type = NA_character_,
    evidence_url_or_note = NA_character_,
    review_date = NA_character_,
    reviewer = NA_character_,
    include_spatial_universe = if_else(hub_status == "candidate_hub", "yes_pending_review", "no_pending_review"),
    decision_note = NA_character_
  )
write_csv(review_template, "data/clean/facility_review_template.csv")

hubs_sf <- st_as_sf(hubs_primary, coords = c("longitude", "latitude"), crs = 4326, remove = FALSE) |>
  st_transform(analysis_crs)

# ---- Full rings ----
make_rings <- function(point, id) {
  outer <- st_buffer(point, dist = max_distance_miles * mile_to_metre)
  buffers <- lapply(ring_breaks[-1], function(d) st_buffer(point, dist = d * mile_to_metre))
  geoms <- vector("list", length(buffers))
  for (k in seq_along(buffers)) {
    geoms[[k]] <- if (k == 1) buffers[[k]] else st_difference(buffers[[k]], buffers[[k - 1]])
  }
  st_sf(
    hub_id = id,
    ring_index = seq_along(geoms),
    inner_miles = head(ring_breaks, -1),
    outer_miles = tail(ring_breaks, -1),
    geometry = st_sfc(geoms, crs = analysis_crs)
  )
}

rings_full <- do.call(
  rbind,
  Map(make_rings, st_geometry(hubs_sf), hubs_sf$hub_id)
) |>
  left_join(st_drop_geometry(hubs_primary) |> select(hub_id, company), by = "hub_id") |>
  mutate(
    ring_id = paste(hub_id, inner_miles, outer_miles, sep = "_"),
    full_area_sq_miles = as.numeric(st_area(geometry)) / mile_to_metre^2
  )

# ---- Exclusive catchments: closest hub in straight-line distance ----
# This is the exact tie-break rule for every overlap, including equal ring bands.
# A pixel can appear in at most one facility's exclusive ring.
bbox <- st_bbox(st_buffer(st_union(hubs_sf), max_distance_miles * mile_to_metre))
voronoi <- st_voronoi(st_union(hubs_sf), envelope = st_as_sfc(bbox)) |>
  st_collection_extract("POLYGON") |>
  st_as_sf()
voronoi$owner_hub_id <- hubs_sf$hub_id[st_nearest_feature(st_point_on_surface(voronoi), hubs_sf)]

rings_exclusive <- st_intersection(
  rings_full |> select(hub_id, ring_index, inner_miles, outer_miles, ring_id),
  voronoi |> select(owner_hub_id)
) |>
  filter(hub_id == owner_hub_id) |>
  transmute(
    hub_id = hub_id,
    ring_index,
    inner_miles,
    outer_miles,
    ring_id,
    geometry
  ) |>
  group_by(hub_id, ring_index, inner_miles, outer_miles, ring_id) |>
  summarise(geometry = st_union(geometry), .groups = "drop") |>
  mutate(exclusive_area_sq_miles = as.numeric(st_area(geometry)) / mile_to_metre^2)

# ---- Pairwise and union overlap diagnostics ----
candidate_pairs <- st_intersects(rings_full, rings_full, sparse = TRUE)
pair_index <- tibble(
  focal_row = rep(seq_along(candidate_pairs), lengths(candidate_pairs)),
  other_row = unlist(candidate_pairs)
) |>
  filter(focal_row < other_row) |>
  filter(rings_full$hub_id[focal_row] != rings_full$hub_id[other_row])

pairs <- lapply(seq_len(nrow(pair_index)), function(k) {
  a <- pair_index$focal_row[k]
  b <- pair_index$other_row[k]
  overlap <- suppressWarnings(st_intersection(rings_full[a, ], rings_full[b, ]))
  overlap_area <- if (nrow(overlap) == 0) 0 else as.numeric(st_area(overlap)) / mile_to_metre^2
  tibble(
    focal_ring_id = rings_full$ring_id[a],
    other_ring_id = rings_full$ring_id[b],
    focal_hub_id = rings_full$hub_id[a],
    other_hub_id = rings_full$hub_id[b],
    focal_inner_miles = rings_full$inner_miles[a],
    focal_outer_miles = rings_full$outer_miles[a],
    other_inner_miles = rings_full$inner_miles[b],
    other_outer_miles = rings_full$outer_miles[b],
    same_distance_band = rings_full$ring_index[a] == rings_full$ring_index[b],
    overlap_area_sq_miles = overlap_area,
    focal_overlap_share = overlap_area / rings_full$full_area_sq_miles[a],
    other_overlap_share = overlap_area / rings_full$full_area_sq_miles[b]
  )
}) |>
  bind_rows() |>
  filter(overlap_area_sq_miles > 0)

write_csv(pairs, "output/facility_ring_overlap_pairs.csv")

# Union overlap avoids double-counting land that overlaps more than one neighboring ring.
overlap_summary <- lapply(seq_len(nrow(rings_full)), function(i) {
  neighbors <- setdiff(candidate_pairs[[i]], i)
  neighbors <- neighbors[rings_full$hub_id[neighbors] != rings_full$hub_id[i]]

  if (length(neighbors) == 0) {
    union_overlap_area <- 0
    n_neighbors <- 0
  } else {
    # Union neighbors first, then intersect once. This avoids repeated geometry
    # operations and ensures land overlapping several rings is counted once.
    neighbor_union <- st_union(st_geometry(rings_full[neighbors, ]))
    overlap_geometry <- suppressWarnings(
      st_intersection(st_geometry(rings_full[i, ]), neighbor_union)
    )
    union_overlap_area <- if (length(overlap_geometry) == 0) 0 else {
      as.numeric(st_area(overlap_geometry)) / mile_to_metre^2
    }
    n_neighbors <- length(unique(rings_full$hub_id[neighbors]))
  }

  exclusive_area <- rings_exclusive |>
    filter(ring_id == rings_full$ring_id[i]) |>
    summarise(x = sum(exclusive_area_sq_miles), .groups = "drop") |>
    pull(x)
  if (length(exclusive_area) == 0) exclusive_area <- 0

  tibble(
    ring_id = rings_full$ring_id[i],
    hub_id = rings_full$hub_id[i],
    company = rings_full$company[i],
    inner_miles = rings_full$inner_miles[i],
    outer_miles = rings_full$outer_miles[i],
    full_area_sq_miles = rings_full$full_area_sq_miles[i],
    union_overlap_area_sq_miles = union_overlap_area,
    union_overlap_share = union_overlap_area / rings_full$full_area_sq_miles[i],
    unambiguous_area_sq_miles = rings_full$full_area_sq_miles[i] - union_overlap_area,
    unambiguous_area_share = 1 - union_overlap_area / rings_full$full_area_sq_miles[i],
    neighboring_hubs = n_neighbors,
    exclusive_area_sq_miles = exclusive_area,
    exclusive_area_share = exclusive_area / rings_full$full_area_sq_miles[i]
  )
}) |>
  bind_rows()

write_csv(overlap_summary, "output/facility_ring_overlap_summary.csv")

# GeoPackages retain geometry and are ready for QGIS / R mapping.
st_write(rings_full, "output/facility_rings_full.gpkg", delete_dsn = TRUE, quiet = TRUE)
st_write(rings_exclusive, "output/facility_rings_exclusive.gpkg", delete_dsn = TRUE, quiet = TRUE)

message(
  "Built ", nrow(rings_full), " full rings and ", nrow(rings_exclusive),
  " exclusive ring geometries for ", nrow(hubs_primary), " candidate hubs."
)

# Create reproducible spatial-overlap diagnostics and an overview map.
#
# Run after code/02_build_spatial_zones.R.
# Outputs are intentionally small and may be committed under output/diagnostics/.

required_packages <- c("sf", "dplyr", "readr", "ggplot2")
missing_packages <- required_packages[!vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing_packages) > 0) {
  stop("Install required packages first: ", paste(missing_packages, collapse = ", "), call. = FALSE)
}

library(sf)
library(dplyr)
library(readr)
library(ggplot2)

full_file <- "output/facility_rings_full.gpkg"
exclusive_file <- "output/facility_rings_exclusive.gpkg"
pair_file <- "output/facility_ring_overlap_pairs.csv"
diagnostic_dir <- "output/diagnostics"
dir.create(diagnostic_dir, recursive = TRUE, showWarnings = FALSE)

if (!all(file.exists(c(full_file, exclusive_file, pair_file)))) {
  stop("Run code/02_build_spatial_zones.R before this script.", call. = FALSE)
}

full_rings <- st_read(full_file, quiet = TRUE)
exclusive_rings <- st_read(exclusive_file, quiet = TRUE)
pairs <- read_csv(pair_file, show_col_types = FALSE)

# Pairwise sums are reported separately from the union-overlap measure because
# one location can overlap more than two rings.
pair_summary <- bind_rows(
  pairs |>
    transmute(
      ring_id = focal_ring_id,
      hub_id = focal_hub_id,
      inner_miles = focal_inner_miles,
      outer_miles = focal_outer_miles,
      pairwise_overlap_area_sq_miles = overlap_area_sq_miles,
      pairwise_overlap_share = focal_overlap_share
    ),
  pairs |>
    transmute(
      ring_id = other_ring_id,
      hub_id = other_hub_id,
      inner_miles = other_inner_miles,
      outer_miles = other_outer_miles,
      pairwise_overlap_area_sq_miles = overlap_area_sq_miles,
      pairwise_overlap_share = other_overlap_share
    )
) |>
  group_by(ring_id, hub_id, inner_miles, outer_miles) |>
  summarise(
    overlapping_ring_pairs = n(),
    pairwise_overlap_area_sq_miles = sum(pairwise_overlap_area_sq_miles),
    pairwise_overlap_share_sum = sum(pairwise_overlap_share),
    .groups = "drop"
  ) |>
  arrange(desc(pairwise_overlap_share_sum))

write_csv(pair_summary, file.path(diagnostic_dir, "pairwise_overlap_summary.csv"))

band_labels <- c(
  "0–25 miles", "25–50 miles", "50–75 miles",
  "75–100 miles", "100–125 miles", "125–150 miles"
)
exclusive_rings <- exclusive_rings |>
  mutate(distance_band = factor(ring_index, levels = 1:6, labels = band_labels))

hubs <- full_rings |>
  filter(ring_index == 1) |>
  transmute(hub_id, geometry = st_centroid(geometry))

map <- ggplot() +
  geom_sf(
    data = exclusive_rings,
    aes(fill = distance_band),
    color = NA,
    alpha = 0.55
  ) +
  geom_sf(data = hubs, shape = 21, fill = "white", color = "#1b1b1b", size = 1.2, stroke = 0.3) +
  scale_fill_brewer(palette = "YlGnBu", name = "Exclusive distance band") +
  coord_sf(datum = NA) +
  labs(
    title = "Exclusive spatial catchments around candidate soybean-processing hubs",
    subtitle = "Each location within 150 miles is assigned to its nearest hub; bands are 25 miles wide.",
    caption = "Source: manually assembled hub locations; geometry constructed in code/02_build_spatial_zones.R."
  ) +
  theme_void(base_size = 11) +
  theme(
    legend.position = "bottom",
    plot.title = element_text(face = "bold"),
    plot.subtitle = element_text(color = "#444444"),
    plot.caption = element_text(hjust = 0, color = "#666666")
  )

ggsave(
  file.path(diagnostic_dir, "exclusive_catchments_overview.png"),
  map,
  width = 11,
  height = 7,
  dpi = 300,
  bg = "white"
)


area_by_band <- exclusive_rings |>
  st_drop_geometry() |>
  mutate(
    distance_band = factor(ring_index, levels = 1:6, labels = band_labels),
    area_sq_miles = exclusive_area_sq_miles
  ) |>
  group_by(distance_band) |>
  summarise(
    area_sq_miles = sum(area_sq_miles, na.rm = TRUE),
    hub_ring_count = n(),
    .groups = "drop"
  )

write_csv(area_by_band, file.path(diagnostic_dir, "exclusive_area_by_band.csv"))

area_plot <- ggplot(area_by_band, aes(x = distance_band, y = area_sq_miles)) +
  geom_col(fill = "#2C7FB8") +
  labs(
    title = "Land assigned to candidate hubs by distance band",
    subtitle = "Exclusive nearest-hub allocation; no land is counted twice.",
    x = NULL,
    y = "Square miles"
  ) +
  theme_minimal(base_size = 11) +
  theme(
    plot.title = element_text(face = "bold"),
    axis.text.x = element_text(angle = 30, hjust = 1)
  )

ggsave(
  file.path(diagnostic_dir, "exclusive_area_by_band.png"),
  area_plot,
  width = 8,
  height = 5,
  dpi = 300,
  bg = "white"
)

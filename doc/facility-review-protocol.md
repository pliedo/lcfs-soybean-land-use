# Candidate-hub facility review protocol

The legacy `soy_crushing_facilities.xlsx` list was assembled manually from the Soy Meal Info Center processor map, Google searches, and visual inspection of site infrastructure. It is retained as the starting universe. This review makes the classification reproducible without retroactively claiming that every location is a verified crusher.

## Unit of review

One row per legacy location, including the original `elevator`, `office`, `no plant`, and bankruptcy classifications. The spatial analysis initially uses the 59 locations marked `elevator`, labelled **candidate local soybean-handling/processing hubs**.

## Fields to record

| Field | Description |
|---|---|
| `hub_id` | Original spreadsheet identifier; never changes. |
| `company`, `address`, `coordinates` | Original values, corrected only with an explicit note. |
| `legacy_type` | Original manual classification. |
| `review_status` | `unreviewed`, `confirmed_operating`, `confirmed_nonplant`, `closed_or_bankrupt`, or `uncertain`. |
| `site_role` | `crushing`, `grain_elevator`, `other_processing`, `office`, `terminal`, or `unknown`. |
| `evidence_type` | Company source, Soy Meal map, satellite imagery, state permit, news item, or other. |
| `evidence_url_or_note` | Stable URL when available, otherwise a concise reproducible search note. |
| `review_date` | Date checked. |
| `reviewer` | Initials / name. |
| `include_spatial_universe` | Yes / no, with rationale. |

## Review decision rule

- **Confirmed operating:** evidence indicates an active physical grain-handling, crushing, or soybean-processing location at the recorded coordinates.
- **Confirmed nonplant:** office, mailing address, or no physical relevant infrastructure.
- **Closed or bankrupt:** facility ceased relevant operations in the study period; retain it in the audit file and decide separately whether it should be active in each year.
- **Uncertain:** do not silently drop it. Keep its legacy status and flag it for sensitivity analysis.

The first presentation analysis will retain the legacy 59 candidate hubs, clearly labelled as such. The paper will report results for a verified / confirmed-operating subset once the review is complete.

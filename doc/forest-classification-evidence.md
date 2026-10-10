# Forest-classification evidence, checked October 10, 2026

## Definitions versus mapping inputs

CDL 141/142/143 correspond to NLCD deciduous/evergreen/mixed forest classes
41/42/43. Forest is dominated by trees generally over 5 m tall and exceeding
20% vegetation cover. Deciduous/evergreen require over 75% dominance of their
respective tree types; mixed means neither exceeds 75%. The checked legends
retain these definitions. No changed numeric forest-code meaning has been
established. A mixed-forest increase is not evidence of a newly planted forest.

https://www.mrlc.gov/data/legends/national-land-cover-database-class-legend-and-description
https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/metadata/landcover.html

## Documented input changes

USDA Iowa metadata identifies NLCD 2011 in 2018, NLCD 2016 in 2019 and 2020,
and NLCD 2019 in 2021. The 2021 tree-canopy ancillary input also changes to
NLCD 2016, versus NLCD 2011 previously. These state examples demonstrate
methodological breaks; they do not constitute a state-by-state audit of every
pixel in our multistate catchments.

https://www.nass.usda.gov/Research_and_Science/Cropland/metadata/metadata_ia18.htm
https://www.nass.usda.gov/Research_and_Science/Cropland/metadata/metadata_ia19.htm
https://www.nass.usda.gov/Research_and_Science/Cropland/metadata/metadata_ia20.htm
https://www.nass.usda.gov/Research_and_Science/Cropland/metadata/metadata_ia21.htm

USGS released NLCD 2016 in 2019 and concurrently produced multiple historical
epochs. Nominal land-cover year is not release year. Thus the 2019 CDL training
change is not a clean 2018-to-2019 ecological change measure. USDA recommends
NLCD for studies of non-agricultural cover; CDL samples NLCD for training and
validation rather than simply copying all non-crop pixels from it.

https://www.usgs.gov/data/nlcd-2016
https://www.usgs.gov/publications/conterminous-united-states-land-cover-change-patterns-2001-2016-2016-national-land
https://www.nass.usda.gov/Research_and_Science/Cropland/sarsfaqs2.php

## Six-band data evidence

Run code/16_plot_forest_break.py. Share calculations EXCLUDE background code 0
and pool pixel counts across hubs within each band. Earlier conversational
pooled forest shares mistakenly included code 0; those values are superseded.
These diagnostics and the paired-pixel inner-band audit use valid pixels only.

2018–2019 changes in percentage points:

| Band (miles) | Deciduous | Evergreen | Mixed | All forest |
|---|---:|---:|---:|---:|
| 0–25 | -0.16 | +0.62 | +0.96 | +1.41 |
| 25–50 | -0.72 | +0.75 | +1.63 | +1.66 |
| 50–75 | -2.03 | +1.04 | +2.76 | +1.78 |
| 75–100 | -2.62 | +1.04 | +3.32 | +1.75 |
| 100–125 | -3.17 | +0.92 | +3.65 | +1.40 |
| 125–150 | -3.41 | +1.02 | +3.52 | +1.13 |

The common timing, offsetting subtype shifts and 2021 all-forest decline in
every band are consistent with source/classifier effects. They do not prove
all movement is artificial or establish the fraction caused by classification.
Grouping all three forest types reduces subtype relabeling but does not
eliminate cross-boundary forest/nonforest measurement changes.

## Paired-pixel evidence and remaining work

Completed 2018–2019 paired audit: 58 hubs, 0–25-mile band only. Identical common
coverage (293,349,945 pixels). Net soybean decline: 7,730,372 pixels. Net flow
from forest to soybean: 90,702 pixels (gain); forest did not drive soybean
loss in this band. Forest/nonforest transitions can still reflect measurement
or real changes; satellite labels alone do not prove either.

New audit-forest-bands.yml examines all 58 hubs x six bands, retaining the three
forest subtypes separately. It must finish before full six-band transition
conclusions. It audits 2018–2019, not 2020–2021. Raw raster failures raise an
error; no failed requests are recoded as zero land cover.

For annual forest-conversion results use a consistent-version NLCD series and
independent validation; do not identify forest clearing from consecutive CDL
forest codes alone. Soybean results need band-specific transition checks and
stable-mask/measurement-break robustness. Year fixed effects alone do not
necessarily absorb spatially heterogeneous classification error.

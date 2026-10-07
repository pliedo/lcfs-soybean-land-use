# Research-design memo

## Question

How does California's Low Carbon Fuel Standard transmit renewable-diesel demand to soybean-producing areas outside California?

## Treatment

The treatment is a crusher-year measure of LCFS exposure:

\[
D_{it} = \sum_r w_{ir} S_{rt},
\]

where \(S_{rt}\) is a refinery-level LCFS-linked shock and \(w_{ir}\) maps each refinery to crushers using predetermined geography and alternative allocation rules.

## Estimation

The baseline is a continuous-treatment panel design with crusher-by-distance-band fixed effects and time fixed effects. The distance bands measure spatial heterogeneity; none is treated as an untreated control group.

## Planned empirical outputs

- audited pathway and capacity timeline;
- treatment-timing and anticipation diagnostics;
- event-study / dynamic effects;
- crop response by distance band;
- sensitivity to refinery--crusher allocation rules;
- crop substitution outcomes.

## Open choices to audit

- facility and pathway crosswalk;
- active-pathway and capacity timing;
- treatment date relative to planting;
- crop-share denominator and distance-band geometry;
- spatial overlap and inference.

# Route-specific soybean-oil transport cost matrix

## Evidence and boundaries
The matrix transports soybean oil from crushers to refineries, not finished fuel from refineries to California. Pathway descriptions often contain both legs. Never use a finished-fuel ocean leg to infer an oil procurement leg.

CARB Rodeo report: https://ww2.arb.ca.gov/sites/default/files/classic/fuels/lcfs/fuelpathways/comments/tier2/b0241_report.pdf
Section 2.2 describes rail or barge to a Louisiana gathering point and barge onward to Rodeo. Shipment distances are marked CBI. This supports route structure, not a named port, exact mileage, or shares. Direct rail is also represented in Rodeo pathway descriptions. Argentinian-oil ocean pathways do not establish U.S.-crusher routes.

USDA rate sources: https://www.ams.usda.gov/services/transportation-analysis/gtr-datasets
Published soybean/grain rail tariffs, inland barge rates, truck and ocean benchmarks are not soybean-oil tanker quotes. Route total dollars/ton must not be interpreted as dollars/ton-km without a corresponding distance and handling basis. Do not use cost indices as cardinal modal ratios.

## Outputs
- pathway_transport_leg_audit.csv: source text, extracted first feedstock clause, modes, foreign-origin flag. Automated parsing requires review.
- refinery_crusher_route_cost_components.csv: all 928 pairs and candidate route records. Existing network legs are retained; unmeasured legs and costs are blank.
- No numeric transport cost or ocean mileage is invented. Blank is not zero.

## Completion steps
1. Identify feasible liquid-bulk gathering terminals, distinguish Gulf river terminals from marine departure ports.
2. Calculate crusher-to-terminal rail and navigable water paths. Geodesic nearest-network connectors are access screens, not road distances or confirmed terminals.
3. Calculate marine route to the relevant California receiving terminal, including Panama routing where applicable; add terminal-to-refinery connection.
4. Calibrate fixed, pre-treatment modal freight benchmarks and handling costs. Clearly label grain-rate sensitivity separately from oil-specific quotes.
5. Compute cost = sum(mode distance * compatible mode rate) + transfer costs. Preserve documented and hypothetical routes separately.
6. Keep direct rail and Gulf-route scenarios separate unless verified shipment shares support mixing. Do not automatically minimize across hypothetical routes.
7. Convert costs into exposure weights without changing capacity timing; retain every specification, including unidentified ones.

Current networks reflect a 2026 snapshot and are not verified pre-treatment infrastructure. This limitation applies to causal interpretation.

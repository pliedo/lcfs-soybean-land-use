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

## Linehaul proxy implementation (11 October 2026)
code/28_build_route_cost_proxies.py computes network paths to an inferred candidate Louisiana gathering terminal: IMTT St Rose. The operator lists vegetable oils, rail, barge and vessel service at https://imtt.com/terminals/st-rose-la/. Coordinates (29.94556687497352, -90.33137552409985) come from its embedded address map; they are not surveyed berth coordinates. CARB does not identify this terminal. This is one transparent candidate, not an exhaustive terminal search or confirmation of procurement.

Rail and inland-waterway paths use the same cached public graphs as scripts24/25. Access is screened at10km with the user's facility mode flags. Connector distances remain geodesic screens, not actual road legs. The downstream handoff selects the southernmost connected inland node in a tight Mississippi delta box. This inferred handoff is exported for inspection. Gulf-to-California marine geometry uses searoute1.4.3, a visualization routing library, not certified navigation. The receiving sea node is not a verified refinery berth. Consequently this does not yet satisfy full feasible routing.

Fixed pre-sample calibration uses BTS Table3-21: https://www.bts.gov/archive/publications/national_transportation_statistics/table_03_21. Common-year2004 freight revenues are truck14.24, rail2.35, barge1.83 cents per short-ton-mile. Dividing each by14.24 produces a truck-equivalent-kilometre linehaul index. Truck is largely LTL general freight; all rates are broad freight proxies, not oil freight quotes, and none are oil purchase prices. No grain-specific quote is used here. Ocean rates are unavailable in this table: barge-rate multipliers0.5/1/2 are explicitly assumed sensitivities, not source-backed ocean estimates.

No handling, canal fee or unmeasured access leg is silently treated as a measured zero: the exported index explicitly excludes these components. USD/tonne costs remain unfilled. Hypothetical California Gulf routes remain labelled separately from the Rodeo-specific CARB structure. No shipment proportions are invented. Numeric linehaul proxies do not establish a completed route-specific transportation-cost matrix; remaining work includes verified marine feasibility, origin-to-transfer routes where rail/barge sequences require them, alternate candidate terminals, access legs and oil-compatible freight/transfer calibration.

Outputs: refinery_crusher_route_cost_proxies.csv (route-specific sensitivities); crusher_louisiana_terminal_network_legs.csv; modal_freight_cost_assumptions.csv; output/diagnostics/route_cost_proxy_validation.json. Original incomplete components are preserved.

## Preserved intermediate routes and source audit
Script31 adds rail to IMTT Lemont, inland waterway to IMTT St Rose, downstream Mississippi and marine to Rodeo as a separate candidate. Lemont's operator explicitly lists vegetable oils, CN rail and Illinois waterway berths: https://imtt.com/terminals/lemont-il/. Coordinates from its embedded address map:41.69282917126276,-87.95638722362305. Shortest paths are constrained to these candidate transfers; no actual shipment or optimality across all terminals is claimed. Joliet was researched but excluded from the candidate set because its page did not explicitly establish vegetable-oil handling.

CARB descriptions listing Artesia pretreatment for Cheyenne and Sinclair produce separate rail-via-Artesia alternatives. Cheyenne's truck alternative remains unresolved, rather than treating air distance as a road leg. The reviewed source audit records unspecified modes and excludes foreign-oil routes.

The 21 November2024 Artesia description starts with US soybeans sent to Monterrey for extraction, then extracted oil returned to Artesia. This is not an outbound US-crusher soybean-oil leg. Its return mode is not specified in that clause; flag it separately, retain its policy approval history, and do not use it to assert a direct crusher-oil route.

USDA Grain Transportation Report, March5 2015, table1 https://apps.ams.usda.gov/SearchReports/Documents/stelprdc5110719.pdf reports fourth-quarter2014 Gulf-to-Japan ocean freight44USD/metric tonne. This is a grain proxy, not oil freight. A per-km ocean calibration additionally requires an inferred Japanese receiving port and route length; it has not yet replaced the explicitly assumed ocean/barge sensitivities. Farm value is never used as transport cost.

Diagnostics script30 preserves all baselines while evaluating predefined hub and refinery influence, period windows, trends, lead diagnostics and denominator support. Full fixed-pixel support and forest-class transitions cannot be inferred from equal denominator counts alone.

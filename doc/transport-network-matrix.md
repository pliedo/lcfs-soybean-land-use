# Alternative transport matrix

The pipeline builds928 physical-refinery–crusher pairs (16 plants ×58 retained elevator hubs), preserving original road and air distances and researcher railfront/riverfront/oceanfront classifications. Rail and water distances are computed from connected graph paths, not arbitrary mode discounts. Disconnected routes remain missing, not zero.

Rail: official FRA/BTS North American Rail Network,2026 update. Only active main/industrial/other/siding/yard/ferry classesM,I,O,S,Y,F enter. Abandoned,out-of-service,removed,trail and transit-only classes are excluded. US links and US nodes are used; foreign/transborder routes are not available in this version. Node IDs preserve topological connections, avoiding false joins at geometric crossings. Parallel segments use the shortest edge, not their sum. Edges lacking US endpoint nodes are reported and omitted. Distances use the sourceKM field.

Water: official USDOT_BTS National Waterway Network Lines, published2025. Only inlandGEO_CLASS='I' links enter. Open-ocean shipping, Panama routes and combined rail–barge transfer routes are not represented. Edge lengths are calculated along geometry geodesically, avoiding an unsupported assumption about source length units. Graph paths are undirected; carrier restrictions,directional routing,lock delays and freight rates are not modeled.

Access: each facility attaches to the nearest active graph node, with a separately reported straight-line connector. This is a conservative node attachment, not nearest-track projection; a facility on a long segment can have a distant nearest endpoint. Flags screen both connectors at5km or10km and require the crusher's corresponding manual access flag. Refinery access is geometric proximity only, not verified unloading capability. A connected graph path does NOT establish a real procurement relationship. Do not silently use all un-screened routes as feasible shipments.

The current network snapshots are exploratory geographic alternatives, not historical infrastructure panels. Pre-policy network versions or evidence of stable routes are needed for a predetermined exposure interpretation. Manual access classification dates are also unverified. Network metadata and cacheSHA hashes are recorded. Downloads are checkpointed and cached; raw network geometry is not committed to the repo.

Official sources:
- https://services.arcgis.com/xOi1kZaI0eWDREZv/ArcGIS/rest/services/NTAD_North_American_Rail_Network_Lines/FeatureServer/0
- https://services.arcgis.com/xOi1kZaI0eWDREZv/ArcGIS/rest/services/NTAD_North_American_Rail_Network_Nodes/FeatureServer/0
- https://www.arcgis.com/sharing/rest/content/items/06037f2b23ff401aa1d379c2632a58f6?f=json (ownerUSDOT_BTS)
- https://services7.arcgis.com/n1YM8pTrFmm7L4hs/ArcGIS/rest/services/Waterway_Networks/FeatureServer/1

Important prior-cutoff check: none of the58 retained crushers is within1000 road miles of the four mapped California plants (AltAirParamount,ChevronElSegundo,Martinez,PhillipsRodeo). Thus the broad hard-cutoff specification removes those four plants' exposure entirely. It should not be interpreted as an independently verified sourcing model or selected because its coefficient is positive.

Outputs when successful: data/clean/refinery_crusher_transport_matrix.csv and output/diagnostics/transport_network_validation.json. Workflow build-transport-matrix.yml runs both stages and commits only after success. It does not automatically replace the baseline weights or rerun regressions with unverified access assumptions.

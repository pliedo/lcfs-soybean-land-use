# Audit of negative distance-weighted estimates (2026-10-10)

Baseline: exponential road-distance decay with 150-mile scale, nearest crusher normalized to 1; planting-aligned eligible capacity; six separate rings; crusher and year FE. This audit does not select a preferred model by coefficient sign.

## Computation and joins

Physical-plant contributions sum exactly to each crusher-year exposure. Outcome joins are many-to-one; aliases are consolidated before summing; lags and leads stay within crusher. Full dummy-variable OLS independently matched baseline coefficients and crusher-clustered SE to 1e-10. Original saved road matrices are identical; road-versus-air distances are consistent after the reviewed Sinclair representative-coordinate choice. These checks do not establish actual procurement links or validate every original geocode.

## Where the negative covariance comes from

The exact TWFE coefficient is decomposed using residualized exposure and outcome: sum(x_tilde*y_tilde)/sum(x_tilde^2). Plant contributions use each plant's residualized exposure; crusher/year contributions use subsets of observation products, holding the full-model denominator fixed. These are algebraic contributions, NOT plant-specific causal effects. Leave-one-out estimates separately re-estimate the complete model after each omission.

In 25–50 miles, Diamond Green Diesel Norco contributes -0.0364 pp/100 MGY and Marathon Dickinson -0.0270 to the overall -0.0952 coefficient. In 50–75 miles their contributions are -0.0344 and -0.0187 to -0.0921. Bunge Destrehan (hub51) and ADM Goodland (hub53) together contribute -0.0540 and -0.0564 respectively (about 57% and 61% of the net negative coefficients). Because other contributions may offset, these percentages are not shares of absolute influence.

DGD Norco's nearest crusher is Destrehan: original road distance 11.8 km, straight-line 7.5 km, weight1. Its next listed crusher is 635.9 km away with weight0.075. Dickinson's nearest listed crusher is Velva ND, 290.0 road km away, also weight1 because of relative normalization. This illustrates why nearest-normalized exposure can be concentrated or give full weight to a distant crusher. Proximity does not establish sourcing; actual procurement still needs validation. Destrehan's soybean share is very low and falls from 0.517% to 0.338% in 25–50 miles and from 0.630% to 0.338% in 50–75 miles (2014–2024). Goodland also has very low shares with modest declines. National soybean expansion need not imply expansion in these specific catchments.

Omitting each plant, crusher or year individually produces no positive significant coefficient in the six baseline ring regressions. In the two main negative rings, all individual omission estimates remain negative. Omitting 2024 makes estimates more negative: -0.211 and -0.160 for 25–50 and 50–75. Therefore 2024 is influential but is not solely responsible for the negative sign.

## Capacity history: actual discrepancy found

The source compilation assigns Norco 290 MGY back to years before 2020. A November 2017 company release instead states 160 MGY while expansion to275 was underway. Expansion completed August2018 according to Valero's timeline. Thus carrying a later NREL snapshot backward is not a verified historical capacity series. Farmdoc's Norco337 in2020 and982 from2021 also differ from company-reported290 before the2021 expansion and700 after Q4 2021. Farmdoc expressly discusses the982-versus690 discrepancy; this is a source disagreement, not a proven duplicate with PortArthur.

An explicit company-history sensitivity uses Norco pre-plant dose160 for2017–18,275 for2019,290 for2021,700 for2022–24, and PortArthur470 instead of537 in2024. Other years/plants retain the compilation; this is targeted sensitivity, not a fully rebuilt company series. It preserves negative estimates: -0.1035 (p0.0098) in25–50 and -0.0984 (p0.0086) in50–75. Original source values remain unchanged.

Sources:
- https://www.sec.gov/Archives/edgar/data/916540/000091654017000030/exh993-pressrelease.htm (Nov7,2017;160→275)
- https://www.valero.com/sites/default/files/valero-documents/2024-04/Basics_of_Renewable_Diesel_-_March_2020-2.pdf (Aug2018 expansion)
- https://investorvalero.com/news/news-details/2022/Valero-Energy-Reports-2021-Fourth-Quarter-and-Full-Year-Results/default.aspx (700 after2021 optimization)
- https://www.sec.gov/Archives/edgar/data/916540/000091654026000008/ex991dgdfy2025fin.htm (Norco700,PortArthur470)
- https://farmdocdaily.illinois.edu/2023/03/overview-of-the-production-capacity-of-u-s-renewable-diesel-plants-through-december-2022.html (explicit Norco capacity discrepancy)

## Approval/capacity timing and common samples

Replacing previous-year capacity with current-year capacity, using either May1 approval eligibility or year-end eligibility, preserves negative signs in all six full-period regressions. For25–50/50–75 the current-capacity May1 estimates are -0.0777/-0.0750; year-end calendar estimates -0.0504/-0.0520. Delaying approval eligibility to the following crop year also preserves negative signs. Approval dates were not changed or assumed retroactive.

All current/lag/lead specifications can be compared on2017–2021 (2014–2024 data supports±3). This short common window yields positive current and lag1/lag2 estimates in the first three bands. Lag2 in50–75 is +0.2303 pp/100 MGY (p0.0184); most other positive estimates are insignificant. This is an exploratory period-sensitivity check, not a selected causal result. The window excludes the major2022–2024 shocks and the2014–2016 zero-dose comparison period. Full-period statements about no positive significant single-lag coefficients do not extend to this different sample.

## 2025 CDL availability

USDA released2025 CDL on February27,2026. National downloads include native10m (9.8GB compressed) and resampled30m (1.9GB compressed). The2025 release also changes ancillary noncrop inputs to NLCD2024 and2023 tree canopy. Therefore adding2025 requires resolution harmonization and a new measurement-break check, particularly for forest/noncrop shares. Outcomes have NOT yet been extracted for2025; existing regressions end2024. Treatment data also end2024, so a2025 capacity/eligibility update is necessary rather than blindly carrying all2024 values forward.

Sources: https://www.nass.usda.gov/Research_and_Science/Cropland/SARS1a.php ; https://data.nass.usda.gov/Research_and_Science/Cropland/Release/ ; https://data.nass.usda.gov/Research_and_Science/Cropland/sarsfaqs2.php

## Files and next work

code19 creates covariance decomposition, leave-one-out coefficients, same-sample timing checks and plant timing history. code20 creates the explicit DGD company-capacity sensitivity. Outputs are under output/tables/exposure_*.csv. The statistical sign is not an arithmetic bug exposed by these checks; source history, geographic concentration and substantial period sensitivity remain material concerns. Next: reconstruct historical capacity with dates, verify actual soybean procurement and approval-history completeness, inspect regional weather/crop shocks, extend2025 outcomes with matching treatment data, and improve spatial/shared-shock inference. No causal expansion or contraction conclusion is justified yet.

# Transport-cost construction and allocation sensitivity

This separates matrix construction from the weight function applied to it. Existing inverse-square weights measure potential exposure but do not sum to one by refinery. A new normalized inverse-square rule uses f(c)=(50/(c+50))^2 and w(h,j)=f(c(h,j))/sum_h f(c(h,j)); exponential sum-to-one already existed. Both preserve each refinery's total capacity when assigning exposure across eligible crushers. These allocations remain assumptions, not measured procurement shares. The 50 and 100 baseline truck-equivalent-km sensitivity scales remain fixed across matrix definitions.

## Cost definitions

Thirteen matrices: baseline; truck, rail, barge or ocean rates multiplied independently by 0.5 or 2; assumed $5 or $15 per tonne per modeled intermodal transfer; exclusion of Lemont transfer candidates; exclusion of St Rose truck-to-rail candidates. Multipliers and handling charges are transparent researcher-assumed stress tests, not observed oil freight quotes. Original sourced broad-freight/grain-ocean rates and mode-specific distance components are retained. No soybean-oil purchase price is used.

Routes are reselected after repricing within the existing documented-mode candidate set, including refinery-specific required intermediates. Rodeo routes are not generalized to all California facilities. No new routes or shipment proportions are invented. Costs use the fixed baseline truck-rate numeraire, so changing truck prices does not silently redefine decay units. Unknown last-mile, terminal and canal costs remain excluded except the explicitly assumed intermodal-transfer charges. Existing 2026 network snapshots and inferred terminal geometry remain fixed; this is not independent network or terminal validation. Each of the 13 definitions retains numeric candidate costs for all 928 pairs. Baseline candidate costs match the committed original matrix.

## Estimation and validation

Eight weights (original seven plus normalized inverse-square), both physical-onset and disputed-site-exclusion dose scenarios, current/lag1/lag2/distributed0–2, six heterogeneous ring slopes, four outcomes, crusher-ring and ring-year FE, crusher-clustered covariance. Cumulative 0–50 and 0–75 predictions are computed for an equal-weight average of 16 locations plus Norco, Rodeo and Dickinson. Log coefficients are exported but not nonlinearly aggregated to acres. 29,952 coefficient rows and 19,968 scenario rows; zero unidentified models. Main baseline average predictions match prior estimates within 6.5e-10 acres and standard errors within 2.5e-10 acres.

## Findings: equal-location average +100 million gallons/year

Normalized inverse-square, distributed current/lag1/lag2, cumulative 0–75: all-land-share model implies +18,864 acres, 95% CI [6,383,31,345], p=.00372. Direct-acreage model gives +13,147 [-1,518,27,813], p=.0779. Cropland-share-derived acreage change is -34,940, p=3.6e-9; the favorable all-land-share result must not be described as a generally positive outcome across definitions.

Normalized inverse-square all-land-share predictions remain positive under all 13 cost definitions and nominally significant at 5% under 12. Range: +10,945 to +33,732 acres. Halving rail rates increases the estimate but makes it imprecise, p=.243. Direct-acreage predictions stay positive, but nominal significance depends on cost assumptions: doubling rail cost gives +9,353, p=.00397; halving ocean cost gives +13,846, p=.0436; baseline is only significant at 10%. These are sensitivity findings, not grounds to prefer the assumptions that produce significance.

Unnormalized inverse-square distributed all-land-share-derived acres: baseline +12,696 [4,933,20,458]; range +4,496 to +36,514; nominally significant in 12/13 matrices. Its direct-acreage baseline +6,145 is uncertain. Preserve this original result separately from the normalized rule.

Nearest allocation lag2 direct acres: baseline cumulative 0–50 +3,118, range +3,118 to +3,665, nominally significant in all 13 matrices. Cumulative 0–75 baseline +4,499, range +4,499 to +5,408, significant in 10/13 matrices. Three matrices change the selected receiving crusher and reduce precision; unchanged winners yield identical estimates, not independent confirmations.

Some original broader allocation rules acquire nominal positive significance under particular perturbed matrices. Therefore earlier statements that five weights produced no significant positive baseline result are baseline-specific, not universal across cost assumptions. The complete grid and stability table preserve all outcomes, signs and uncertainty. Multiple testing is unadjusted. Share-versus-acre and cropland-denominator differences remain material; lead/timing concerns from earlier diagnostics are not resolved by these tests. No results are established causal LCFS effects.

Reproduce: code/44_transport_matrix_sensitivity.py, code/45_estimate_transport_matrix_sensitivity.py, code/46_summarize_matrix_sensitivity.py. Cost matrices, coefficients and scenarios are committed as compressed CSVs; assumptions, equal-location averages and stability summaries are ordinary CSVs. A GitHub workflow reproduces the calculations without requesting any new CDL rasters.

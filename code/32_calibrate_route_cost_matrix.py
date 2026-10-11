"""Fixed 2013-price transport proxies; grain ocean and broad-freight domestic proxies explicit."""
import json
from pathlib import Path
import numpy as np,pandas as pd
import searoute
R=Path(__file__).resolve().parents[1];C=R/"data/clean"
BTS="https://www.bts.gov/archive/publications/national_transportation_statistics/table_03_21"
USDA="https://apps.ams.usda.gov/SearchReports/Documents/stelprdc5110719.pdf"
def main():
 v=json.loads((R/"output/diagnostics/route_cost_proxy_validation.json").read_text());exit=v["delta_exit"]
 # Representative Tokyo Bay endpoint, researcher-selected within Japan benchmark region.
 japan=searoute.searoute([exit["lon"],exit["lat"]],[140.1,35.6],units="km")
 km=float(japan["properties"]["length"]);ocean=55.96/km
 # BTS total finished-goods PPI2004=125,2013=165; generic price-level conversion,
 # not a freight-specific deflator. Fixed for all planting years, no outcome-tuned rates.
 deflator=165/125
 rates={"truck":14.24/100/0.90718474/1.609344*deflator,"rail":2.35/100/0.90718474/1.609344*deflator,"barge":1.83/100/0.90718474/1.609344*deflator,"ocean":ocean}
 assumptions=[]
 for mode,rate in rates.items():
  assumptions.append(dict(mode=mode,usd2013_per_metric_tonne_km=rate,rate_relative_to_truck=rate/rates["truck"],source=USDA if mode=="ocean" else BTS,observed_rate_year=2013 if mode=="ocean" else 2004,benchmark="Gulf to Japan fourth-quarter2013 grain ocean55.96USD/metric tonne" if mode=="ocean" else "BTS broad freight revenue per short-ton-mile",grain_proxy=mode=="ocean",oil_quote=False,price_conversion="none" if mode=="ocean" else "PPI165/125; general finished-goods proxy, not freight deflator",distance_status="inferred Tokyo Bay representative endpoint marine path" if mode=="ocean" else "published ton-mile rate"))
 pd.DataFrame(assumptions).to_csv(C/"calibrated_modal_freight_proxy_rates.csv",index=False)
 a=pd.read_csv(C/"refinery_crusher_route_cost_proxies.csv");a=a[a.ocean_to_barge_rate_assumption==1].copy()
 b=pd.read_csv(C/"documented_intermediate_route_proxies.csv").rename(columns={"eligible":"access_screen_eligible"})
 b["route_support"]=b.support
 allroutes=pd.concat([a,b],ignore_index=True,sort=False)
 rows=[]
 for _,r in allroutes.iterrows():
  required={"direct_truck":["truck"],"direct_rail":["rail"],"inland_barge":["barge"],"rail_gulf_marine":["rail","barge","ocean"],"river_gulf_marine":["barge","ocean"],"rail_Lemont_barge_StRose_marine_Rodeo":["rail","barge","ocean"],"rail_via_Artesia_pretreatment":["rail"]}[r.route]
  for mult in ([0.5,1,2] if "ocean" in required else [1]):
   legs=[r.get(mode+"_km",np.nan) for mode in required]
   cost=sum(float(r[mode+"_km"])*rates[mode]*(mult if mode=="ocean" else 1) for mode in required) if all(pd.notna(x) and np.isfinite(x) for x in legs) else np.nan
   q=r.to_dict();q.update(ocean_rate_multiplier=mult,linehaul_cost_proxy_usd2013_per_tonne=cost,cost_proxy_truck_equivalent_km=cost/rates["truck"] if pd.notna(cost) else np.nan,cost_basis="fixed2013 price-level proxy; broad domestic freight and grain ocean",cost_exclusions="unmeasured access legs, transfer handling, canal fee; NOT total delivered shipping quote")
   rows.append(q)
 out=pd.DataFrame(rows)
 zero=out.linehaul_cost_proxy_usd2013_per_tonne.eq(0)
 # Shared nearest network nodes do not establish a free transport route.
 out.loc[zero,["linehaul_cost_proxy_usd2013_per_tonne","cost_proxy_truck_equivalent_km"]]=np.nan
 out.loc[zero,"cost_status"]="zero_network_leg_access_cost_unmeasured_not_free_route"
 out.loc[zero,"access_screen_eligible"]=False
 assert out[["hub_id","physical_plant_id"]].drop_duplicates().shape[0]==928
 assert (out.linehaul_cost_proxy_usd2013_per_tonne.dropna()>0).all()
 out.to_csv(C/"refinery_crusher_calibrated_route_cost_proxies.csv",index=False)
 # Inventory never silently replaces an infeasible documented mode with hypothetical trucking.
 audit=pd.read_csv(C/"pathway_transport_leg_audit_reviewed.csv")
 p=pd.read_csv(C/"refinery_crusher_transport_matrix.csv")
 inventory=[]
 for _,pair in p.iterrows():
  z=out[(out.hub_id==pair.hub_id)&(out.physical_plant_id==pair.physical_plant_id)&(out.ocean_rate_multiplier==1)]
  modes=set("|".join(audit.loc[(audit.physical_plant_id==pair.physical_plant_id)&audit.US_crusher_oil_route_evidence.astype(str).str.lower().eq("true"),"feedstock_modes"].fillna("")).split("|"))
  eligible=z[z.access_screen_eligible.astype(str).str.lower().eq("true")].copy()
  allowed=eligible[(eligible.route.eq("direct_rail")&("rail" in modes))|(eligible.route.eq("direct_truck")&("truck" in modes))|(eligible.route.eq("inland_barge")&("barge" in modes))]
  if "Rodeo" in pair.physical_plant_id:allowed=pd.concat([allowed,eligible[eligible.route.isin(["rail_gulf_marine","river_gulf_marine","rail_Lemont_barge_StRose_marine_Rodeo"])]])
  best=allowed.dropna(subset=["linehaul_cost_proxy_usd2013_per_tonne"]).sort_values("linehaul_cost_proxy_usd2013_per_tonne")
  truck=z[z.route=="direct_truck"]
  inventory.append(dict(hub_id=pair.hub_id,physical_plant_id=pair.physical_plant_id,documented_mode_candidate_count=len(best),lowest_documented_candidate_linehaul_proxy=best.linehaul_cost_proxy_usd2013_per_tonne.iloc[0] if len(best) else np.nan,lowest_candidate_route=best.route.iloc[0] if len(best) else "",hypothetical_road_linehaul_proxy=truck.linehaul_cost_proxy_usd2013_per_tonne.iloc[0] if len(truck) else np.nan,status="documented_mode_candidate_proxy_not_verified_procurement" if len(best) else "no_access_eligible_documented_mode_candidate_do_not_zero"))
 inv=pd.DataFrame(inventory);assert len(inv)==928;assert not inv.duplicated(["hub_id","physical_plant_id"]).any()
 inv.to_csv(C/"route_cost_pair_coverage_inventory.csv",index=False)
 diag={"pairs":928,"numeric_route_costs":int(out.linehaul_cost_proxy_usd2013_per_tonne.notna().sum()),"documented_mode_candidate_pairs":int(inv.lowest_documented_candidate_linehaul_proxy.notna().sum()),"unresolved_documented_candidate_pairs":int(inv.lowest_documented_candidate_linehaul_proxy.isna().sum()),"rates":rates,"grain_ocean_reference_usd_per_tonne":55.96,"Japan_reference_endpoint":[140.1,35.6],"Japan_reference_km":km,"marine_reference_geometry":japan["geometry"],"completion_status":"calibrated linehaul proxies computed; full access/handling feasibility and all-pair documented routing remain unresolved"}
 (R/"output/diagnostics/calibrated_route_cost_validation.json").write_text(json.dumps(diag,indent=2))
 print({k:v for k,v in diag.items() if k!="marine_reference_geometry"},flush=True)
if __name__=="__main__":main()

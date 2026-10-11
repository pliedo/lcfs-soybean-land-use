"""Truck-to-liquid-terminal alternatives for origins without on-site rail; retain exclusions."""
import importlib,json,time,urllib.request
import numpy as np,pandas as pd
m=importlib.import_module("31_add_constrained_transfer_routes");R=m.R;C=m.C
OSRM="https://router.project-osrm.org/route/v1/driving/"
def road(lon,lat,tlon,tlat):
 url=OSRM+f"{lon},{lat};{tlon},{tlat}?overview=false&alternatives=false&steps=false"
 for k in range(3):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"LCFS-research-route-proxy/1.0"}),timeout=60) as f:d=json.load(f)
   if d.get("code")!="Ok":raise RuntimeError(d)
   return d["routes"][0]["distance"]/1000,[x.get("distance") for x in d["waypoints"]],url
  except Exception:
   if k==2:raise
   time.sleep(2**k)
def main():
 inventory=pd.read_csv(C/"route_cost_pair_coverage_inventory.csv")
 missing=inventory[inventory.lowest_documented_candidate_linehaul_proxy.isna()]
 hubs=sorted(missing.hub_id.unique());assert set(hubs)<=set([7,9,34]),"New unreviewed origin requires route audit"
 h=pd.read_excel(R/"data/raw/soy_crushing_facilities.xlsx").set_index("number")
 cross=pd.read_csv(C/"lcfs_physical_plant_crosswalk.csv").drop_duplicates("physical_plant_id").set_index("physical_plant_id")
 plants=sorted(missing.physical_plant_id.unique());pc=np.array([list(map(float,cross.loc[p,"coordinate_used"].split(","))) for p in plants])
 terminals=np.array([[t["lat"],t["lon"]] for t in m.TERMINALS]);rail,tc,rc=m.paths("rail",terminals,pc)
 rates=pd.read_csv(C/"calibrated_modal_freight_proxy_rates.csv").set_index("mode").usd2013_per_metric_tonne_km.to_dict()
 audit=pd.read_csv(C/"pathway_transport_leg_audit_reviewed.csv")
 roads=[];routes=[]
 for hub in hubs:
  for j,t in enumerate(m.TERMINALS):
   km,snaps,url=road(h.loc[hub,"lat"],h.loc[hub,"lon"],t["lon"],t["lat"])
   roads.append(dict(hub_id=hub,terminal=t["name"],road_km=km,origin_road_snap_m=snaps[0],terminal_road_snap_m=snaps[1],url=url,road_status="OSRM driving route between snapped address points; not truck clearance or site-gate verification"))
   for i,plant in enumerate(plants):
    if not ((missing.hub_id==hub)&(missing.physical_plant_id==plant)).any():continue
    modes="|".join(audit.loc[audit.physical_plant_id==plant,"feedstock_modes"].fillna(""))
    if "rail" not in modes:continue
    rk=float(rail[i,j]);eligible=bool(np.isfinite(rk) and max(tc[j],rc[i])<=10 and max(snaps)<=1000)
    cost=km*rates["truck"]+rk*rates["rail"]
    routes.append(dict(hub_id=hub,physical_plant_id=plant,route="truck_"+t["name"].replace("IMTT ","").replace(" ","")+"_"+"rail",truck_km=km,rail_km=rk,barge_km=0,ocean_km=0,terminal=t["name"],access_screen_eligible=eligible,ocean_rate_multiplier=1,linehaul_cost_proxy_usd2013_per_tonne=cost,cost_proxy_truck_equivalent_km=cost/rates["truck"],route_support="inferred truck access to publicly documented liquid-bulk rail terminal; refinery rail mode documented; NOT observed shipment",cost_status="linehaul proxy; terminal handling and site access fees excluded",cost_exclusions="terminal handling and site access fees; truck restrictions unverified"))
   time.sleep(1)
 routes=pd.DataFrame(routes);pd.DataFrame(roads).to_csv(C/"nonrail_origin_terminal_road_routes.csv",index=False);routes.to_csv(C/"nonrail_origin_transfer_cost_proxies.csv",index=False)
 existing=pd.read_csv(C/"refinery_crusher_calibrated_route_cost_proxies.csv")
 combined=pd.concat([existing,routes],ignore_index=True,sort=False)
 combined.to_csv(C/"refinery_crusher_transport_cost_matrix.csv",index=False)
 eligible=combined[combined.access_screen_eligible.astype(str).str.lower().eq("true")&combined.linehaul_cost_proxy_usd2013_per_tonne.notna()]
 coverage=eligible[["hub_id","physical_plant_id"]].drop_duplicates()
 assert combined[["hub_id","physical_plant_id"]].drop_duplicates().shape[0]==928
 resolved=set(map(tuple,routes.loc[routes.access_screen_eligible,["hub_id","physical_plant_id"]].drop_duplicates().to_numpy()))
 still=[(int(r.hub_id),r.physical_plant_id) for _,r in missing.iterrows() if (r.hub_id,r.physical_plant_id) not in resolved]
 v={"all_pairs":928,"new_transfer_alternatives":len(routes),"eligible_new_alternatives":int(routes.access_screen_eligible.sum()),"unresolved_previous_pairs":still,"OSRM_source":OSRM,"candidate_terminals":m.TERMINALS,"completion_status":"numeric linehaul transport proxy; inferred terminals, not actual procurement; excludes handling; road truck restrictions unverified"}
 (R/"output/diagnostics/nonrail_transfer_validation.json").write_text(json.dumps(v,indent=2));print(v,flush=True)
if __name__=="__main__":main()

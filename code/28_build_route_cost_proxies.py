"""Modelled freight cost proxies, not oil freight quotes or procurement shares."""
from pathlib import Path
import importlib,json
import numpy as np,pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
import searoute
m=importlib.import_module("24_build_transport_network_matrix");R=m.R;C=R/"data/clean"
BTS="https://www.bts.gov/archive/publications/national_transportation_statistics/table_03_21"
TERMINAL="https://imtt.com/terminals/st-rose-la/"
# Coordinates from operator's embedded address map: point at facility, not surveyed berth.
terminal=np.array([[29.94556687497352,-90.33137552409985]])
def graph(kind):
 if kind=="rail":
  f=m.features(m.RAIL,"COUNTRY='US' AND NET IN ('M','I','O','S','Y','F')","OBJECTID,FRFRANODE,TOFRANODE,KM,NET",False,"rail_active_edges")
  nf=m.features(m.NODES,"COUNTRY='US'","OBJECTID,FRANODEID",True,"rail_us_nodes")
  nodes={x["attributes"]["FRANODEID"]:[x["geometry"]["x"],x["geometry"]["y"]] for x in nf}
  links=[(x["attributes"]["FRFRANODE"],x["attributes"]["TOFRANODE"],x["attributes"]["KM"]) for x in f]
 else:
  w=importlib.import_module("25_add_waterway_network_matrix")
  f=m.features(w.WATER,"GEO_CLASS='I'","OBJECTID,ANODE,BNODE,DIR,GEO_CLASS,LINKTYPE",True,"water_inland_edges");nodes={};links=[]
  for x in f:
   paths=x.get("geometry",{}).get("paths",[])
   if not paths:continue
   length=0
   for p in paths:
    p=np.array(p)[:,:2];v=m.xyz(p[:,1],p[:,0]);length+=m.gc(v[:-1],v[1:]).sum()
   a=x["attributes"];nodes.setdefault(a["ANODE"],paths[0][0][:2]);nodes.setdefault(a["BNODE"],paths[-1][-1][:2]);links.append((a["ANODE"],a["BNODE"],length))
 e=pd.DataFrame(links,columns=["a","b","km"]).dropna();e=e[(e.km>0)&e.a.isin(nodes)&e.b.isin(nodes)]
 e["lo"]=e[["a","b"]].min(axis=1);e["hi"]=e[["a","b"]].max(axis=1);e=e.groupby(["lo","hi"],as_index=False).km.min()
 n=pd.DataFrame.from_dict(nodes,orient="index",columns=["lon","lat"]).loc[sorted(set(e.lo)|set(e.hi))]
 lookup={v:i for i,v in enumerate(n.index)};a=e.lo.map(lookup).to_numpy();b=e.hi.map(lookup).to_numpy()
 g=csr_matrix((np.r_[e.km,e.km],(np.r_[a,b],np.r_[b,a])),shape=(len(n),len(n)))
 return n,g
def paths_to_terminal(kind,h):
 n,g=graph(kind);nn=m.xyz(n.lat.to_numpy(),n.lon.to_numpy());tree=cKDTree(nn)
 hh=m.xyz(h.lon.to_numpy(),h.lat.to_numpy());tt=m.xyz(terminal[:,0],terminal[:,1])
 _,hi=tree.query(hh);_,ti=tree.query(tt);dist=dijkstra(g,directed=False,indices=ti[0])
 out=pd.DataFrame({"hub_id":h.number.astype(int),"network_km":dist[hi],"origin_connector_geodesic_km":m.gc(hh,nn[hi]),"terminal_connector_geodesic_km":m.gc(tt,nn[ti])[0]})
 out["mode"]=kind;out["terminal"]="IMTT St Rose candidate";out["terminal_status"]="inferred candidate not CARB identified"
 # Select downstream Mississippi exit within a tight delta bounding box; exclude disconnected nodes.
 if kind=="water":
  candidates=np.flatnonzero((n.lon.to_numpy()>-89.5)&(n.lon.to_numpy()<-89)&(n.lat.to_numpy()>28.8)&(n.lat.to_numpy()<29.2)&np.isfinite(dist))
  if not len(candidates):raise RuntimeError("No connected Mississippi delta exit in search box")
  exit_i=candidates[np.argmin(n.lat.to_numpy()[candidates])]
  return out,{"lat":float(n.lat.iloc[exit_i]),"lon":float(n.lon.iloc[exit_i]),"river_terminal_to_exit_km":float(dist[exit_i]),"selection":"southernmost connected inland endpoint in Mississippi delta box; inferred marine handoff"}
 return out,None
def main():
 h=pd.read_excel(R/"data/raw/soy_crushing_facilities.xlsx");h=h[(h.type.str.lower().str.strip()=="elevator")&(h.bankrupt.fillna(0)==0)].sort_values("number")
 rail,_=paths_to_terminal("rail",h);water,exit=paths_to_terminal("water",h)
 legs=pd.concat([rail,water]);legs.replace([np.inf,-np.inf],np.nan).to_csv(C/"crusher_louisiana_terminal_network_legs.csv",index=False)
 comp=pd.read_csv(C/"refinery_crusher_route_cost_components.csv")
 cross=pd.read_csv(C/"lcfs_physical_plant_crosswalk.csv").drop_duplicates("physical_plant_id").set_index("physical_plant_id")
 pair=pd.read_csv(C/"refinery_crusher_transport_matrix.csv").set_index(["hub_id","physical_plant_id"])
 marine={}
 for plant in comp.loc[comp.route.str.contains("marine"),"physical_plant_id"].unique():
  lat,lon=map(float,cross.loc[plant,"coordinate_used"].split(","))
  route=searoute.searoute([exit["lon"],exit["lat"]],[lon,lat],units="km")
  marine[plant]={"km":route["properties"]["length"],"geometry":route["geometry"],"status":"searoute geometric proxy; nearest sea endpoint; receiving berth and navigation feasibility unverified"}
 rates=pd.DataFrame([dict(mode=mode,benchmark_year=2004,cents_per_short_ton_mile=v,truck_equivalent_cost_per_km=v/14.24,source=BTS,qualification="broad freight revenue proxy; truck mostly LTL; not soybean oil quote") for mode,v in [("truck",14.24),("rail",2.35),("barge",1.83)]])
 rates.to_csv(C/"modal_freight_cost_assumptions.csv",index=False)
 rail=rail.set_index("hub_id");water=water.set_index("hub_id");rows=[]
 for _,row in comp.iterrows():
  p=pair.loc[(row.hub_id,row.physical_plant_id)];r=row.to_dict();r.update(terminal="",connector_status="geodesic access screens, not actual road legs")
  if "marine" in row.route:
   origin=rail.loc[row.hub_id] if row.route.startswith("rail") else water.loc[row.hub_id]
   mode="rail_km" if row.route.startswith("rail") else "barge_km"
   r[mode]=origin.network_km;r["barge_km"]=exit["river_terminal_to_exit_km"]+(origin.network_km if row.route.startswith("river") else 0)
   r["ocean_km"]=marine[row.physical_plant_id]["km"];r["terminal"]="IMTT St Rose inferred"
   r["origin_access_geodesic_km"]=origin.origin_connector_geodesic_km
   eligible=bool(np.isfinite(origin.network_km) and origin.origin_connector_geodesic_km<=10 and origin.terminal_connector_geodesic_km<=10 and (p.crusher_railfront==1 if row.route.startswith("rail") else p.crusher_riverfront==1))
  elif row.route=="direct_rail":eligible=bool(p.rail_screen_10km);r["origin_access_geodesic_km"]=p.crusher_rail_connector_km
  elif row.route=="inland_barge":eligible=bool(p.water_screen_10km);r["origin_access_geodesic_km"]=p.crusher_water_connector_km
  else:eligible=bool(pd.notna(row.truck_km));r["origin_access_geodesic_km"]=0
  r["access_screen_eligible"]=eligible
  # No fictitious connector road costs; index is an explicitly incomplete linehaul proxy.
  for ocean_mult in ([0.5,1,2] if "marine" in row.route else [1]):
   q=r.copy();q["ocean_to_barge_rate_assumption"]=ocean_mult
   q["cost_proxy_truck_equivalent_km"]=sum(float(q.get(k,0) or 0)*v for k,v in [("truck_km",1),("rail_km",2.35/14.24),("barge_km",1.83/14.24),("ocean_km",ocean_mult*1.83/14.24)] if pd.notna(q.get(k)))
   required={"direct_rail":["rail_km"],"direct_truck":["truck_km"],"inland_barge":["barge_km"],"rail_gulf_marine":["rail_km","barge_km","ocean_km"],"river_gulf_marine":["barge_km","ocean_km"]}[row.route]
   if not all(pd.notna(q.get(k)) and np.isfinite(q[k]) for k in required):q["cost_proxy_truck_equivalent_km"]=np.nan
   q["cost_status"]="linehaul_proxy_excludes_unmeasured_access_handling_and_canal_costs"
   rows.append(q)
 out=pd.DataFrame(rows);assert out[["hub_id","physical_plant_id"]].drop_duplicates().shape[0]==928
 assert (out.cost_proxy_truck_equivalent_km.dropna()>=0).all()
 out.to_csv(C/"refinery_crusher_route_cost_proxies.csv",index=False)
 v={"pairs":928,"route_scenarios":len(out),"numeric_linehaul_proxies":int(out.cost_proxy_truck_equivalent_km.notna().sum()),"access_eligible":int(out.access_screen_eligible.sum()),"terminal_source":TERMINAL,"terminal_coordinates":terminal.tolist(),"delta_exit":exit,"marine_routes":marine,"completion_status":"partial: linehaul proxies computed; actual access, feasible marine verification, handling and oil freight calibration outstanding"}
 (R/"output/diagnostics/route_cost_proxy_validation.json").write_text(json.dumps(v,indent=2));print({k:v[k] for k in ["pairs","route_scenarios","numeric_linehaul_proxies","access_eligible","completion_status"]},flush=True)
if __name__=="__main__":main()

"""Documented intermediate locations with inferred terminal choices; alternatives separate."""
import importlib,json
import numpy as np,pandas as pd
from scipy.spatial import cKDTree
from scipy.sparse.csgraph import dijkstra
m=importlib.import_module("28_build_route_cost_proxies");R=m.R;C=m.C
TERMINALS=[dict(name="IMTT Lemont",lat=41.69282917126276,lon=-87.95638722362305,source="https://imtt.com/terminals/lemont-il/",selection="operator address map; vegetable oil rail/barge candidate; not confirmed CARB terminal"),dict(name="IMTT St Rose",lat=29.94556687497352,lon=-90.33137552409985,source="https://imtt.com/terminals/st-rose-la/",selection="operator address map; Louisiana gathering candidate; not confirmed CARB terminal")]
def paths(kind,orig,dest):
 n,g=m.graph(kind);nn=m.m.xyz(n.lat.to_numpy(),n.lon.to_numpy());tree=cKDTree(nn)
 oo=m.m.xyz(orig[:,0],orig[:,1]);dd=m.m.xyz(dest[:,0],dest[:,1]);_,oi=tree.query(oo);_,di=tree.query(dd)
 return dijkstra(g,directed=False,indices=di)[:,oi],m.m.gc(oo,nn[oi]),m.m.gc(dd,nn[di])
def main():
 h=pd.read_excel(R/"data/raw/soy_crushing_facilities.xlsx");h=h[(h.type.str.lower().str.strip()=="elevator")&(h.bankrupt.fillna(0)==0)].sort_values("number")
 hc=np.column_stack([h.lon,h.lat]);t=np.array([[x["lat"],x["lon"]] for x in TERMINALS])
 rd,rc,rtc=paths("rail",hc,t[:1]);wd,wc,wtc=paths("water",t[:1],t[1:])
 validation=json.loads((R/"output/diagnostics/route_cost_proxy_validation.json").read_text())
 rodeo="Phillips 66 Rodeo (82191)";sea=validation["marine_routes"][rodeo]["km"];exitkm=validation["delta_exit"]["river_terminal_to_exit_km"]
 rows=[]
 for i,hub in enumerate(h.number):
  rail=float(rd[0,i]);barge=float(wd[0,0]+exitkm)
  eligible=bool(h.railfront.iloc[i]==1 and rc[i]<=10 and rtc[0]<=10 and wc[0]<=10 and wtc[0]<=10 and np.isfinite(rail+barge))
  rows.append(dict(hub_id=int(hub),physical_plant_id=rodeo,route="rail_Lemont_barge_StRose_marine_Rodeo",rail_km=rail,barge_km=barge,ocean_km=sea,origin_connector_geodesic_km=rc[i],Lemont_rail_connector_geodesic_km=rtc[0],Lemont_water_connector_geodesic_km=wc[0],StRose_water_connector_geodesic_km=wtc[0],eligible=eligible,linehaul_proxy_truck_equivalent_km=rail*2.35/14.24+(barge+sea)*1.83/14.24,mode_sequence="rail|inland_barge|marine_barge",support="Rodeo CARB b0241 sequence; Lemont and St Rose inferred, not actual shipments",cost_status="broad_freight_proxy_ocean_rate_assumed_handling_access_excluded"))
 cross=pd.read_csv(C/"lcfs_physical_plant_crosswalk.csv").drop_duplicates("physical_plant_id").set_index("physical_plant_id")
 artesia="RENEWABLE DIESEL UNIT (RDU) / PRE-TREATMENT UNIT (PTU) (82381)"
 ac=np.array([list(map(float,cross.loc[artesia,"coordinate_used"].split(",")))])
 first,cc,tc=paths("rail",hc,ac)
 for plant in ["sinclair_wy","Cheyenne Renewable Diesel Company LLC (F00494)"]:
  pc=np.array([list(map(float,cross.loc[plant,"coordinate_used"].split(",")))])
  last,oc,dc=paths("rail",ac,pc)
  for i,hub in enumerate(h.number):
   km=float(first[0,i]+last[0,0]);eligible=bool(h.railfront.iloc[i]==1 and max(cc[i],tc[0],oc[0],dc[0])<=10 and np.isfinite(km))
   rows.append(dict(hub_id=int(hub),physical_plant_id=plant,route="rail_via_Artesia_pretreatment",rail_km=km,barge_km=0,ocean_km=0,origin_connector_geodesic_km=cc[i],eligible=eligible,linehaul_proxy_truck_equivalent_km=km*2.35/14.24,mode_sequence="rail|Artesia_pretreatment|rail",support="CARB feedstock clause Artesia intermediate preserved; actual origin and transfer legs inferred; Cheyenne truck alternative remains uncomputed",cost_status="broad_freight_proxy_handling_access_excluded"))
 out=pd.DataFrame(rows).replace([np.inf,-np.inf],np.nan);assert len(out)==174
 out.to_csv(C/"documented_intermediate_route_proxies.csv",index=False)
 pd.DataFrame(TERMINALS).to_csv(C/"inferred_liquid_bulk_terminal_sources.csv",index=False)
 audit=pd.read_csv(C/"pathway_transport_leg_audit.csv")
 audit["review_status"]="source_clause_reviewed_feedstock_finishedfuel_separated"
 audit["sequence_status"]="listed_modes_order_not_inferred"
 audit.loc[audit.full_description.str.contains("Artesia",case=False,na=False),"required_intermediate"]="Artesia NM pretreatment"
 audit.loc[audit.foreign_feedstock.astype(str).str.lower().eq("true"),"sequence_status"]="foreign_feedstock_excluded_from_US_crusher_routes"
 audit.loc[audit.feedstock_modes.fillna("").eq(""),"sequence_status"]="mode_unspecified_no_mode_claim"
 mexico=audit.full_description.str.contains("Monterrey",case=False,na=False)
 audit.loc[mexico,"required_intermediate"]="Monterrey Mexico soybean extraction then Artesia NM PTU"
 audit.loc[mexico,"sequence_status"]="raw_soybeans_outbound_not_US_crusher_oil_leg_return_oil_mode_unspecified"
 audit["US_crusher_oil_route_evidence"]=~(audit.foreign_feedstock.astype(str).str.lower().eq("true")|mexico)
 audit.to_csv(C/"pathway_transport_leg_audit_reviewed.csv",index=False)
 diag={"rows":len(out),"eligible":int(out.eligible.sum()),"terminals":TERMINALS,"Lemont_StRose_water_km":float(wd[0,0]),"limitations":"Shortest network paths within candidate terminals; no confirmed terminal shipment, no oil-specific rates or actual access legs. Alternatives not procurement shares."}
 (R/"output/diagnostics/intermediate_route_validation.json").write_text(json.dumps(diag,indent=2));print(diag,flush=True)
if __name__=="__main__":main()

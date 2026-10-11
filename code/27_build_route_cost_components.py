"""Audit feedstock vs finished-fuel transport; construct route-component matrix.
Missing legs/rates remain missing, never zero. No procurement shares inferred.
"""
from pathlib import Path
import re
import pandas as pd
R=Path(__file__).resolve().parents[1];C=R/"data/clean"
history=pd.read_csv(C/"lcfs_soy_pathway_history.csv")
rows=[]
for idx,row in history.iterrows():
 text=str(row["Pathway Description"])
 # Delimit first feedstock clause before process energy or explicit finished fuel.
 clauses=re.split(r";|natural gas|\bNG,|finished fuel|renewable diesel transported|fuel produced",text,flags=re.I)
 feed=clauses[0]
 modes=[m for m,pattern in [("rail",r"\brail\b"),("truck",r"\btruck\b"),("barge",r"\bbarge\b"),("ocean",r"ocean tanker|\bship\b")] if re.search(pattern,feed,re.I)]
 rows.append(dict(pathway_row=idx,physical_plant_id=row.physical_plant_id,certification_date=row["Certification Date"],feedstock_clause=feed,feedstock_modes="|".join(modes),foreign_feedstock=bool(re.search(r"Argentin|Argentina",feed,re.I)),review_status="automated_clause_split_requires_manual_review",full_description=text))
audit=pd.DataFrame(rows)
audit.to_csv(C/"pathway_transport_leg_audit.csv",index=False)
d=pd.read_csv(C/"refinery_crusher_transport_matrix.csv")
cross=pd.read_csv(C/"lcfs_physical_plant_crosswalk.csv").drop_duplicates("physical_plant_id").set_index("physical_plant_id")
routes=[]
for _,pair in d.iterrows():
 plant=pair.physical_plant_id
 eligible=audit[(audit.physical_plant_id==plant)&(~audit.foreign_feedstock)]
 modes=set("|".join(eligible.feedstock_modes).split("|"))
 california=str(cross.loc[plant,"Standard Location"]).endswith(", CA")
 candidates=["direct_rail","direct_truck"]
 if "barge" in modes:candidates+=["inland_barge"]
 # Gulf corridor is supported at Rodeo; other California sites are explicitly hypothetical.
 if california:candidates+=["rail_gulf_marine","river_gulf_marine"]
 for route in candidates:
  rail=truck=barge=ocean=None
  status="missing_mode_specific_freight_rates"
  support="mode_documented_route_not_verified" if route.replace("direct_","") in modes else "hypothetical_sensitivity"
  if route=="direct_rail":
   rail=pair.rail_network_km
   # Network connectors are geodesic proximity, NOT measured road legs.
   status="network_geometry_proxy_and_unmeasured_terminal_connectors"
  elif route=="direct_truck":truck=pair.road_km
  elif route=="inland_barge":
   barge=pair.water_network_km
   status="inland_network_proxy_terminal_access_unverified"
  else:
   status="pending_gulf_terminal_origin_leg_marine_leg_and_rates"
   if plant=="Phillips 66 Rodeo (82191)":
    support="CARB_b0241_Louisiana_gathering_point_to_Rodeo_structure_supported_terminal_unspecified"
  routes.append(dict(hub_id=pair.hub_id,physical_plant_id=plant,route=route,rail_km=rail,truck_km=truck,barge_km=barge,ocean_km=ocean,crusher_rail_connector_geodesic_km=pair.crusher_rail_connector_km,refinery_rail_connector_geodesic_km=pair.refinery_rail_connector_km,crusher_riverfront=pair.crusher_riverfront,crusher_railfront=pair.crusher_railfront,route_support=support,cost_status=status,transport_cost_usd_per_tonne=None))
matrix=pd.DataFrame(routes)
assert d[["hub_id","physical_plant_id"]].drop_duplicates().shape[0]==928
assert matrix.transport_cost_usd_per_tonne.isna().all()
matrix.to_csv(C/"refinery_crusher_route_cost_components.csv",index=False)
print("Audited descriptions:",len(audit),"pair coverage:",matrix[["hub_id","physical_plant_id"]].drop_duplicates().shape[0],"candidate routes:",len(matrix),flush=True)

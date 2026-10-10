"""Add inland-waterway graph paths; no invented rail/water freight rates."""
from pathlib import Path
import importlib,json,numpy as np,pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
m=importlib.import_module('24_build_transport_network_matrix');R=m.R
WATER='https://services7.arcgis.com/n1YM8pTrFmm7L4hs/ArcGIS/rest/services/Waterway_Networks/FeatureServer/1'
def main():
 features=m.features(WATER,"GEO_CLASS='I'",'OBJECTID,ANODE,BNODE,DIR,GEO_CLASS,LINKTYPE',True,'water_inland_edges')
 links=[];nodes={}
 for f in features:
  a=f['attributes'];paths=f.get('geometry',{}).get('paths',[])
  if not paths:continue
  length=0
  for path in paths:
   v=np.array(path)[:,:2];xx=m.xyz(v[:,1],v[:,0]);length+=m.gc(xx[:-1],xx[1:]).sum()
  if length<=0:continue
  nodes.setdefault(a['ANODE'],paths[0][0][:2]);nodes.setdefault(a['BNODE'],paths[-1][-1][:2]);links.append((a['ANODE'],a['BNODE'],length))
 e=pd.DataFrame(links,columns=['a','b','km']);e['lo']=e[['a','b']].min(axis=1);e['hi']=e[['a','b']].max(axis=1);e=e.groupby(['lo','hi'],as_index=False).km.min();n=pd.DataFrame.from_dict(nodes,orient='index',columns=['lon','lat']).sort_index();lookup={v:i for i,v in enumerate(n.index)};aa=e.lo.map(lookup).to_numpy();bb=e.hi.map(lookup).to_numpy();g=csr_matrix((np.r_[e.km,e.km],(np.r_[aa,bb],np.r_[bb,aa])),shape=(len(n),len(n)))
 h=pd.read_excel(R/'data/raw/soy_crushing_facilities.xlsx');h=h[(h.type.str.lower().str.strip()=='elevator')&(h.bankrupt.fillna(0)==0)].sort_values('number');cross=pd.read_csv(R/'data/clean/lcfs_physical_plant_crosswalk.csv').drop_duplicates('physical_plant_id').sort_values('physical_plant_id');coords=np.array([list(map(float,s.split(','))) for s in cross.coordinate_used]);nh=m.xyz(h.lon.to_numpy(),h.lat.to_numpy());nr=m.xyz(coords[:,0],coords[:,1]);nn=m.xyz(n.lat.to_numpy(),n.lon.to_numpy());tree=cKDTree(nn);_,hi=tree.query(nh);_,ri=tree.query(nr);hc=m.gc(nh,nn[hi]);rc=m.gc(nr,nn[ri]);paths=dijkstra(g,directed=False,indices=ri)[:,hi];river=next(c for c in h.columns if c.startswith('riverfront'));rows=[]
 for j,plant in enumerate(cross.physical_plant_id):
  for i,hub in enumerate(h.number):
   distance=paths[j,i];rows.append(dict(hub_id=int(hub),physical_plant_id=plant,water_network_km=float(distance) if np.isfinite(distance) else None,crusher_water_connector_km=hc[i],refinery_water_connector_km=rc[j],water_connected=bool(np.isfinite(distance)),water_screen_5km=bool(np.isfinite(distance) and h[river].iloc[i]==1 and hc[i]<=5 and rc[j]<=5),water_screen_10km=bool(np.isfinite(distance) and h[river].iloc[i]==1 and hc[i]<=10 and rc[j]<=10),water_with_connectors_km=float(distance+hc[i]+rc[j]) if np.isfinite(distance) else None,water_access_status='inland_network_proximity_only_not_verified'))
 x=pd.read_csv(R/'data/clean/refinery_crusher_transport_matrix.csv').merge(pd.DataFrame(rows),on=['hub_id','physical_plant_id'],validate='one_to_one');assert len(x)==928;x.to_csv(R/'data/clean/refinery_crusher_transport_matrix.csv',index=False)
 v=json.loads((R/'output/diagnostics/transport_network_validation.json').read_text());v.update(water_service=WATER,water_edges=len(e),water_nodes=len(n),water_connected_pairs=int(x.water_connected.sum()),water_screen_5km_pairs=int(x.water_screen_5km.sum()),water_screen_10km_pairs=int(x.water_screen_10km.sum()));(R/'output/diagnostics/transport_network_validation.json').write_text(json.dumps(v,indent=2));print(v)
if __name__=='__main__':main()

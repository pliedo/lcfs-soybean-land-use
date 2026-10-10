"""Exploratory physical rail/water network paths, not verified procurement routes.
Requires numpy pandas scipy openpyxl; caches public ArcGIS features locally.
"""
from pathlib import Path
import json,time,urllib.request,urllib.parse,concurrent.futures,hashlib
import numpy as np,pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[1];CACHE=R/'data/raw/network_cache';CACHE.mkdir(exist_ok=True,parents=True)
RAIL='https://services.arcgis.com/xOi1kZaI0eWDREZv/ArcGIS/rest/services/NTAD_North_American_Rail_Network_Lines/FeatureServer/0'
NODES='https://services.arcgis.com/xOi1kZaI0eWDREZv/ArcGIS/rest/services/NTAD_North_American_Rail_Network_Nodes/FeatureServer/0'
def query(url,params):
 encoded=urllib.parse.urlencode(params)
 u=url+'?'+encoded
 request=urllib.request.Request(url,data=encoded.encode()) if len(u)>1800 else u
 for k in range(3):
  try:
   with urllib.request.urlopen(request,timeout=60) as f:d=json.load(f)
   if 'error' in d:raise RuntimeError(d['error'])
   return d
  except Exception:
   if k==2:raise
   time.sleep(2**k)
def features(url,where,fields,geometry,name):
 p=CACHE/(name+'.json')
 if p.exists():return json.loads(p.read_text())
 ids=query(url+'/query',dict(where=where,returnIdsOnly='true',f='json'))['objectIds'];ids=sorted(ids or [])
 chunks=[ids[i:i+300] for i in range(0,len(ids),300)]
 def batch(chunk):
  checkpoint=CACHE/(name+'_'+hashlib.sha256(str(chunk).encode()).hexdigest()[:16]+'.json')
  if checkpoint.exists():return json.loads(checkpoint.read_text())
  d=query(url+'/query',dict(objectIds=','.join(map(str,chunk)),outFields=fields,returnGeometry=str(geometry).lower(),outSR=4326,f='json'))
  assert not d.get('exceededTransferLimit',False)
  assert len(d['features'])==len(chunk)
  checkpoint.write_text(json.dumps(d['features']))
  return d['features']
 result=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for i,items in enumerate(pool.map(batch,chunks)):
   result.extend(items)
   if i%20==0:print(name,len(result),'/',len(ids),flush=True)
 assert len(result)==len(ids);p.write_text(json.dumps(result));return result
def xyz(lat,lon):
 lat,lon=np.deg2rad(lat),np.deg2rad(lon);return np.column_stack([np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)])
def gc(a,b):return 6371.0088*2*np.arcsin(np.clip(np.linalg.norm(a-b,axis=1)/2,0,1))
def build_rail():
 meta=query(RAIL,{'f':'json'})
 edges=features(RAIL,"COUNTRY='US' AND NET IN ('M','I','O','S','Y','F')",'OBJECTID,FRFRANODE,TOFRANODE,KM,NET',False,'rail_active_edges')
 nodes=features(NODES,"COUNTRY='US'",'OBJECTID,FRANODEID',True,'rail_us_nodes')
 n=pd.DataFrame([dict(id=f['attributes']['FRANODEID'],lon=f['geometry']['x'],lat=f['geometry']['y']) for f in nodes]);n=n.drop_duplicates('id').set_index('id')
 e=pd.DataFrame([f['attributes'] for f in edges]);e=e.rename(columns={'FRFRANODE':'a','TOFRANODE':'b','KM':'km'});e=e.dropna(subset=['a','b','km']);e=e[e.km>0]
 missing=int((~e.a.isin(n.index)|~e.b.isin(n.index)).sum());e=e[e.a.isin(n.index)&e.b.isin(n.index)]
 e['lo']=e[['a','b']].min(axis=1);e['hi']=e[['a','b']].max(axis=1);e=e.groupby(['lo','hi'],as_index=False).km.min()
 n=n.loc[sorted(set(e.lo)|set(e.hi))].copy();lookup={int(v):i for i,v in enumerate(n.index)};aa=e.lo.map(lookup).to_numpy();bb=e.hi.map(lookup).to_numpy();g=csr_matrix((np.r_[e.km,e.km],(np.r_[aa,bb],np.r_[bb,aa])),shape=(len(n),len(n)))
 h=pd.read_excel(R/'data/raw/soy_crushing_facilities.xlsx');h=h[(h.type.str.lower().str.strip()=='elevator')&(h.bankrupt.fillna(0)==0)].sort_values('number')
 cross=pd.read_csv(R/'data/clean/lcfs_physical_plant_crosswalk.csv').drop_duplicates('physical_plant_id').sort_values('physical_plant_id');coords=np.array([list(map(float,s.split(','))) for s in cross.coordinate_used]);nh=xyz(h.lon.to_numpy(),h.lat.to_numpy());nr=xyz(coords[:,0],coords[:,1]);nn=xyz(n.lat.to_numpy(),n.lon.to_numpy());tree=cKDTree(nn);_,hi=tree.query(nh);_,ri=tree.query(nr);hc=gc(nh,nn[hi]);rc=gc(nr,nn[ri]);paths=dijkstra(g,directed=False,indices=ri)[:,hi]
 rivercol=next(c for c in h.columns if c.startswith('riverfront'))
 result=[]
 for j,plant in enumerate(cross.physical_plant_id):
  for i,hub in enumerate(h.number):
   path=paths[j,i];result.append(dict(hub_id=int(hub),physical_plant_id=plant,crusher_railfront=int(h.railfront.iloc[i]),crusher_riverfront=int(h[rivercol].iloc[i]),crusher_oceanfront=int(h.oceanfront.iloc[i]),rail_network_km=float(path) if np.isfinite(path) else None,crusher_rail_connector_km=hc[i],refinery_rail_connector_km=rc[j],rail_with_connectors_km=float(path+hc[i]+rc[j]) if np.isfinite(path) else None,rail_connected=bool(np.isfinite(path)),rail_screen_5km=bool(np.isfinite(path) and h.railfront.iloc[i]==1 and hc[i]<=5 and rc[j]<=5),rail_screen_10km=bool(np.isfinite(path) and h.railfront.iloc[i]==1 and hc[i]<=10 and rc[j]<=10),refinery_access_status='network_proximity_only_not_verified',network_year=2026))
 out=pd.DataFrame(result).merge(pd.read_csv(R/'data/clean/refinery_crusher_distances_physical.csv'),on=['hub_id','physical_plant_id'],validate='one_to_one')
 # Keep distance modes separately; physically shorter is not necessarily cheaper.
 out.to_csv(R/'data/clean/refinery_crusher_transport_matrix.csv',index=False)
 validation={'rail_service':RAIL,'node_service':NODES,'network_updated_ms':meta.get('editingInfo',{}).get('lastEditDate'),'active_edges':len(e),'nodes':len(n),'edges_omitted_missing_us_nodes':missing,'pairs':len(out),'connected_pairs':int(out.rail_connected.sum()),'screen_5km_pairs':int(out.rail_screen_5km.sum()),'screen_10km_pairs':int(out.rail_screen_10km.sum()),'cache_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in CACHE.glob('rail_*.json')}}
 (R/'output/diagnostics/transport_network_validation.json').write_text(json.dumps(validation,indent=2));print(validation,flush=True)
if __name__=='__main__':build_rail()

"""Observed changes into consecutive soybean, not rotation or first-ever cultivation.
0–25-mile full-period-valid ever-soy pixels, 2013–2025. Save annual sequences
so future definitions do not require downloading the rasters again.
"""
import argparse,importlib.util,json
from pathlib import Path
import numpy as np,pandas as pd,rasterio
from shapely.geometry import box
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('freq',R/'code/91_soy_substitution_by_frequency.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
OUT=R/'persistent-soy-results';YEARS=list(range(2013,2026))
def classify(d):
 # Mutually exclusive baseline histories. Strict observed alternating pattern.
 b=d[:3];rot=((b[0]==5)&(b[1]==1)&(b[2]==5))|((b[0]==1)&(b[1]==5)&(b[2]==1));initial=(b==5).all(axis=0);nonsoy=(b!=5).all(axis=0);always=(d==5).all(axis=0)
 group=np.full(d.shape[1],3,dtype='uint8');group[rot]=1;group[nonsoy]=2;group[initial]=0
 rows=[];origins=[]
 for k in [2,3,4]:
  end=(d[-k:]==5).all(axis=0)
  for g in range(4):
   base=group==g
   # Endpoint rotation is strict alternating soybean/corn in the final 3 years.
   er=((d[-3]==5)&(d[-2]==1)&(d[-1]==5))|((d[-3]==1)&(d[-2]==5)&(d[-1]==1))
   for status,sel in [('consecutive_soy',end),('alternating_soy_corn',er&~end),('other_endpoint',~end&~er)]:
    rows.append(dict(required_years=k,baseline_group=g,endpoint=status,pixels=int((base&sel).sum())))
   sel=base&end
   # Trace the source immediately before the terminal uninterrupted soybean run.
   # A run extending to 2013 has no prior observation; use code -1 explicitly.
   for t in range(13):
    starts=sel&(d[t:]==5).all(axis=0)
    if t>0:starts&=d[t-1]!=5
    else:starts&=always
    codes=d[t-1,starts] if t else np.full(int(starts.sum()),-1)
    for c,n in zip(*np.unique(codes,return_counts=True)):origins.append(dict(required_years=k,baseline_group=g,run_start_year=2013+t,prior_code=int(c),pixels=int(n)))
  assert sum(r['pixels'] for r in rows if r['required_years']==k)==d.shape[1]
  assert sum(r['pixels'] for r in origins if r['required_years']==k)==int(end.sum())
 return rows,origins

def run(hub):
 folder=OUT/f'hub_{hub:03d}';folder.mkdir(parents=True,exist_ok=True)
 files=sorted((R/'pixel-history-results'/f'hub_{hub:03d}').glob('history_*.tif'));assert files
 for tile in files:
  target=folder/(tile.stem+'.npz')
  if target.exists():print('Reuse',target,flush=True);continue
  history=folder/(tile.stem+'.history.npz')
  with rasterio.open(tile) as src:
   freq=src.read(1);mask=(freq>0)&(freq<=13);tf=src.transform;shape=src.shape;bounds=src.bounds
  if history.exists():d=np.load(history)['annual_classes']
  else:
   d=np.empty((13,int(mask.sum())),dtype='uint8')
   for i,y in enumerate(YEARS):
    p=folder/'temporary.tif';m.extract.get_raster(box(*bounds),y,p)
    with rasterio.open(p) as src:
     assert src.crs.to_epsg()==5070 and src.transform==tf and src.shape==shape
     v=src.read(1)[mask];assert ((src.read_masks(1)[mask]>0)&(v>0)&(v!=81)).all();d[i]=v
    p.unlink();print(hub,tile.stem,y,flush=True)
   assert np.array_equal((d==5).sum(axis=0),freq[mask])
   temp=history.with_suffix('.tmp.npz');np.savez_compressed(temp,annual_classes=d);temp.replace(history)
  assert np.array_equal((d==5).sum(axis=0),freq[mask])
  rows,origins=classify(d)
  tmp=target.with_suffix('.tmp.npz');np.savez_compressed(tmp,rows=np.array([[r[k] if k!='endpoint' else ['consecutive_soy','alternating_soy_corn','other_endpoint'].index(r[k]) for k in ['required_years','baseline_group','endpoint','pixels']] for r in rows],dtype='int64'),origins=np.array([[r[k] for k in ['required_years','baseline_group','run_start_year','prior_code','pixels']] for r in origins],dtype='int64').reshape(-1,5));tmp.replace(target)
 counts=[];orig=[]
 for tile in files:
  z=np.load(folder/(tile.stem+'.npz'));counts.append(pd.DataFrame(z['rows'],columns=['required_years','baseline_group','endpoint','pixels']));orig.append(pd.DataFrame(z['origins'],columns=['required_years','baseline_group','run_start_year','prior_code','pixels']))
 a=pd.concat(counts).groupby(['required_years','baseline_group','endpoint'],as_index=False).pixels.sum();b=pd.concat(orig).groupby(['required_years','baseline_group','run_start_year','prior_code'],as_index=False).pixels.sum()
 expected=pd.read_csv(R/'output/pixel_history_inner/soy_persistence.csv');expected=expected[(expected.hub_id==hub)&(expected.soy_years>0)].pixels.sum()
 assert (a.groupby('required_years').pixels.sum()==expected).all();a['hub_id']=hub;b['hub_id']=hub;a.to_csv(folder/'states.csv',index=False);b.to_csv(folder/'sources.csv',index=False);(folder/'complete.json').write_text(json.dumps({'hub':hub,'ever_soy_pixels':int(expected),'sequences_retained':True}))

def merge():
 ids=pd.read_csv(R/'output/pixel_history_inner/soy_persistence.csv').hub_id.unique();assert len(ids)==57;folders=[OUT/f'hub_{int(h):03d}' for h in ids];assert all((p/'complete.json').exists() for p in folders)
 out=R/'output/persistent_soybean';out.mkdir(parents=True,exist_ok=True)
 for name in ['states','sources']:
  x=pd.concat([pd.read_csv(p/(name+'.csv')) for p in folders],ignore_index=True);x.to_csv(out/(name+'.csv'),index=False)
 a=pd.read_csv(out/'states.csv');b=pd.read_csv(out/'sources.csv');assert a.groupby('required_years').pixels.sum().eq(164257754).all()
 for k in [2,3,4]:assert a[(a.required_years==k)&(a.endpoint==0)].pixels.sum()==b[b.required_years==k].pixels.sum()
 (out/'README.md').write_text('Complete 2013–2025-valid ever-class-5 soybean pixels only, exclusive 0–25-mile catchments, all 57 hubs. Baseline 2013–2015 groups: 0 soybean in all three years; 1 strict 5-1-5 or 1-5-1 soybean/corn sequence; 2 no pure soybean in any of the three years; 3 other mixed soybean histories. Endpoint 0: final k years all pure soybean; endpoint 1: final three years strict soybean/corn alternation, excluding consecutive-soy endpoint; endpoint 2 other endpoints. k=2,3,4 retained. Consecutive soybean is observed persistence, not proof of permanent monoculture. Sources records the exact class immediately before the uninterrupted terminal soybean run; -1 means soybean throughout all observed years. Double-crop soybean codes remain distinct from pure class 5. Every full annual pixel sequence is retained in compressed artifacts/caches. No causal attribution. Failed downloads never become zero counts.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--hub',type=int);p.add_argument('--merge',action='store_true');a=p.parse_args();merge() if a.merge else run(a.hub)

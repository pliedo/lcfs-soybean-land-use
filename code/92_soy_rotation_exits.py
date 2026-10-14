"""Descriptive first exits from baseline soybean/soy-corn, common 2013-2025 support."""
import importlib.util,json,argparse
from pathlib import Path
import numpy as np,pandas as pd,rasterio
from shapely.geometry import box
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('freq',ROOT/'code/91_soy_substitution_by_frequency.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
OUT=ROOT/'rotation-exit-results';YEARS=list(range(2013,2026))
def run(hub):
 folder=OUT/f'hub_{hub:03d}';folder.mkdir(parents=True,exist_ok=True)
 for tile in sorted((ROOT/'pixel-history-results'/f'hub_{hub:03d}').glob('history_*.tif')):
  target=folder/(tile.stem+'.npz')
  if target.exists():continue
  with rasterio.open(tile) as src:
   f=src.read(1);mask=(f>0)&(f<=13);tf=src.transform;shape=src.shape;bounds=src.bounds
  data=np.empty((13,int(mask.sum())),dtype='uint8')
  for k,y in enumerate(YEARS):
   p=folder/'temporary.tif';m.extract.get_raster(box(*bounds),y,p)
   with rasterio.open(p) as src:
    assert src.crs.to_epsg()==5070 and src.transform==tf and src.shape==shape
    v=src.read(1)[mask];assert ((src.read_masks(1)[mask]>0)&(v>0)&(v!=81)).all();data[k]=v
   p.unlink()
  assert np.array_equal((data==5).sum(axis=0),f[mask])
  base=data[:3];soy=(base==5).all(axis=0);rot=((base==5)|(base==1)).all(axis=0)&(base==5).any(axis=0)&(base==1).any(axis=0)
  counts=np.zeros((2,4,256),dtype='int64');totals=np.array([soy.sum(),rot.sum()],dtype='int64')
  for g,sel in enumerate([soy,rot]):
   d=data[:,sel];outside=(d[3:]!=5)&(d[3:]!=1);has=outside.any(axis=0);idx=outside.argmax(axis=0)+3
   counts[g,0,0]=int((~has).sum())
   for k in range(3,13):
    ix=np.flatnonzero(has&(idx==k));dest=d[k,ix]
    returned=((d[k+1:,ix]==5)|(d[k+1:,ix]==1)).any(axis=0)
    # Sustained exit: no observed return and at least three consecutive outside years.
    state=np.where(returned,1,2 if k<=10 else 3)
    counts[g]+=np.bincount(state*256+dest,minlength=1024).reshape(4,256)
  assert np.array_equal(counts.sum(axis=(1,2)),totals)
  tmp=target.with_suffix('.tmp.npz');np.savez_compressed(tmp,counts=counts,totals=totals);tmp.replace(target)
 counts=sum(np.load(p)['counts'] for p in folder.glob('history_*.npz'));totals=sum(np.load(p)['totals'] for p in folder.glob('history_*.npz'))
 rows=[dict(hub_id=hub,baseline=g,status=t,cdl_code=c,pixels=int(counts[g,t,c])) for g,t,c in zip(*np.nonzero(counts))]
 pd.DataFrame(rows).to_csv(folder/'counts.csv',index=False);(folder/'complete.json').write_text(json.dumps({'hub':hub,'totals':totals.tolist()}))
def merge():
 ids=pd.read_csv(ROOT/'output/pixel_history_inner/soy_persistence.csv').hub_id.unique();folders=[OUT/f'hub_{int(h):03d}' for h in ids];assert len(ids)==57 and all((p/'complete.json').exists() for p in folders)
 x=pd.concat([pd.read_csv(p/'counts.csv') for p in folders]);out=ROOT/'output/soy_rotation_exits';out.mkdir(parents=True,exist_ok=True);x.to_csv(out/'exact_exit_counts.csv',index=False)
 def cat(c):
  if c in [141,142,143]:return 'Forest'
  return {2:'Cotton',3:'Rice',4:'Sorghum',21:'Barley',22:'Durum wheat',23:'Spring wheat',24:'Winter wheat',41:'Sugar beet'}.get(c,m.category(c))
 x['destination']=x.cdl_code.map(cat);x.loc[x.status==0,'destination']='No exit from soy/corn';x.groupby(['baseline','status','destination']).pixels.sum().reset_index().to_csv(out/'category_exit_counts.csv',index=False)
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,axes=plt.subplots(1,2,figsize=(14,7))
 for g,ax in enumerate(axes):
  z=x[(x.baseline==g)&(x.status==2)].groupby('destination').pixels.sum().sort_values();den=z.sum();assert den>0
  ax.barh(z.index,z/den*100,color=['#b44' if c=='Forest' else '#26738d' for c in z.index]);ax.set_xlabel('Share of sustained first exits (%)');ax.set_title(['Initially soybean only','Initially soybean–corn mix'][g]);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
  for i,v in enumerate(z/den*100):ax.text(v+.3,i,f'{v:.1f}%',va='center',fontsize=9)
  ax.set_xlim(0,max(z/den*100)*1.2)
 fig.suptitle('What replaced soybean / soybean–corn histories?\nExclusive 0–25-mile catchments, baseline 2013–2015');fig.text(.5,.02,'First exit in 2016–2023; at least 3 observed years outside soy/corn and no subsequent return.\nDestination is the class at first exit. Descriptive classification changes, not causal effects.',ha='center',fontsize=10);fig.tight_layout(rect=[0,.09,1,.9]);fig.savefig(out/'sustained_exit_destinations.png',dpi=180);fig.savefig(out/'sustained_exit_destinations.pdf')
 (out/'README.md').write_text('Baseline 2013–2015: pure soy all three years, or both pure soy and corn with no third class. Soy-corn mix is compatible with rotation, not proof of agronomic practice. Track first exit outside class 1/5 in 2016–2025. Status 0 no exit; 1 later observed return to soy/corn; 2 at least three outside years without subsequent return; 3 late exit insufficient follow-up. Figure denominator is sustained-exit pixels separately per baseline group. Forest retained explicitly. Common complete valid 2013–2025 grid; destinations are first-exit classes, not necessarily final class. Double-crop soybean separately classified. No economic causal attribution.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--hub',type=int);p.add_argument('--merge',action='store_true');a=p.parse_args();merge() if a.merge else run(a.hub)

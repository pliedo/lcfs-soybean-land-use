"""Crop substitution conditional on soybean frequency, using saved pixel masks.
No forest audit rerun and no econometric models. One 30km tile at a time.
"""
import argparse,importlib.util,json
from pathlib import Path
import numpy as np,pandas as pd,rasterio
from shapely.geometry import box
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('extract',ROOT/'code/07_extract_cdl_raster_band.py');extract=importlib.util.module_from_spec(spec);spec.loader.exec_module(extract)
YEARS=list(range(2013,2026));OUT=ROOT/'soy-substitution-results'
def category(code):
 if code==1:return 'Corn'
 if code in [26,239,240,241,254]:return 'Double-crop soybean'
 if code==61:return 'Fallow/idle'
 if code in [36,37,176]:return 'Grass/pasture/hay'
 if code==255:return 'Mixed/tied crops'
 if extract.cropland(code):return 'Other crops'
 return 'Other land cover'
def run(hub):
 folder=OUT/f'hub_{hub:03d}';folder.mkdir(parents=True,exist_ok=True)
 files=sorted((ROOT/'pixel-history-results'/f'hub_{hub:03d}').glob('history_*.tif'));assert files
 for file in files:
  target=folder/(file.stem+'.npz')
  if target.exists():print('Reuse',target,flush=True);continue
  with rasterio.open(file) as src:
   freq=src.read(1);tf=src.transform;shape=src.shape;bounds=src.bounds
  mask=(freq>0)&(freq<=13);f=freq[mask].astype('int32');n=len(f)
  # Max 256 MB for a one-million-pixel tile, released after each tile.
  counts=np.zeros((256,n),dtype='uint8');episode=np.zeros((14,256),dtype='int64')
  annual=np.zeros((13,14,256),dtype='int64')
  for k,year in enumerate(YEARS):
   path=folder/'temporary_download.tif';extract.get_raster(box(*bounds),year,path)
   with rasterio.open(path) as src:
    assert src.transform==tf and src.shape==shape and src.crs.to_epsg()==5070
    data=src.read(1)[mask].astype('int32');valid=(src.read_masks(1)[mask]>0)&(data>0)&(data!=81)
    assert valid.all(),'Previously complete coverage changed; stop rather than replacing labels'
   path.unlink();nonsoy=data!=5
   ix=np.flatnonzero(nonsoy);counts[data[ix],ix]+=1
   annual[k]=np.bincount(f[ix]*256+data[ix],minlength=3584).reshape(14,256);episode+=annual[k]
   print(f'hub {hub}: {file.stem} {year}',flush=True)
  assert np.array_equal(counts.sum(axis=0),13-f),'Soybean frequency changed since original audit'
  dominant=counts.argmax(axis=0).astype('int32');maximum=counts.max(axis=0)
  ties=(counts==maximum).sum(axis=0)>1
  dominant[ties]=255;dominant[f==13]=5
  dc=np.bincount(f*256+dominant,minlength=3584).reshape(14,256)
  expected=np.bincount(f,minlength=14);assert np.array_equal(dc.sum(axis=1),expected)
  assert np.array_equal(episode.sum(axis=1),(13-np.arange(14))*expected)
  tmp=target.with_suffix('.tmp.npz');np.savez_compressed(tmp,dominant=dc,episodes=episode,annual=annual,pixels=expected);tmp.replace(target)
 counters={}
 for name in ['dominant','episodes','annual','pixels']:
  counters[name]=sum(np.load(p)[name] for p in sorted(folder.glob('history_*.npz')))
 expected=pd.read_csv(ROOT/'output/pixel_history_inner/soy_persistence.csv')
 expected=expected[expected.hub_id==hub].set_index('soy_years').pixels.reindex(range(14)).to_numpy(copy=True);expected[0]=0
 assert np.array_equal(counters['pixels'],expected)
 for key in ['dominant','episodes']:
  rows=[]
  for soy,code in zip(*np.nonzero(counters[key])):
   rows.append(dict(hub_id=hub,soy_years=int(soy),nonsoy_years=13-int(soy),cdl_code=int(code),count=int(counters[key][soy,code])))
  pd.DataFrame(rows).to_csv(folder/(key+'.csv'),index=False)
 (folder/'complete.json').write_text(json.dumps({'hub_id':hub,'years':YEARS}))
def plot():
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 out=ROOT/'output/soy_substitution_frequency';out.mkdir(parents=True,exist_ok=True)
 ids=pd.read_csv(ROOT/'output/pixel_history_inner/soy_persistence.csv').hub_id.unique()
 folders=[OUT/f'hub_{h:03d}' for h in ids];assert all((p/'complete.json').exists() for p in folders)
 for key in ['dominant','episodes']:
  x=pd.concat([pd.read_csv(p/(key+'.csv')) for p in folders],ignore_index=True)
  x.to_csv(out/(key+'_exact_codes.csv'),index=False)
  x['category']=x.cdl_code.map(category);x.loc[x.nonsoy_years==0,'category']='Always soy'
  t=x.groupby(['nonsoy_years','category'])['count'].sum().unstack(fill_value=0).reindex(range(13),fill_value=0)
  t.to_csv(out/(key+'_categories.csv'))
  if key=='dominant':
   total=t.to_numpy().sum();group=t.sum(axis=1);xshare=100*t/total
   fig,axs=plt.subplots(1,2,figsize=(13,6),gridspec_kw={'width_ratios':[1,1.5]},sharey=True)
   axs[0].barh(group.index,100*group/total,color='#163749');axs[0].set(xlabel='Share of all ever-soybean pixels (%)',ylabel='Number of nonsoybean years, out of 13')
   for k,v in group.items():axs[0].text(100*v/total+.2,k,f'{100*v/total:.2f}%',va='center',fontsize=8)
   comp=t.div(group,axis=0)*100;left=np.zeros(13)
   colors={'Always soy':'#176C93','Corn':'#DDAA33','Double-crop soybean':'#44AA99','Fallow/idle':'#999999','Grass/pasture/hay':'#88CC66','Other crops':'#AA66AA','Other land cover':'#6699CC','Mixed/tied crops':'#CC6677'}
   for label in colors:
    if label not in comp:continue
    axs[1].barh(comp.index,comp[label],left=left,label=label,color=colors[label]);left+=comp[label].to_numpy()
   axs[1].set(xlabel='Most frequent nonsoybean class within group (%)',xlim=(0,100));axs[0].set_yticks(range(13));axs[0].invert_yaxis()
   fig.suptitle('Soybean substitution in exclusive 0–25-mile catchments, 2013–2025',fontsize=14)
   fig.legend(loc='lower center',ncol=4,fontsize=9);fig.tight_layout(rect=[0,.12,1,.95]);fig.savefig(out/'soy_substitution_by_frequency.png',dpi=180);fig.savefig(out/'soy_substitution_by_frequency.pdf');plt.close(fig)
  else:
   t.drop(index=0,errors='ignore').div(t.sum(axis=1),axis=0).mul(100).to_csv(out/'nonsoy_pixel_year_composition_percent.csv')
 (out/'README.md').write_text('Each group counts distinct pixels that were class-5 soybeans at least once on common valid 2013–2025 support. Left panel uses all ever-soybean pixels as denominator. Right panel assigns each pixel its most frequent exact nonsoybean CDL class; exact-code ties are a separate group. Always-soy pixels have no alternative class. Episode tables count nonsoybean pixel-years, a different denominator. Double-crop soybean is explicitly separate from pure soybean. These are descriptive rotations/substitutions, not policy effects.\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--hub',type=int);a.add_argument('--merge',action='store_true');args=a.parse_args()
 if args.merge:plot()
 else:run(args.hub)

"""Origins of NEW consecutive-soybean and soybean/corn-rotation patterns.
Consumes retained annual pixel sequences from workflow95; no raster downloads.
Baseline 2013–2015 vs endpoint 2023–2025, common valid support.
"""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
R=Path(__file__).resolve().parents[1];SRC=R/'persistent-soy-results';OUT=R/'pattern-origins-results'
def count(d):
 b=d[:3];initialsoy=(b==5).all(axis=0);initialrot=((b[0]==5)&(b[1]==1)&(b[2]==5))|((b[0]==1)&(b[1]==5)&(b[2]==1));nonsoy=(b!=5).all(axis=0)
 mode=np.where((b[0]==b[1])|(b[0]==b[2]),b[0],np.where(b[1]==b[2],b[1],255)).astype('int16')
 source=mode.copy();source[~nonsoy]=-12;source[initialsoy]=-11;source[initialrot]=-10
 finalsoy=(d[-3:]==5).all(axis=0);e=d[-3:];finalrot=((e[0]==5)&(e[1]==1)&(e[2]==5))|((e[0]==1)&(e[1]==5)&(e[2]==1))
 rows=[]
 for target,sel in [('consecutive_soybean',finalsoy&~initialsoy),('soybean_corn_rotation',finalrot&~initialrot)]:
  for c,n in zip(*np.unique(source[sel],return_counts=True)):rows.append(dict(target=target,baseline_code=int(c),pixels=int(n)))
 return rows,dict(ever_soy_pixels=d.shape[1],new_consecutive=int((finalsoy&~initialsoy).sum()),new_rotation=int((finalrot&~initialrot).sum()),continuing_consecutive=int((finalsoy&initialsoy).sum()),continuing_rotation=int((finalrot&initialrot).sum()))
def run(hub):
 folder=OUT/f'hub_{hub:03d}';folder.mkdir(parents=True,exist_ok=True);files=sorted((SRC/f'hub_{hub:03d}').glob('*.history.npz'));assert files
 allrows=[];sums={}
 for file in files:
  checkpoint=folder/(file.stem+'.csv');meta=checkpoint.with_suffix('.json')
  if checkpoint.exists() and meta.exists():rows=pd.read_csv(checkpoint).to_dict('records');tot=json.loads(meta.read_text())
  else:
   d=np.load(file)['annual_classes'];assert d.shape[0]==13;rows,tot=count(d);pd.DataFrame(rows,columns=['target','baseline_code','pixels']).to_csv(checkpoint,index=False);meta.write_text(json.dumps(tot))
  allrows.extend(rows)
  for k,v in tot.items():sums[k]=sums.get(k,0)+v
 expected=pd.read_csv(R/'output/pixel_history_inner/soy_persistence.csv');expected=expected[(expected.hub_id==hub)&(expected.soy_years>0)].pixels.sum();assert sums['ever_soy_pixels']==expected
 x=pd.DataFrame(allrows).groupby(['target','baseline_code'],as_index=False).pixels.sum();assert x.query("target=='consecutive_soybean'").pixels.sum()==sums['new_consecutive'];assert x.query("target=='soybean_corn_rotation'").pixels.sum()==sums['new_rotation'];x['hub_id']=hub;x.to_csv(folder/'counts.csv',index=False);(folder/'complete.json').write_text(json.dumps(sums))
def merge():
 ids=pd.read_csv(R/'output/pixel_history_inner/soy_persistence.csv').hub_id.unique();assert len(ids)==57;folders=[OUT/f'hub_{int(h):03d}' for h in ids];assert all((p/'complete.json').exists() for p in folders)
 out=R/'output/soybean_pattern_origins';out.mkdir(parents=True,exist_ok=True);x=pd.concat([pd.read_csv(p/'counts.csv') for p in folders],ignore_index=True);x.to_csv(out/'exact_origins.csv',index=False)
 totals=pd.DataFrame([dict(hub_id=int(h),**json.loads((p/'complete.json').read_text())) for h,p in zip(ids,folders)]);assert totals.ever_soy_pixels.sum()==164257754;totals.to_csv(out/'accounting.csv',index=False)
 def cat(c):
  if c==-10:return 'Soybean–corn rotation'
  if c==-11:return 'Soybean in all baseline years'
  if c==-12:return 'Other soybean histories'
  if c==255:return 'Tied nonsoybean baseline classes'
  if c==1:return 'Corn'
  if c in [26,239,240,241,254]:return 'Double-crop soybean'
  if c in [141,142,143]:return 'Forest'
  if c in [36,37,176]:return 'Grass / pasture / hay'
  if c==61:return 'Fallow / idle'
  if c in [190,195]:return 'Wetlands'
  if c in [83,111]:return 'Water'
  if 1<=c<=61 or 66<=c<=77 or 204<=c<=254:return 'Other crops'
  return 'Other land cover'
 x['origin']=x.baseline_code.map(cat);z=x.groupby(['target','origin'],as_index=False).pixels.sum();z['acres']=z.pixels*900/4046.8564224;z['share_percent']=100*z.pixels/z.groupby('target').pixels.transform('sum');z.to_csv(out/'origins.csv',index=False)
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 plt.rcParams.update({'font.size':11,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False,'text.color':'#163749'})
 fig,axs=plt.subplots(1,2,figsize=(13.3,5.1))
 for ax,target,title in zip(axs,['consecutive_soybean','soybean_corn_rotation'],['Became consecutive soybean','Became soybean–corn rotation']):
  q=z[z.target==target].sort_values('acres');n=q.acres.sum();yy=np.arange(len(q));ax.barh(yy,q.acres/1e6,color='#26738d',height=.65);ax.set_yticks(yy,q.origin);ax.set_title(title+'\n'+f'{n/1e6:.2f} million acres in the entrant cohort',fontsize=12);ax.set_xlabel('Million acres by baseline origin');ax.set_xlim(0,(q.acres/1e6).max()*1.28);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
  for i,(_,r) in enumerate(q.iterrows()):ax.text(r.acres/1e6+.01,i,f'{r.share_percent:.1f}%',va='center',fontsize=9)
 fig.tight_layout(w_pad=3)
 for ext in ['png','pdf']:fig.savefig(out/('soybean_pattern_origins.'+ext),dpi=180,bbox_inches='tight')
 (out/'README.md').write_text('Baseline 2013–2015; endpoint 2023–2025. Consecutive target: all three endpoint years pure soybean (5), excluding pixels already all soybean in baseline. Rotation target: endpoint 5-1-5 or1-5-1, excluding pixels already strictly alternating in baseline. Origin is baseline HISTORY when soybean occurs there (all soybean, alternating, or other mixed soybean); for no-soy baseline use modal exact CDL class across first3 years, with all-distinct ties explicit. Every counted pixel is on complete valid 2013–2025 support, exclusive0–25 rings,57 hubs. Counts are entrants into observed patterns, not permanent conversion, net expansion or LCFS effects. Rotation-to-consecutive soybean can change planting intensity without expanding cropland. Double-crop soybean separate, forest neutral color. Source annual sequences retained by workflow95; no raster redownload.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--hub',type=int);p.add_argument('--merge',action='store_true');a=p.parse_args();merge() if a.merge else run(a.hub)

"""Annual origins of sustained soybean-system adoption, 2016–2025.
Reuse workflow95 annual sequences; never downloads rasters. Broad soybean system
allows consecutive soybean and soybean/corn alternation, but no consecutive corn.
Strict rotation allows only alternation since entry. First source is class before
that active episode. Episodes can exit; curves are active acres, not ever-adopted.
"""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
R=Path(__file__).resolve().parents[1];SRC=R/'persistent-soy-results';OUT=R/'post2016-pattern-results'
def count(d):
 ever=d.shape[1];fixed=((d!=83)&(d!=111)).all(axis=0);d=d[:,fixed];n=d.shape[1];sb=np.zeros(n,dtype='int16');sr=sb.copy();pre=(d[:3]==5).any(axis=0);ii=np.arange(n);rows=[];soy=[]
 for t in range(13):
  valid=(d[t]==1)|(d[t]==5);sb[~valid]=t+1;sr[~valid]=t+1
  if t:
   sb[valid&(d[t]==1)&(d[t-1]==1)]=t
   sr[valid&(d[t]==d[t-1])]=t
  if t<3:continue
  soy.append(dict(year=2013+t,soy_pixels=int((d[t]==5).sum())))
  for k in [2,3]:
   broad=valid&(sb>=3)&((t-sb+1)>=k)
   strict=broad&(sr==sb)
   assert np.all(~strict|broad)
   for target,sel in [('sustained_soybean_system',broad),('strict_soybean_corn_rotation',strict)]:
    ind=ii[sel];codes=d[sb[sel]-1,ind].astype('int32');start=sb[sel].astype('int32')
    key=((start*256+codes)*2+pre[sel].astype('int32'));u,c=np.unique(key,return_counts=True)
    for v,nn in zip(u,c):rows.append(dict(year=2013+t,min_years=k,target=target,entry_year=2013+int(v//512),origin_code=int((v//2)%256),pre2016_soy=int(v%2),pixels=int(nn)))
 return rows,soy,dict(ever_soy_pixels=ever,fixed_nonwater_ever_soy_pixels=n)
def run(hub):
 folder=OUT/f'hub_{hub:03d}';folder.mkdir(parents=True,exist_ok=True);files=sorted((SRC/f'hub_{hub:03d}').glob('*.history.npz'));assert files;rows=[];annual=[];totals={}
 for file in files:
  cache=folder/(file.stem+'.csv');meta=folder/(file.stem+'.json');ann=folder/(file.stem+'.annual.csv')
  if cache.exists() and meta.exists() and ann.exists():a=pd.read_csv(cache).to_dict('records');b=pd.read_csv(ann).to_dict('records');c=json.loads(meta.read_text())
  else:
   a,b,c=count(np.load(file)['annual_classes']);pd.DataFrame(a,columns=['year','min_years','target','entry_year','origin_code','pre2016_soy','pixels']).to_csv(cache,index=False);pd.DataFrame(b).to_csv(ann,index=False);meta.write_text(json.dumps(c))
  rows+=a;annual+=b
  for key,v in c.items():totals[key]=totals.get(key,0)+v
 expected=pd.read_csv(R/'output/pixel_history_inner/soy_persistence.csv');expected=expected[(expected.hub_id==hub)&(expected.soy_years>0)].pixels.sum();assert totals['ever_soy_pixels']==expected
 x=pd.DataFrame(rows,columns=['year','min_years','target','entry_year','origin_code','pre2016_soy','pixels']).groupby(['year','min_years','target','entry_year','origin_code','pre2016_soy'],as_index=False).pixels.sum();x['hub_id']=hub;x.to_csv(folder/'counts.csv',index=False);y=pd.DataFrame(annual).groupby('year',as_index=False).soy_pixels.sum();y['hub_id']=hub;y.to_csv(folder/'annual.csv',index=False);(folder/'complete.json').write_text(json.dumps(totals))
def category(c):
 if c==1:return 'Corn'
 if c in [26,239,240,241,254]:return 'Double-crop soybean'
 if c==61:return 'Fallow / idle'
 if c in [36,37,176]:return 'Grass / pasture / hay'
 if c in [141,142,143]:return 'Forest'
 if c in [190,195]:return 'Wetlands'
 if 1<=c<=61 or 66<=c<=77 or 204<=c<=254:return 'Other crops'
 return 'Other land cover'
def merge():
 ids=pd.read_csv(R/'output/pixel_history_inner/soy_persistence.csv').hub_id.unique();assert len(ids)==57;folders=[OUT/f'hub_{int(h):03d}' for h in ids];assert all((p/'complete.json').exists() for p in folders)
 out=R/'output/post2016_soybean_patterns';out.mkdir(parents=True,exist_ok=True)
 a=pd.concat([pd.read_csv(p/'counts.csv') for p in folders],ignore_index=True);annual=pd.concat([pd.read_csv(p/'annual.csv') for p in folders],ignore_index=True);meta=pd.DataFrame([dict(hub_id=int(h),**json.loads((p/'complete.json').read_text())) for h,p in zip(ids,folders)]);assert meta.ever_soy_pixels.sum()==164257754
 coverage=pd.read_csv(R/'output/pixel_history_inner/coverage.csv');denom=int(coverage.groupby('hub_id').fixed_nonwater.first().sum());a['origin']=a.origin_code.map(category);acres=900/4046.8564224;a['acres']=a.pixels*acres;a['percent_fixed_nonwater_land']=100*a.pixels/denom;a.to_csv(out/'annual_exact_origins.csv',index=False);meta.to_csv(out/'accounting.csv',index=False)
 z=a.groupby(['year','min_years','target','origin'],as_index=False)[['pixels','acres','percent_fixed_nonwater_land']].sum();z.to_csv(out/'annual_origins.csv',index=False)
 totals=z.groupby(['year','min_years','target'],as_index=False).pixels.sum().pivot(index=['year','min_years'],columns='target',values='pixels').fillna(0);assert (totals.strict_soybean_corn_rotation<=totals.sustained_soybean_system).all()
 sy=annual.groupby('year',as_index=False).soy_pixels.sum();sy['soy_acres']=sy.soy_pixels*acres;sy['soy_share_fixed_nonwater']=100*sy.soy_pixels/denom;sy.to_csv(out/'annual_soybean_fixed_support.csv',index=False);peak=int(sy.sort_values(['soy_pixels','year'],ascending=[False,True]).iloc[0].year);z[z.year.eq(peak)].to_csv(out/'peak_year_origins.csv',index=False)
 # Fixed source panel distinguishes first observed adoption from returns to land with pre-2016 soybean.
 a.groupby(['year','min_years','target','pre2016_soy'],as_index=False).pixels.sum().to_csv(out/'prior_soybean_status.csv',index=False)
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 plt.rcParams.update({'font.size':11,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False,'text.color':'#163749'})
 order=['Corn','Fallow / idle','Grass / pasture / hay','Other crops','Double-crop soybean','Forest','Wetlands','Other land cover'];colors=['#DDAA33','#A3A3A3','#74A65A','#8B6DA6','#44AA99','#637B75','#89B7C2','#426983'];fig,axs=plt.subplots(1,2,figsize=(13.3,4.7),sharey=True)
 for ax,target,title in zip(axs,['sustained_soybean_system','strict_soybean_corn_rotation'],['Sustained soybean cultivation (rotation allowed)','Strict soybean–corn rotation since entry']):
  v=z[(z.target==target)&(z.min_years==2)].pivot(index='year',columns='origin',values='percent_fixed_nonwater_land').reindex(index=range(2016,2026),columns=order,fill_value=0).fillna(0);bottom=np.zeros(10)
  for c,col in zip(order,colors):ax.bar(v.index,v[c],bottom=bottom,color=col,width=.78,label=c);bottom+=v[c].to_numpy()
  ax.axvline(peak,color='#163749',ls=':',lw=1.2);ax.set_title(title,fontsize=11);ax.set_xticks(range(2016,2026,2));ax.set_xlabel('Observation year');ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
 axs[0].set_ylabel('Active adopted acres / fixed nonwater land (%)');fig.legend(*axs[0].get_legend_handles_labels(),loc='lower center',ncol=4,frameon=False,fontsize=9);fig.suptitle(f'0–25-mile catchments: origins of qualifying episodes starting in 2016 or later\nDotted line: peak soybean acres on fixed support ({peak})',fontsize=12);fig.tight_layout(rect=[0,.12,1,.87],w_pad=2)
 for ext in ['png','pdf']:fig.savefig(out/('post2016_pattern_origins.'+ext),dpi=180,bbox_inches='tight')
 plt.close(fig)
 fig,axs=plt.subplots(1,2,figsize=(13.3,4.7))
 for ax,target,title in zip(axs,['sustained_soybean_system','strict_soybean_corn_rotation'],['Sustained soybean cultivation','Strict soybean–corn rotation']):
  q=z[(z.year==peak)&(z.min_years==2)&(z.target==target)].sort_values('acres');pp=100*q.acres/q.acres.sum();ax.barh(q.origin,pp,color='#26738d');ax.set_xlabel('Share of qualifying acres by prior crop / land use (%)');ax.set_title(title+'\n'+f'{q.acres.sum()/1e6:.2f} million active acres',fontsize=12);ax.set_xlim(0,105)
  for i,pc in enumerate(pp):ax.text(pc+.7,i,f'{pc:.1f}%',va='center',fontsize=10)
 fig.suptitle(f'What preceded these post-2015 episodes? Peak soybean year: {peak}',fontsize=13);fig.tight_layout(rect=[0,0,1,.92],w_pad=3)
 for ext in ['png','pdf']:fig.savefig(out/('peak_pattern_origins.'+ext),dpi=180,bbox_inches='tight')
 (out/'README.md').write_text('Annual analysis2016–2025, full-period valid fixed nonwater support, exclusive0–25 catchments57hubs. A qualifying episode starts2016 or later, lasts at least2 observed seasons (3-year sensitivity retained), uses only pure soybean5/corn1, and contains no consecutive corn years. It may be all soybean or include rotation. Strict rotation is a SUBSET: every season alternates since that same episode began. Origin is exact CDL class immediately before the episode, not a fixed three-year modal baseline. Existing episodes beginning before2016 excluded; returning pre2016-soy land flagged separately. At each year count ACTIVE qualifying acres; exits remove acres, reentries are new episodes and do not double-count a pixel within a year. Crop establishment cannot be confirmed until minimum history exists. Fixed land denominator includes all fixed nonwater land, not just adopters. Origin composition percentages at peak have the entrant cohort denominator instead. Peaks are2016–2025 soybean-acre maxima on the SAME fixed support; never-soy pixels contribute zero soy. Observed sustained use is not permanent conversion or a causal LCFS effect. Rotation in broad panel also appears in strict panel, so panels must not be added. Pure double-crop classes remain separate sources. Only inner ring has pixel sequences here; aggregate peak references for other rings do not establish their pixel histories.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--hub',type=int);p.add_argument('--merge',action='store_true');a=p.parse_args();merge() if a.merge else run(a.hub)

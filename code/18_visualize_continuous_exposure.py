"""Descriptive exposure gradients; exposure terciles are not causal control groups."""
from pathlib import Path
import pandas as pd,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];C=ROOT/'data/clean';O=ROOT/'output/figures/results'
e=pd.read_csv(C/'crusher_year_lcfs_exposure_baseline.csv');y=pd.read_csv(C/'crop_outcomes_exclusive.csv');y=y[y.year>=2014]
end=e[e.year==2024].set_index('hub_id').exp_150mi
# Rank ties by hub identifier, fixed groups across years, before looking at outcomes.
group=pd.qcut(end.rank(method='first'),3,labels=['Low exposure','Medium exposure','High exposure']).rename('exposure_group')
e=e.merge(group,on='hub_id');p=y.merge(e[['hub_id','year','exp_150mi','exposure_group']],on=['hub_id','year'])
base=p[p.year==2014][['hub_id','ring_index','soy_share_all_land']].rename(columns={'soy_share_all_land':'share2014'})
p=p.merge(base,on=['hub_id','ring_index'],validate='many_to_one');p['change_pp']=100*(p.soy_share_all_land-p.share2014)
p.groupby(['exposure_group','ring_index','year'],observed=True).agg(mean_change_pp=('change_pp','mean'),hubs=('change_pp','count'),mean_share=('soy_share_all_land','mean')).reset_index().to_csv(ROOT/'output/tables/continuous_exposure_descriptive_trends.csv',index=False)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
colors={'Low exposure':'#3496B3','Medium exposure':'#D99C39','High exposure':'#773E87'}
fig,axes=plt.subplots(2,3,figsize=(12.8,7.2),sharex=True)
for ring,ax in enumerate(axes.flat,1):
 for name,color in colors.items():
  z=p[(p.ring_index==ring)&(p.exposure_group==name)].groupby('year').change_pp.mean()
  ax.plot(z.index,z.values,color=color,label=name,lw=2.5)
 ax.axhline(0,color='#aaaaaa',ls=':',lw=1);ax.set_title(f'{(ring-1)*25}–{ring*25} miles',loc='left');ax.set_xticks([2014,2019,2024]);ax.set_ylabel('Change from 2014 (pp)')
fig.suptitle('Soybean-share changes by geographic exposure',x=.08,ha='left',fontsize=19,weight='bold')
fig.legend(*axes.flat[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,.91),ncol=3,frameon=False)
fig.subplots_adjust(left=.08,right=.98,top=.79,bottom=.19,hspace=.40,wspace=.32)
fig.text(.08,.06,'Fixed terciles of 2024 distance-weighted capacity; exponential road-distance decay, 150-mile scale.\nSame hub groups across all years and rings; equal hub weights; soybean / all valid land pixels.\nDescriptive only: future exposure defines groups. These are not treated/control groups or a parallel-trends test.',fontsize=10,color='#555555')
for ext in ['png','pdf']:fig.savefig(O/f'continuous_exposure_group_trends.{ext}',dpi=180)
fig,ax=plt.subplots(figsize=(12.8,7.2))
for hub,z in e.groupby('hub_id'):
 color=colors[str(z.exposure_group.iloc[0])];ax.plot(z.year,z.exp_150mi*100,color=color,alpha=.22,lw=1)
for name,color in colors.items():
 z=e[e.exposure_group==name].groupby('year').exp_150mi.mean()*100
 ax.plot(z.index,z.values,color=color,lw=3,label=name+' mean')
ax.set(xlabel='Growing-season year',ylabel='Weighted eligible capacity (million gal/year)',xticks=range(2014,2025,2));ax.legend(frameon=False,loc='upper left')
ax.set_title('Policy exposure adds across eligible refineries',loc='left',fontsize=20,weight='bold',pad=20)
fig.subplots_adjust(left=.10,right=.96,top=.86,bottom=.21)
fig.text(.10,.065,'Thin lines: individual crushers; thick lines: exposure-group means. Groups fixed using 2024 exposure.\nExposure = sum of pre-plant eligible refinery capacities × fixed distance weights.\nThis is weighted exposure, not refinery output or soybean purchases; nearest-normalized weights do not conserve capacity.',fontsize=10,color='#555555')
for ext in ['png','pdf']:fig.savefig(O/f'continuous_exposure_trajectories.{ext}',dpi=180)

"""Six-band forest classification audit, valid pixels only."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
x=pd.read_csv(ROOT/'data/clean/cdl_class_composition_exclusive.csv')
x=x[(x.cdl_code!=0)&(x.year>=2014)]
a=x.groupby(['ring_index','year','cdl_code']).pixel_count.sum().unstack(fill_value=0)
s=a.div(a.sum(axis=1),axis=0)*100
out=ROOT/'output/diagnostics'
rows=[]
for r in range(1,7):
 d=s.loc[r]
 rows.append({'ring_index':r,'band':f'{(r-1)*25}–{r*25}',
              'deciduous_change_pp':d.loc[2019,141]-d.loc[2018,141],
              'evergreen_change_pp':d.loc[2019,142]-d.loc[2018,142],
              'mixed_change_pp':d.loc[2019,143]-d.loc[2018,143],
              'total_forest_change_pp':d.loc[2019,[141,142,143]].sum()-d.loc[2018,[141,142,143]].sum()})
pd.DataFrame(rows).to_csv(out/'forest_2019_break_six_bands.csv',index=False)
s[[141,142,143]].to_csv(out/'forest_types_six_band_year_shares.csv')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
fig,axes=plt.subplots(2,3,figsize=(12.8,7.2),sharex=True)
for r,ax in enumerate(axes.flat,1):
 d=s.loc[r]
 for code,label,color in [(141,'Deciduous','#163D64'),(142,'Evergreen','#2A917C'),(143,'Mixed','#D17B28')]:
  ax.plot(d.index,d[code],label=label,color=color,lw=2)
 for year in [2019,2021]:ax.axvline(year,color='#999999',ls=':',lw=1)
 ax.set_title(f'{(r-1)*25}–{r*25} miles',loc='left',weight='bold')
 ax.set_xticks([2014,2019,2021,2024]);ax.grid(axis='y',alpha=.15)
 axes[0,0].legend(frameon=False,fontsize=9)
fig.suptitle('Forest classifications across the six distance bands',x=.08,ha='left',fontsize=19,weight='bold',y=.97)
fig.supylabel('Share of valid pixels (%)',x=.02)
fig.subplots_adjust(left=.08,right=.97,top=.85,bottom=.19,hspace=.36,wspace=.24)
fig.text(.08,.065,'Dotted lines: 2019 and 2021 source updates documented in USDA Iowa metadata.\nPixel-weighted across hubs within each band; panel y-axes differ. Background pixels excluded.',fontsize=10,color='#555555')
f=ROOT/'output/figures/diagnostics';f.mkdir(parents=True,exist_ok=True)
for ext in ['png','pdf']:fig.savefig(f/f'forest_classification_break_six_bands.{ext}',dpi=200,facecolor='white')

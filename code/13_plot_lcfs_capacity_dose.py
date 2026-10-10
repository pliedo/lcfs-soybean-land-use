"""Presentation plot of first-observed soybean approval eligible capacity."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
x=pd.read_csv(ROOT/'output/diagnostics/lcfs_physical_plant_sensitivity_totals.csv')
x=x[x.scenario=='physical_onset_snapshot_capacity'].sort_values('year')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':15,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
fig,ax=plt.subplots(figsize=(12.8,7.2))
for field,color,label,style in [('calendar_dose_mgy','#163D64','Approved by year-end','-'),('planting_cutoff_dose_mgy','#D17B28','Approved by May 1','--')]:
 ax.plot(x.year,x[field]/1000,marker='o',lw=3,color=color,label=label,linestyle=style)
ax.set(xlim=(2013,2024.3),ylim=(-.08,5.6),ylabel='Eligible capacity (billion gallons/year)',xlabel='Year')
ax.set_xticks(range(2013,2025));ax.tick_params(axis='x',labelsize=12)
ax.grid(axis='y',alpha=.18);ax.legend(loc='upper left',frameon=False)
ax.annotate('5.11',xy=(2024,5.108),xytext=(-5,13),textcoords='offset points',ha='right',color='#163D64',weight='bold')
ax.annotate('4.85',xy=(2024,4.848),xytext=(-5,-25),textcoords='offset points',ha='right',color='#D17B28',weight='bold')
fig.suptitle('LCFS-linked renewable diesel capacity',x=.09,ha='left',fontsize=23,weight='bold',y=.96)
fig.text(.09,.89,'Eligibility begins at the first observed soybean pathway approval',fontsize=14,color='#555555')
fig.subplots_adjust(left=.09,right=.97,top=.82,bottom=.28)
fig.text(.09,.065,'16 physical plants; Sinclair alias mapping provisional. Capacity counts each plant once.\nMay 1 is a planting-timing assumption; capacity is annual, not observed throughput.\nZeros before 2017 reflect this approval snapshot, not proof of no earlier LCFS eligibility.',fontsize=10.5,color='#555555',linespacing=1.5)
out=ROOT/'output/figures/treatment';out.mkdir(parents=True,exist_ok=True)
for ext in ['png','pdf']:fig.savefig(out/f'lcfs_capacity_dose_by_year.{ext}',dpi=200,facecolor='white')

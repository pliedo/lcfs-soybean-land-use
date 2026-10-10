"""Pre-planting exposure: May 1 eligibility times previous-year capacity.

Annual change decomposes into new eligibility and existing eligible capacity
changes. These are changes in constructed eligible capacity, not new builds.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
x=pd.read_csv(ROOT/'data/clean/lcfs_physical_plant_year_treatment_scenarios.csv',parse_dates=['first_observed_soy_approval'])
keys=['scenario','physical_plant_id','year']
lag=x[keys+['capacity_mgy']].rename(columns={'capacity_mgy':'preplant_capacity_mgy'})
lag.year+=1
x=x.merge(lag,on=keys,how='left',validate='one_to_one')
x=x[x.year>=2014].copy()
assert x.preplant_capacity_mgy.notna().all()
x['eligible']=x.first_observed_soy_approval<=pd.to_datetime(x.year.astype(str)+'-05-01')
x['eligible_previous']=x.first_observed_soy_approval<=pd.to_datetime((x.year-1).astype(str)+'-05-01')
x['planting_aligned_dose_mgy']=x.preplant_capacity_mgy*x.eligible
x['new_eligibility_mgy']=x.preplant_capacity_mgy*(x.eligible.astype(int)-x.eligible_previous.astype(int))
x=x.sort_values(keys)
x['previous_preplant_capacity_mgy']=x.groupby(['scenario','physical_plant_id']).preplant_capacity_mgy.shift()
x['existing_eligible_capacity_change_mgy']=(x.preplant_capacity_mgy-x.previous_preplant_capacity_mgy)*x.eligible_previous
# Initial sample year is known zero eligibility in this snapshot, not an
# imputed 2012 capacity. Do not use this rule if earlier approvals are added.
assert not x.loc[x.year==2014,'eligible_previous'].any()
x.loc[x.year==2014,'existing_eligible_capacity_change_mgy']=0
out=ROOT/'output/figures/treatment';out.mkdir(parents=True,exist_ok=True)
x.to_csv(ROOT/'data/clean/lcfs_preplant_capacity_dose_scenarios.csv',index=False)
s=x.groupby(['scenario','year'])[['planting_aligned_dose_mgy','new_eligibility_mgy','existing_eligible_capacity_change_mgy']].sum().reset_index()
s['annual_dose_change_mgy']=s.groupby('scenario').planting_aligned_dose_mgy.diff()
s.loc[s.year==2014,'annual_dose_change_mgy']=s.loc[s.year==2014,'planting_aligned_dose_mgy']
assert np.allclose(s.annual_dose_change_mgy,s.new_eligibility_mgy+s.existing_eligible_capacity_change_mgy)
s.to_csv(ROOT/'output/diagnostics/lcfs_preplant_dose_annual_changes.csv',index=False)
d=s[s.scenario=='physical_onset_snapshot_capacity']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
fig,axes=plt.subplots(2,1,figsize=(12.8,7.2),sharex=True,gridspec_kw={'height_ratios':[1,1.1]})
axes[0].plot(d.year,d.planting_aligned_dose_mgy/1000,color='#163D64',lw=3,marker='o')
axes[0].set_ylabel('Total dose\n(billion gal/year)');axes[0].set_ylim(0,5)
axes[0].set_title('Total eligible capacity before planting',loc='left',fontsize=14)
axes[1].bar(d.year,d.new_eligibility_mgy/1000,color='#D17B28',label='New pathway eligibility')
axes[1].bar(d.year,d.existing_eligible_capacity_change_mgy/1000,bottom=d.new_eligibility_mgy/1000,color='#163D64',label='Capacity change at already eligible plants')
axes[1].set_ylabel('Annual change\n(billion gal/year)');axes[1].set_title('What adds to the dose each crop year?',loc='left',fontsize=14)
axes[1].legend(frameon=False,loc='upper left',fontsize=10)
axes[1].set_xticks(range(2014,2025));axes[1].set_xlabel('Crop year')
for ax in axes:ax.grid(axis='y',alpha=.16);ax.set_axisbelow(True)
fig.suptitle('LCFS capacity dose aligned with soybean planting',x=.09,ha='left',fontsize=20,weight='bold',y=.97)
fig.subplots_adjust(left=.10,right=.97,top=.85,bottom=.22,hspace=.42)
fig.text(.10,.055,'Eligibility: first observed soybean approval by May 1. Capacity: previous calendar year.\nAnnual change is constructed eligible capacity, not actual production or newly built capacity.\n16 mapped plants; Sinclair mapping provisional. Early zeros reflect the approval snapshot.',fontsize=10,color='#555555',linespacing=1.4)
for ext in ['png','pdf']:fig.savefig(out/f'lcfs_preplant_dose_and_annual_change.{ext}',dpi=200,facecolor='white')
print(d.to_string(index=False))

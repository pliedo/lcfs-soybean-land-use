"""Prespecified absolute road-distance exposure checks; all results reported."""
from pathlib import Path
import importlib,numpy as np,pandas as pd
m=importlib.import_module('17_estimate_distance_dose');R=Path(__file__).resolve().parents[1];C=R/'data/clean';O=R/'output/tables'
d=pd.read_csv(C/'refinery_crusher_distances_physical.csv');c=pd.read_csv(C/'lcfs_preplant_capacity_dose_scenarios.csv');c=c[c.scenario=='physical_onset_snapshot_capacity'];y=pd.read_csv(C/'crop_outcomes_exclusive.csv');y=y[y.year>=2014].copy()
rows=[];exposures=[];weights=[]
for name in ['absolute_exp_50mi','absolute_exp_150mi','absolute_exp_300mi','absolute_cutoff_100mi','absolute_cutoff_250mi','absolute_cutoff_500mi','absolute_cutoff_1000mi','absolute_exp150_sum1']:
 w=d[['hub_id','physical_plant_id']].copy();dist=d.road_km/1.609344
 if 'cutoff' in name:v=(dist<=float(name.split('_')[-1].replace('mi',''))).astype(float)
 else:
  scale=150 if name.endswith('sum1') else float(name.split('_')[-1].replace('mi',''));v=np.exp(-dist/scale)
  if name.endswith('sum1'):v=v/v.groupby(d.physical_plant_id).transform('sum')
 w['weight']=v;w['rule']=name;weights.append(w)
 a=w.merge(c,on='physical_plant_id');a['dose_100mgy']=a.weight*a.planting_aligned_dose_mgy/100;e=a.groupby(['hub_id','year'],as_index=False).dose_100mgy.sum().sort_values(['hub_id','year']);e['rule']=name
 for k in [1,2,3]:e[f'lag{k}']=e.groupby('hub_id').dose_100mgy.shift(k)
 exposures.append(e);p=y.merge(e,on=['hub_id','year'],validate='many_to_one')
 for ring in range(1,7):
  for spec,cols,trend in [('current',['dose_100mgy'],False),('lag1',['lag1'],False),('lag2',['lag2'],False),('lag3',['lag3'],False),('distributed_0_2',['dose_100mgy','lag1','lag2'],False),('hub_trends',['dose_100mgy'],True)]:
   m.FE_CACHE.clear()
   for r in m.fit(p[p.ring_index==ring],'soy_share_all_land',cols,trend):r.update(rule=name,ring=ring,specification=spec);rows.append(r)
r=pd.DataFrame(rows);r.to_csv(O/'absolute_distance_robustness.csv',index=False);pd.concat(exposures).to_csv(C/'crusher_year_absolute_distance_exposure.csv',index=False);pd.concat(weights).to_csv(C/'refinery_crusher_absolute_distance_weights.csv',index=False)
print('Rows',len(r));print(r[(r.specification=='current')].pivot(index='rule',columns='ring',values='beta_pp_per_100mgy').round(4).to_string());print('Positive significant single-dose models:',len(r[r.specification.isin(['current','lag1','lag2','lag3'])&(r.beta_pp_per_100mgy>0)&(r.p_value<.05)]))

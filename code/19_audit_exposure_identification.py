"""Trace TWFE numerator, leave-one-out estimates and timing conventions."""
from pathlib import Path
import importlib,numpy as np,pandas as pd
m=importlib.import_module('17_estimate_distance_dose');R=Path(__file__).resolve().parents[1];C=R/'data/clean';O=R/'output/tables';O.mkdir(exist_ok=True)
y=pd.read_csv(C/'crop_outcomes_exclusive.csv');y=y[y.year>=2014].copy()
e=pd.read_csv(C/'crusher_year_lcfs_exposure_scenarios.csv');e=e[(e.scenario=='physical_onset_snapshot_capacity')&(e.distance_metric=='road_km')&(e.weight_rule=='exp_150mi')]
p=y.merge(e,on=['hub_id','year'],validate='many_to_one')
w=pd.read_csv(C/'refinery_crusher_weights_baseline.csv');c=pd.read_csv(C/'lcfs_preplant_capacity_dose_scenarios.csv');c=c[c.scenario=='physical_onset_snapshot_capacity']
a=w[['hub_id','physical_plant_id','exp_150mi']].merge(c,on='physical_plant_id');a['contribution']=a.exp_150mi*a.planting_aligned_dose_mgy/100
wide=a.pivot(index=['hub_id','year'],columns='physical_plant_id',values='contribution').reset_index();plants=list(wide.columns[2:]);p=p.merge(wide,on=['hub_id','year'],validate='many_to_one')
assert np.allclose(p[plants].sum(axis=1),p.dose_100mgy)
# Avoid FE cache reuse across different row identities in leave-one-out panels.
def fit(d,cols=['dose_100mgy']):
 m.FE_CACHE.clear();return m.fit(d,'soy_share_all_land',cols)
def residual(v,F):return v-F@np.linalg.lstsq(F,v,rcond=None)[0]
trace=[];loo=[];timing=[]
for ring in range(1,7):
 d=p[(p.ring_index==ring)&p.soy_share_all_land.notna()].copy()
 F=np.column_stack([np.ones(len(d)),pd.get_dummies(d.hub_id,drop_first=True,dtype=float),pd.get_dummies(d.year,drop_first=True,dtype=float)])
 yr=residual(d.soy_share_all_land.to_numpy()*100,F);xr=residual(d.dose_100mgy.to_numpy(),F);den=xr@xr
 for kind,col,vals in [('year','year',d.year.unique()),('hub','hub_id',d.hub_id.unique())]:
  for val in vals:
   mask=d[col].to_numpy()==val;trace.append(dict(ring=ring,kind=kind,item=str(val),coefficient_contribution=float((xr[mask]@yr[mask])/den)))
   for z in fit(d[~mask]):z.update(ring=ring,omission_kind=kind,omitted=str(val));loo.append(z)
 for plant in plants:
  pr=residual(d[plant].to_numpy(),F);trace.append(dict(ring=ring,kind='plant',item=plant,coefficient_contribution=float(pr@yr/den)))
  dd=d.copy();dd['dose_100mgy']=dd.dose_100mgy-dd[plant]
  for z in fit(dd):z.update(ring=ring,omission_kind='plant',omitted=plant);loo.append(z)
 # Same 2017–2021 sample supports all ±3-year comparisons.
 for spec,col in [('current','dose_100mgy'),('lag1','dose_lag1'),('lag2','dose_lag2'),('lag3','dose_lag3')]:
  for z in fit(d[d.year.between(2017,2021)],[col]):z.update(ring=ring,test='common_sample_2017_2021',specification=spec);timing.append(z)
 # Leads join explicitly by hub and future year, never row offsets across hubs.
 for k in [1,2,3]:
  future=e[['hub_id','year','dose_100mgy']].copy();future.year-=k;future=future.rename(columns={'dose_100mgy':f'lead{k}'})
  dd=d.merge(future,on=['hub_id','year'],validate='many_to_one')
  for z in fit(dd[dd.year.between(2017,2021)],[f'lead{k}']):z.update(ring=ring,test='common_sample_2017_2021',specification=f'lead{k}');timing.append(z)
for convention in ['calendar_dose_mgy','planting_cutoff_dose_mgy','next_year_dose_mgy']:
 aa=a.copy();aa['v']=aa.exp_150mi*aa[convention]/100
 ee=aa.groupby(['hub_id','year'],as_index=False).v.sum().rename(columns={'v':'alternative_dose'})
 dd=y.merge(ee,on=['hub_id','year'],validate='many_to_one')
 for ring in range(1,7):
  for z in fit(dd[dd.ring_index==ring],['alternative_dose']):z.update(ring=ring,test='capacity_timing',specification=convention);timing.append(z)
pd.DataFrame(trace).to_csv(O/'exposure_covariance_decomposition.csv',index=False)
pd.DataFrame(loo).to_csv(O/'exposure_leave_one_out.csv',index=False)
pd.DataFrame(timing).to_csv(O/'exposure_timing_audit.csv',index=False)
# National annual dose increments by physical plant, with dates and capacity sources.
cc=c.sort_values(['physical_plant_id','year']).copy();cc['annual_change_mgy']=cc.groupby('physical_plant_id').planting_aligned_dose_mgy.diff();cc.to_csv(O/'exposure_plant_timing_history.csv',index=False)
print('Audit complete:',len(trace),'decomposition rows;',len(loo),'leave-one-out coefficients')

import sys,importlib,pandas as pd
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'code'));m=importlib.import_module('17_estimate_distance_dose');C=str(ROOT/'data/clean')+'/'
c=pd.read_csv(C+'lcfs_preplant_capacity_dose_scenarios.csv');c=c[c.scenario=='physical_onset_snapshot_capacity'].copy();w=pd.read_csv(C+'refinery_crusher_weights_baseline.csv');y=pd.read_csv(C+'crop_outcomes_exclusive.csv');y=y[y.year>=2014]
# Explicit sensitivity, not a replacement for the source series.
c.loc[(c.physical_plant_id=='Diamond Green Diesel LLC (81496)')&c.year.isin([2017,2018]),'planting_aligned_dose_mgy']=160
c.loc[(c.physical_plant_id=='Diamond Green Diesel LLC (81496)')&(c.year==2019),'planting_aligned_dose_mgy']=275
c.loc[(c.physical_plant_id=='Diamond Green Diesel LLC (81496)')&(c.year==2021),'planting_aligned_dose_mgy']=290
c.loc[(c.physical_plant_id=='Diamond Green Diesel LLC (81496)')&c.year.between(2022,2024),'planting_aligned_dose_mgy']=700
c.loc[c.physical_plant_id.str.contains('82621')&(c.year==2024),'planting_aligned_dose_mgy']=470
a=w[['hub_id','physical_plant_id','exp_150mi']].merge(c,on='physical_plant_id');a['dose_100mgy']=a.exp_150mi*a.planting_aligned_dose_mgy/100;e=a.groupby(['hub_id','year'],as_index=False).dose_100mgy.sum();d=y.merge(e,on=['hub_id','year']);rows=[]
for ring in range(1,7):
 m.FE_CACHE.clear()
 for r in m.fit(d[d.ring_index==ring],'soy_share_all_land',['dose_100mgy']):r['ring']=ring;rows.append(r)
r=pd.DataFrame(rows);r.to_csv(ROOT/'output/tables/exposure_dgd_capacity_sensitivity.csv',index=False);print(r[['ring','beta_pp_per_100mgy','ci_low','ci_high','p_value']].round(4).to_string(index=False))

"""Restrict ring-block pooled fits without recomputing identical ring slopes.

Ring-specific slopes, hub-ring FE and ring-year FE make normal equations
block diagonal by ring. Removing other rings leaves retained residuals/slopes
unchanged. Restriction changes clustered finite-sample correction and G.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import t
R=Path(__file__).resolve().parents[1];O=R/'output/tables'
p=pd.read_csv(O/'pooled_100mgy_cumulative_scenarios.csv.gz')
p=p[p.specification.isin(['current','lag1','lag2','distributed_0_2'])].copy()
y=pd.read_csv(R/'data/clean/crop_outcomes_exclusive.csv')
y=y[y.year.between(2014,2025)&y.all_valid_acres.gt(0)]
p['original_full_sample_p_value']=p.p_value
for (spec,outcome,cutoff),idx in p.groupby(['specification','outcome','outer_miles']).groups.items():
 start=2014 if spec=='current' else 2015 if spec=='lag1' else 2016
 a=y[y.year>=start].dropna(subset=[outcome]);small=a[a.outer_miles<=cutoff]
 terms=3 if spec=='distributed_0_2' else 1
 def correction(d):
  k=sum(g.hub_id.nunique()+g.year.nunique()-1+terms for _,g in d.groupby('ring_index'))
  n=len(d);G=d.hub_id.nunique()
  return G/(G-1)*(n-1)/(n-k)
 assert len(a)==int(p.loc[idx,'n'].iloc[0])
 G=small.hub_id.nunique()
 p.loc[idx,'se_acres']*=np.sqrt(correction(small)/correction(a))
 se=p.loc[idx,'se_acres'];b=p.loc[idx,'predicted_acres_change']
 p.loc[idx,'ci_low_acres']=b-t.ppf(.975,G-1)*se
 p.loc[idx,'ci_high_acres']=b+t.ppf(.975,G-1)*se
 p.loc[idx,'p_value']=2*t.sf(abs(b/se),G-1)
 p.loc[idx,'n']=len(small);p.loc[idx,'clusters']=G
p['fit_support']='Only hub-ring observations inside cumulative cutoff; ring-specific FE and slopes unchanged algebraically; restricted-sample cluster finite correction'
p.to_csv(O/'pooled_restricted_ring_scenarios.csv.gz',index=False,compression={'method':'gzip','mtime':0})
z=p[(p.scenario=='physical_onset_snapshot_capacity')&(p.physical_plant_id=='Phillips 66 Rodeo (82191)')]
z.to_csv(O/'pooled_restricted_Rodeo_lags_0_2.csv',index=False)
print(len(p),'restricted-support scenarios; no lag3 estimates')

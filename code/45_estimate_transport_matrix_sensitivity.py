"""Hold weights/specifications fixed while changing transport matrix construction."""
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import t
R=Path(__file__).resolve().parents[1];C=R/'data/clean';O=R/'output/tables'
y=pd.read_csv(C/'crop_outcomes_exclusive.csv');y=y[y.year.between(2014,2025)&y.all_valid_acres.gt(0)].copy();y['log_soy_acres']=np.log1p(y.soy_acres)
base=y[y.year==2024];mat=pd.read_csv(C/'transport_matrix_sensitivity_candidates.csv')
dose=pd.concat([pd.read_csv(C/'lcfs_preplant_capacity_dose_scenarios.csv').query('year<=2024'),pd.read_csv(C/'lcfs_2025_preplant_projection.csv')],ignore_index=True)
outcomes=['soy_share_all_land','soy_share_cropland','soy_acres','log_soy_acres'];coefs=[];preds=[];skipped=[]
def demean(a,g1,g2):
 a=a.copy()
 for _ in range(1000):
  old=a.copy()
  for g in [g1,g2]:
   sums=np.zeros((g.max()+1,a.shape[1]));np.add.at(sums,g,a);a-=sums[g]/np.bincount(g)[g,None]
  if np.max(abs(a-old))<1e-9:return a
 raise RuntimeError('FE convergence')
for matrix,w0 in mat.groupby('matrix_scenario',sort=False):
 for rule in ['relative_exp100','relative_inverse50','inverse50','inverse_square50','inverse_square50_sum1','absolute_exp100','exp100_sum1','nearest_eligible']:
  w=w0.copy();c=w.cost_proxy_truck_equivalent_km;eligible=c.notna()&c.gt(0);mn=c.groupby(w.physical_plant_id).transform('min');v=pd.Series(0.,index=w.index)
  if rule=='relative_exp100':v[eligible]=np.exp(-(c[eligible]-mn[eligible])/100)
  elif rule=='relative_inverse50':v[eligible]=(mn[eligible]+50)/(c[eligible]+50)
  elif rule=='inverse50':v[eligible]=50/(c[eligible]+50)
  elif rule in ['inverse_square50','inverse_square50_sum1']:v[eligible]=(50/(c[eligible]+50))**2
  elif rule=='nearest_eligible':v[eligible]=np.isclose(c[eligible],mn[eligible],atol=1e-8,rtol=0).astype(float)
  else:v[eligible]=np.exp(-c[eligible]/100)
  if rule in ['exp100_sum1','inverse_square50_sum1','nearest_eligible']:v/=v.groupby(w.physical_plant_id).transform('sum').replace(0,np.nan)
  w['weight']=v.fillna(0)
  assert w.groupby('physical_plant_id').weight.sum().gt(0).all()
  avg=w.groupby('hub_id',as_index=False).weight.mean();avg['physical_plant_id']='equal_location_average_16'
  targets=pd.concat([avg,w[w.physical_plant_id.isin(['Diamond Green Diesel LLC (81496)','Phillips 66 Rodeo (82191)','Marathon Dickinson Refinery (F00313)'])][['hub_id','physical_plant_id','weight']]])
  # Precompute aggregation contrasts; do not average correlated standard errors.
  Ls={}
  for plant,ww in targets.groupby('physical_plant_id'):
   for cutoff in [50,75]:
    bb=base[base.outer_miles<=cutoff].merge(ww[['hub_id','weight']],on='hub_id');L=np.zeros((3,6))
    for r in range(1,7):
     z=bb[bb.ring_index==r];L[:,r-1]=[(z.weight*z.all_valid_acres/100).sum(),(z.weight*z.cropland_acres/100).sum(),z.weight.sum()]
    Ls[plant,cutoff]=(L,bb.soy_acres.sum(),bb.all_valid_acres.sum())
  for scenario,dd in dose.groupby('scenario'):
   if scenario not in ['physical_onset_snapshot_capacity','exclude_both_disputed_sites']:continue
   j=w.merge(dd[['physical_plant_id','year','planting_aligned_dose_mgy']],on='physical_plant_id');j['dose']=j.weight*j.planting_aligned_dose_mgy/100
   e=j.groupby(['hub_id','year'],as_index=False).dose.sum().sort_values(['hub_id','year'])
   for k in [1,2]:e[f'lag{k}']=e.groupby('hub_id').dose.shift(k)
   p=y.merge(e,on=['hub_id','year'],validate='many_to_one')
   for spec,terms in [('current',['dose']),('lag1',['lag1']),('lag2',['lag2']),('distributed_0_2',['dose','lag1','lag2'])]:
    a=p.dropna(subset=terms+outcomes);names=[(term,r) for term in terms for r in range(1,7)]
    X=np.column_stack([a[term]*(a.ring_index==r) for term,r in names]);Y=a[outcomes].to_numpy();Y[:,:2]*=100
    g1=pd.factorize(pd.MultiIndex.from_arrays([a.hub_id,a.ring_index]))[0];g2=pd.factorize(pd.MultiIndex.from_arrays([a.ring_index,a.year]))[0]
    z=demean(np.column_stack([X,Y]),g1,g2);xx=z[:,:len(names)];yy=z[:,len(names):]
    if np.linalg.matrix_rank(xx)<len(names):skipped.append(dict(matrix_scenario=matrix,rule=rule,scenario=scenario,specification=spec,reason='residualized rank'));continue
    bread=np.linalg.inv(xx.T@xx);B=bread@xx.T@yy;res=yy-xx@B;hubs=a.hub_id.to_numpy();ids=np.unique(hubs);G=len(ids);N=len(a)
    K=sum(g.hub_id.nunique()+g.year.nunique()-1 for _,g in a.groupby('ring_index'))+len(names);corr=G/(G-1)*(N-1)/(N-K);crit=t.ppf(.975,G-1)
    for oi,outcome in enumerate(outcomes):
     b=B[:,oi];scores=np.stack([(xx[hubs==h]*res[hubs==h,oi,None]).sum(axis=0) for h in ids]);V=bread@scores.T@scores@bread*corr
     common=dict(matrix_scenario=matrix,rule=rule,scenario=scenario,specification=spec,outcome=outcome,n=N,clusters=G)
     for i,(term,r) in enumerate(names):
      se=np.sqrt(max(V[i,i],0));coefs.append(dict(**common,term=term,ring=r,beta=b[i],se=se,ci_low=b[i]-crit*se,ci_high=b[i]+crit*se,p_value=2*t.sf(abs(b[i]/se),G-1)))
     if oi==3:continue
     for (plant,cutoff),(ls,initial,area) in Ls.items():
      L=np.tile(ls[oi],len(terms));val=float(L@b);se=float(np.sqrt(max(L@V@L,0)))
      preds.append(dict(**common,physical_plant_id=plant,outer_miles=cutoff,added_capacity_mgy=100,predicted_acres_change=val,se_acres=se,ci_low_acres=val-crit*se,ci_high_acres=val+crit*se,p_value=2*t.sf(abs(val/se),G-1),relative_acres_change_percent=100*val/initial,share_change_pp=100*val/area))
 print('Finished matrix',matrix,flush=True)
pd.DataFrame(coefs).to_csv(O/'transport_matrix_sensitivity_coefficients.csv.gz',index=False,compression={'method':'gzip','mtime':0})
pd.DataFrame(preds).to_csv(O/'transport_matrix_sensitivity_scenarios.csv.gz',index=False,compression={'method':'gzip','mtime':0})
pd.DataFrame(skipped).to_csv(O/'transport_matrix_sensitivity_unidentified.csv',index=False)
p=pd.DataFrame(preds);p[(p.physical_plant_id=='equal_location_average_16')&(p.scenario=='physical_onset_snapshot_capacity')].to_csv(O/'transport_matrix_sensitivity_average_summary.csv',index=False)
print('Complete',len(coefs),'coefficients',len(preds),'location/average scenarios',len(skipped),'unidentified')

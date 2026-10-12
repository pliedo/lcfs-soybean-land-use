"""Hold weights/specifications fixed while changing transport matrix construction."""
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import t, f
R=Path(__file__).resolve().parents[1];C=R/'data/clean';O=R/'output/tables'
y=pd.read_csv(C/'crop_outcomes_nonwater_exclusive.csv');y=y[y.year.between(2014,2025)&y.nonwater_valid_acres.gt(0)].copy();y['log_soy_acres']=np.log1p(y.soy_acres)
base=y[y.year==2024];mat=pd.read_csv(C/'transport_matrix_sensitivity_candidates.csv.gz');mat=mat[mat.matrix_scenario.isin(['baseline','rail_rate_x0.5','rail_rate_x2'])].copy()
roads=pd.read_csv(C/'refinery_crusher_distances_physical.csv')
for label,col in [('road','road_km'),('geodesic','air_km')]:
 q=roads[['hub_id','physical_plant_id']].copy();q['cost_proxy_truck_equivalent_km']=roads[col];q['matrix_scenario']=label;mat=pd.concat([mat,q],ignore_index=True)
dose=pd.concat([pd.read_csv(C/'lcfs_preplant_capacity_dose_scenarios.csv').query('year<=2024'),pd.read_csv(C/'lcfs_2025_preplant_projection.csv')],ignore_index=True)
outcomes=['soy_share_nonwater','soy_acres'];coefs=[];preds=[];skipped=[];leadtests=[]
def demean(a,g1,g2):
 a=a.copy()
 for _ in range(1000):
  old=a.copy()
  for g in [g1,g2]:
   sums=np.zeros((g.max()+1,a.shape[1]));np.add.at(sums,g,a);a-=sums[g]/np.bincount(g)[g,None]
  if np.max(abs(a-old))<1e-9:return a
 raise RuntimeError('FE convergence')
for matrix,w0 in mat.groupby('matrix_scenario',sort=False):
 for rule in ['inverse_square50_sum1','exp100_sum1','nearest_eligible']:
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
    bb=base[base.outer_miles<=cutoff].merge(ww[['hub_id','weight']],on='hub_id');L=np.zeros((2,6))
    for r in range(1,7):
     z=bb[bb.ring_index==r];L[:,r-1]=[(z.weight*z.nonwater_valid_acres/100).sum(),z.weight.sum()]
    Ls[plant,cutoff]=(L,bb.soy_acres.sum(),bb.nonwater_valid_acres.sum())
  for scenario,dd in dose.groupby('scenario'):
   if scenario not in ['physical_onset_snapshot_capacity','exclude_both_disputed_sites']:continue
   j=w.merge(dd[['physical_plant_id','year','planting_aligned_dose_mgy']],on='physical_plant_id');j['dose']=j.weight*j.planting_aligned_dose_mgy/100
   e=j.groupby(['hub_id','year'],as_index=False).dose.sum().sort_values(['hub_id','year'])
   for k in [1,2]:
    e[f'lag{k}']=e.groupby('hub_id').dose.shift(k);e[f'lead{k}']=e.groupby('hub_id').dose.shift(-k)
   p=y.merge(e,on=['hub_id','year'],validate='many_to_one')
   p=p.dropna(subset=['lag1']+outcomes) # common lag-one sample across matrices
   for spec,terms in [('lag1',['lag1'])]:
    a=p.dropna(subset=terms+outcomes);names=[(term,r) for term in terms for r in range(1,7)]
    X=np.column_stack([a[term]*(a.ring_index==r) for term,r in names]);Y=a[outcomes].to_numpy(dtype=float,copy=True);Y[:,0]*=100
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
     if spec=='full_lead_lag':
      for label,selected in [('no_anticipation',['lead1','lead2']),('no_delayed_response',['lag1','lag2']),('no_post_eligibility_response',['dose','lag1','lag2'])]:
       for test_cutoff in [50,75,150]:
        ii=[i for i,(term,r) in enumerate(names) if term in selected and 25*r<=test_cutoff];q=len(ii);stat=float(b[ii]@np.linalg.pinv(V[np.ix_(ii,ii)])@b[ii]/q)
        leadtests.append(dict(**common,test=label,outer_miles=test_cutoff,statistic=stat,p_value=f.sf(stat,q,G-1),first_crop_year=int(a.year.min()),last_crop_year=int(a.year.max())))
     contrasts=[(term,[term]) for term in terms]+[('post_0_2',['dose','lag1','lag2']),('pre_leads',['lead1','lead2'])] if spec=='full_lead_lag' else [('model_total',terms)]
     for contrast,selected in contrasts:
      for (plant,cutoff),(ls,initial,area) in Ls.items():
       L=np.concatenate([ls[oi] if term in selected else np.zeros(6) for term in terms]);val=float(L@b);se=float(np.sqrt(max(L@V@L,0)))
       preds.append(dict(**common,contrast=contrast,physical_plant_id=plant,outer_miles=cutoff,added_capacity_mgy=100,predicted_acres_change=val,se_acres=se,ci_low_acres=val-crit*se,ci_high_acres=val+crit*se,p_value=2*t.sf(abs(val/se),G-1),relative_acres_change_percent=100*val/initial,share_change_pp=100*val/area,share_ci_low_pp=100*(val-crit*se)/area,share_ci_high_pp=100*(val+crit*se)/area,first_crop_year=int(a.year.min()),last_crop_year=int(a.year.max())))
 print('Finished matrix',matrix,flush=True)
pd.DataFrame(coefs).to_csv(O/'nonwater_lag1_matrix_coefficients.csv',index=False)
pd.DataFrame(preds).to_csv(O/'nonwater_lag1_matrix_contrasts.csv',index=False)
pd.DataFrame(skipped).to_csv(O/'nonwater_lag1_matrix_unidentified.csv',index=False)
p=pd.DataFrame(preds);p[(p.physical_plant_id=='equal_location_average_16')&(p.scenario=='physical_onset_snapshot_capacity')].to_csv(O/'nonwater_lag1_matrix_average_summary.csv',index=False)
print('Complete',len(coefs),'coefficients',len(preds),'location/average scenarios',len(skipped),'unidentified')

pd.DataFrame(leadtests).to_csv(O/'nonwater_lag1_matrix_joint_tests.csv',index=False)

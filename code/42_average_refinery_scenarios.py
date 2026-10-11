"""Pooled ring responses and 100-mgy refinery additions; no sign selection."""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import t, f
R=Path(__file__).resolve().parents[1]; C=R/'data/clean'; O=R/'output/tables'; O.mkdir(parents=True,exist_ok=True)
y=pd.read_csv(C/'crop_outcomes_exclusive.csv'); y=y[y.year.between(2014,2025)&y.all_valid_acres.gt(0)].copy()
y['log_soy_acres']=np.log1p(y.soy_acres)
routes=pd.read_csv(C/'refinery_crusher_lowest_supported_mode_cost_candidates.csv')
dose=pd.concat([pd.read_csv(C/'lcfs_preplant_capacity_dose_scenarios.csv').query('year<=2024'),pd.read_csv(C/'lcfs_2025_preplant_projection.csv')],ignore_index=True)
assert not dose.duplicated(['scenario','physical_plant_id','year']).any()
base=y[y.year==2024].copy(); assert not base.duplicated(['hub_id','ring_index']).any()
coef=[]; predictions=[]; tests=[]; leads=[]
def residualize(a,groups):
 a=a.copy()
 for it in range(1000):
  old=a.copy()
  for g in groups:
   sums=np.zeros((g.max()+1,a.shape[1]));np.add.at(sums,g,a);counts=np.bincount(g)
   a-=sums[g]/counts[g,None]
  if np.max(np.abs(a-old))<1e-9:return a
 raise RuntimeError('FE demeaning did not converge')
for rule in ['relative_exp100','relative_inverse50','inverse50','inverse_square50','absolute_exp100','exp100_sum1','nearest_eligible']:
 w=routes.copy(); cost=w.cost_proxy_truck_equivalent_km; mn=cost.groupby(w.physical_plant_id).transform('min')
 if rule=='relative_exp100': w['weight']=np.exp(-(cost-mn)/100)
 elif rule=='relative_inverse50':w['weight']=(mn+50)/(cost+50)
 elif rule=='inverse50':w['weight']=50/(cost+50)
 elif rule=='inverse_square50':w['weight']=(50/(cost+50))**2
 elif rule=='nearest_eligible':w['weight']=np.isclose(cost,mn,atol=1e-8,rtol=0).astype(float)
 else:w['weight']=np.exp(-cost/100)
 if rule in ['exp100_sum1','nearest_eligible']:w['weight']/=w.weight.groupby(w.physical_plant_id).transform('sum')
 for scenario,dd in dose.groupby('scenario'):
  if scenario not in ['physical_onset_snapshot_capacity','exclude_both_disputed_sites']:continue
  j=w.merge(dd[['physical_plant_id','year','planting_aligned_dose_mgy']],on='physical_plant_id'); j['dose']=j.weight*j.planting_aligned_dose_mgy/100
  e=j.groupby(['hub_id','year'],as_index=False).dose.sum().sort_values(['hub_id','year'])
  for k in [1,2,3]:e[f'lag{k}']=e.groupby('hub_id').dose.shift(k);e[f'lead{k}']=e.groupby('hub_id').dose.shift(-k)
  p=y.merge(e,on=['hub_id','year'],validate='many_to_one')
  for spec,terms in [('current',['dose']),('lag1',['lag1']),('lag2',['lag2']),('lag3',['lag3']),('distributed_0_2',['dose','lag1','lag2']),('joint_leads',['dose','lead1','lead2','lead3'])]:
   for outcome in ['soy_share_all_land','soy_share_cropland','soy_acres','log_soy_acres']:
    a=p.dropna(subset=terms+[outcome]).copy(); rings=a.ring_index.to_numpy(); names=[(term,r) for term in terms for r in range(1,7)]
    X=np.column_stack([a[term].to_numpy()*(rings==r) for term,r in names]);Y=a[outcome].to_numpy();Y=Y*100 if outcome.startswith('soy_share') else Y
    g1=pd.factorize(pd.MultiIndex.from_arrays([a.hub_id,a.ring_index]))[0];g2=pd.factorize(pd.MultiIndex.from_arrays([a.ring_index,a.year]))[0]
    z=residualize(np.column_stack([X,Y]),[g1,g2]);xx=z[:,:-1];yy=z[:,-1]
    if np.linalg.matrix_rank(xx)<xx.shape[1]:continue
    b=np.linalg.solve(xx.T@xx,xx.T@yy);res=yy-xx@b;bread=np.linalg.inv(xx.T@xx)
    hubs=a.hub_id.to_numpy(); ids=np.unique(hubs);G=len(ids);N=len(a)
    # Each ring's connected hub/year FE block has H+T-1 parameters.
    rankfe=sum(a[a.ring_index==r].hub_id.nunique()+a[a.ring_index==r].year.nunique()-1 for r in range(1,7));K=rankfe+len(b)
    score=np.stack([(xx[hubs==h]*res[hubs==h,None]).sum(axis=0) for h in ids]);V=bread@score.T@score@bread*(G/(G-1))*((N-1)/(N-K));crit=t.ppf(.975,G-1)
    common=dict(rule=rule,scenario=scenario,specification=spec,outcome=outcome,n=N,clusters=G)
    for i,(term,r) in enumerate(names):
     se=np.sqrt(max(V[i,i],0));coef.append(dict(**common,term=term,ring=r,beta=b[i],se=se,ci_low=b[i]-crit*se,ci_high=b[i]+crit*se,p_value=2*t.sf(abs(b[i]/se),G-1)))
    if spec=='joint_leads':
     ii=[i for i,(term,r) in enumerate(names) if term.startswith('lead')];v=V[np.ix_(ii,ii)];q=len(ii);stat=float(b[ii]@np.linalg.pinv(v)@b[ii]/q)
     tests.append(dict(**common,test='all_18_lead_interactions_zero',statistic=stat,p_value=f.sf(stat,q,G-1)))
     continue
    # Test inner 0-75 ring slopes against outer 75-150 slopes, equal ring weights.
    L=np.zeros(len(b)); L[:3]=1/3;L[3:6]=-1/3;se=np.sqrt(max(L@V@L,0));val=L@b
    tests.append(dict(**common,test='mean_inner_minus_mean_outer_first_term',estimate=val,se=se,p_value=2*t.sf(abs(val/se),G-1)))
    average=w.groupby('hub_id',as_index=False).weight.mean();average['physical_plant_id']='equal_location_average_16'
    prediction_weights=pd.concat([w[['hub_id','physical_plant_id','weight']],average],ignore_index=True)
    for plant,ww in prediction_weights.groupby('physical_plant_id'):
     for cutoff in range(1,7):
      qbase=base[base.ring_index<=cutoff].merge(ww[['hub_id','weight']],on='hub_id',validate='many_to_one');L=np.zeros(len(b))
      # Persistent 100-mgy eligible addition: single-lag response at selected lag;
      # distributed response once current and both lagged additions are active.
      for i,(term,r) in enumerate(names):
       zbase=qbase[qbase.ring_index==r]
       L[i]=(zbase.weight*zbase.all_valid_acres/100).sum() if outcome=='soy_share_all_land' else ((zbase.weight*zbase.cropland_acres/100).sum() if outcome=='soy_share_cropland' else zbase.weight.sum())
      if outcome=='log_soy_acres':continue # nonlinear aggregation needs bootstrap, not a linear contrast
      acres=float(L@b);se=float(np.sqrt(max(L@V@L,0)));total=qbase.all_valid_acres.sum();initial=qbase.soy_acres.sum()
      predictions.append(dict(**common,physical_plant_id=plant,outer_miles=25*cutoff,added_capacity_mgy=100,baseline_year=2024,baseline_soy_acres=initial,baseline_valid_acres=total,predicted_acres_change=acres,se_acres=se,ci_low_acres=acres-crit*se,ci_high_acres=acres+crit*se,p_value=2*t.sf(abs(acres/se),G-1),relative_acres_change_percent=100*acres/initial,share_change_pp=100*acres/total,baseline_share_percent=100*initial/total,predicted_share_percent=100*(initial+acres)/total))
# Save the average contrast separately; location uncertainty is shared, not independent.
ave=pd.DataFrame(predictions);ave=ave[ave.physical_plant_id=='equal_location_average_16']
ave.to_csv(O/'pooled_average_100mgy_refinery.csv',index=False)
predictions=[x for x in predictions if x['physical_plant_id']!='equal_location_average_16']
pd.DataFrame(coef).to_csv(O/'pooled_ring_capacity_coefficients.csv',index=False)
pred=pd.DataFrame(predictions)
pred[pred.outer_miles==150].to_csv(O/'pooled_100mgy_refinery_scenarios.csv',index=False)
pred.to_csv(O/'pooled_100mgy_cumulative_scenarios.csv.gz',index=False,compression={'method':'gzip','mtime':0})
pred[(pred.rule=='relative_exp100')&(pred.scenario=='physical_onset_snapshot_capacity')].to_csv(O/'pooled_100mgy_cumulative_focal.csv',index=False)
pd.DataFrame(tests).to_csv(O/'pooled_ring_capacity_joint_tests.csv',index=False)
z=pd.DataFrame(coef);z=z[z.term.str.startswith('lead')];z['positive_significant']=(z.beta>0)&(z.p_value<.05);z['negative_significant']=(z.beta<0)&(z.p_value<.05)
z.groupby(['outcome','term']).agg(models=('beta','size'),positive=('beta',lambda s:int((s>0).sum())),positive_significant=('positive_significant','sum'),negative_significant=('negative_significant','sum'),median_beta=('beta','median')).reset_index().to_csv(O/'pooled_lead_sign_magnitude_summary.csv',index=False)
print('Completed',len(coef),'coefficients',len(predictions),'100-mgy location scenarios')

from pathlib import Path
import pandas as pd,numpy as np
from scipy.stats import t
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];C=R/'data/clean';O=R/'output/tables'
m=pd.read_csv(C/'transport_matrix_sensitivity_candidates.csv.gz');m=m[m.matrix_scenario.isin(['baseline','rail_rate_x0.5','rail_rate_x2'])]
d=pd.read_csv(C/'refinery_crusher_distances_physical.csv')
for label,col in [('road','road_km'),('geodesic','air_km')]:
 q=d[['hub_id','physical_plant_id']].copy();q['cost_proxy_truck_equivalent_km']=d[col];q['matrix_scenario']=label;m=pd.concat([m,q],ignore_index=True)
cap=pd.read_csv(C/'lcfs_preplant_capacity_dose_scenarios.csv');cap=cap[(cap.scenario=='physical_onset_snapshot_capacity')&(cap.year==2024)].copy();cap['eligible_capacity']=cap.capacity_mgy.where(pd.to_datetime(cap.first_observed_soy_approval).dt.year<=2024,0)
y=pd.read_csv(C/'crop_outcomes_nonwater_exclusive.csv');y=y[(y.year==2024)&(y.nonwater_valid_acres>0)]
b=pd.read_csv(O/'nonwater_refinery_individual_rings_coefficients.csv.gz');b=b[(b.outcome=='soy_share_nonwater')&(b.scenario=='physical_onset_snapshot_capacity|approval_year')]
rows=[]
for matrix,w0 in m.groupby('matrix_scenario'):
 for rule in ['inverse_square50_sum1','exp100_sum1','nearest_eligible']:
  w=w0.copy();cost=w.cost_proxy_truck_equivalent_km;mn=cost.groupby(w.physical_plant_id).transform('min')
  raw=(50/(cost+50))**2 if rule=='inverse_square50_sum1' else np.exp(-cost/100) if rule=='exp100_sum1' else np.isclose(cost,mn,rtol=0,atol=1e-8).astype(float)
  w['raw']=raw;w['weight']=w.raw/w.groupby('physical_plant_id').raw.transform('sum');z=w.merge(cap[['physical_plant_id','eligible_capacity']],on='physical_plant_id');z['exposure']=z.weight*z.eligible_capacity/100;e=z.groupby('hub_id',as_index=False).exposure.sum()
  for spec,term in [('lag1_only','lag1'),('current_plus_lag1','current_plus_lag1_sum')]:
   bb=b[(b.matrix_scenario==matrix)&(b.rule==rule)&(b.specification==spec)&(b.term==term)]
   for _,r in bb.iterrows():
    a=y[y.ring_index==r.ring].merge(e,on='hub_id');area=a.nonwater_valid_acres.sum();L=(a.exposure*a.nonwater_valid_acres).sum()/area;val=L*r.beta;se=L*r.se;crit=t.ppf(.975,r.clusters-1);base=100*a.soy_acres.sum()/area
    rows.append(dict(matrix=matrix,rule=rule,specification=spec,ring=int(r.ring),eligible_capacity_mgy=cap.eligible_capacity.sum(),eligible_refineries=int(cap.eligible_capacity.gt(0).sum()),share_change_pp=val,ci_low=val-crit*se,ci_high=val+crit*se,p_value=r.p_value,baseline_2024_share_percent=base,illustrative_share_without_exposure_percent=base-val))
p=pd.DataFrame(rows);p.to_csv(O/'all_refineries_2024_capacity_ring_share_predictions.csv',index=False)
fig,axs=plt.subplots(1,2,figsize=(13,6),sharey=True)
for ax,(matrix,title) in zip(axs,[('road','Road distance'),('baseline','Mode-adjusted cost')]):
 for k,(spec,label,color) in enumerate([('lag1_only','Lag-one stock','#176c93'),('current_plus_lag1','Current + lag-one stock','#d47a18')]):
  q=p[(p.matrix==matrix)&(p.rule=='inverse_square50_sum1')&(p.specification==spec)].sort_values('ring');ax.errorbar(q.share_change_pp,np.arange(6)+(k-.5)*.16,xerr=[q.share_change_pp-q.ci_low,q.ci_high-q.share_change_pp],fmt='o',capsize=3,label=label,color=color)
 ax.axvline(0,color='gray',lw=1);ax.set_yticks(range(6),['0–25','25–50','50–75','75–100','100–125','125–150']);ax.invert_yaxis();ax.set_title(title);ax.set_xlabel('Predicted aggregate share contribution (pp)');ax.grid(axis='x',alpha=.15)
fig.suptitle(f'All {int(cap.eligible_capacity.gt(0).sum())} eligible refineries: {cap.eligible_capacity.sum():,.0f} million gallons/year',fontsize=17);axs[0].legend(frameon=False)
fig.text(.02,.02,'2024 observed eligible capacity and location weights; 2025 capacity held at 2024. Individual rings; area-weighted across crushers.\nModel-implied exposure contribution versus zero eligible exposure—not an identified national policy counterfactual. 95% coefficient-only intervals.',fontsize=10);fig.tight_layout(rect=(0,.10,1,.93))
for ext in ['png','pdf']:fig.savefig(R/f'output/figures/results/all_refineries_ring_share_predictions.{ext}',dpi=180)
print(p[(p.matrix=='road')&(p.rule=='inverse_square50_sum1')&(p.specification=='lag1_only')].to_string(index=False))

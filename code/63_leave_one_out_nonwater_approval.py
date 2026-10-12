"""Influence diagnostics; original data and weights retained, no selected exclusions."""
from pathlib import Path
import pandas as pd,numpy as np
from scipy.stats import t
R=Path(__file__).resolve().parents[1];C=R/'data/clean';O=R/'output/tables'
y=pd.read_csv(C/'crop_outcomes_nonwater_exclusive.csv');y=y[y.year.between(2016,2025)&y.nonwater_valid_acres.gt(0)].copy()
d=pd.concat([pd.read_csv(C/'lcfs_preplant_capacity_dose_scenarios.csv').query('year<=2024'),pd.read_csv(C/'lcfs_2025_preplant_projection.csv')],ignore_index=True);d=d[d.scenario=='physical_onset_snapshot_capacity'].copy();last=d[d.year==2024].set_index('physical_plant_id').capacity_mgy;d.loc[d.year==2025,'capacity_mgy']=d.loc[d.year==2025,'physical_plant_id'].map(last);d['cap']=d.capacity_mgy.where(d.year>=pd.to_datetime(d.first_observed_soy_approval).dt.year,0)
m=pd.read_csv(C/'transport_matrix_sensitivity_candidates.csv.gz').query("matrix_scenario=='baseline'");road=pd.read_csv(C/'refinery_crusher_distances_physical.csv');road['cost_proxy_truck_equivalent_km']=road.road_km;road['matrix_scenario']='road';m=pd.concat([m,road],ignore_index=True)
rows=[];skipped=[]
def demean(a,g1,g2):
 a=a.copy()
 for _ in range(100):
  old=a.copy()
  for g in [g1,g2]:
   sums=np.zeros((g.max()+1,a.shape[1]));np.add.at(sums,g,a);a-=sums[g]/np.bincount(g)[g,None]
  if np.max(abs(a-old))<1e-9:return a
 raise RuntimeError('FE convergence')
def fit(a,terms,meta):
 names=[(v,r) for v in terms for r in range(1,7)];X=np.column_stack([a[v]*(a.ring_index==r) for v,r in names]);Y=a.soy_share_nonwater.to_numpy()*100
 g1=pd.factorize(pd.MultiIndex.from_arrays([a.hub_id,a.ring_index]))[0];g2=pd.factorize(pd.MultiIndex.from_arrays([a.ring_index,a.year]))[0];z=demean(np.column_stack([X,Y]),g1,g2);x=z[:,:len(names)];yy=z[:,-1]
 if np.linalg.matrix_rank(x)<len(names):skipped.append(meta);return
 bread=np.linalg.inv(x.T@x);b=bread@x.T@yy;res=yy-x@b;h=a.hub_id.to_numpy();ids=np.unique(h);G=len(ids);N=len(a);K=sum(g.hub_id.nunique()+g.year.nunique()-1 for _,g in a.groupby('ring_index'))+len(names)
 score=np.stack([(x[h==i]*res[h==i,None]).sum(axis=0) for i in ids]);V=bread@score.T@score@bread*(G/(G-1)*(N-1)/(N-K));crit=t.ppf(.975,G-1)
 for term in terms+(['model_total'] if len(terms)>1 else []):
  group=[]
  for r in range(1,7):
   L=np.array([float(rr==r and (v==term or term=='model_total')) for v,rr in names]);val=L@b;se=np.sqrt(max(L@V@L,0));group.append(dict(**meta,term=term,ring=r,beta=val,se=se,ci_low=val-crit*se,ci_high=val+crit*se,p_value=2*t.sf(abs(val/se),G-1),n=N,clusters=G))
  order=np.argsort([g['p_value'] for g in group]);adjust=np.minimum(1,np.maximum.accumulate(np.array([group[i]['p_value'] for i in order])*np.arange(6,0,-1)))
  for i,padj in zip(order,adjust):group[i]['holm_p_six_rings']=padj
  rows.extend(group)
for matrix,w0 in m.groupby('matrix_scenario'):
 for rule in ['inverse_square50_sum1','exp100_sum1','nearest_eligible']:
  w=w0.copy();c=w.cost_proxy_truck_equivalent_km;mn=c.groupby(w.physical_plant_id).transform('min');w['raw']=(50/(c+50))**2 if rule=='inverse_square50_sum1' else np.exp(-c/100) if rule=='exp100_sum1' else np.isclose(c,mn,atol=1e-8,rtol=0).astype(float);w['weight']=w.raw/w.groupby('physical_plant_id').raw.transform('sum')
  j=w.merge(d[['physical_plant_id','year','cap']],on='physical_plant_id');j['dose']=j.weight*j.cap/100
  for excluded in ['']+sorted(d.physical_plant_id.unique()):
   jj=j if not excluded else j[j.physical_plant_id!=excluded];e=jj.groupby(['hub_id','year'],as_index=False).dose.sum().sort_values(['hub_id','year']);e['lag1']=e.groupby('hub_id').dose.shift(1);a=y.merge(e,on=['hub_id','year'],validate='many_to_one').dropna(subset=['dose','lag1'])
   for spec,terms in [('lag1_only',['lag1']),('current_plus_lag1',['dose','lag1'])]:
    meta=dict(matrix=matrix,rule=rule,specification=spec,sensitivity='baseline' if not excluded else 'leave_refinery_out',excluded=excluded);fit(a,terms,meta)
    if not excluded:
     for hub in sorted(a.hub_id.unique()):fit(a[a.hub_id!=hub],terms,dict(meta,sensitivity='leave_hub_out',excluded=str(hub)))
  print(matrix,rule,'completed',flush=True)
p=pd.DataFrame(rows);p.to_csv(O/'nonwater_approval_leave_one_out_coefficients.csv.gz',index=False,compression='gzip');pd.DataFrame(skipped).to_csv(O/'nonwater_approval_leave_one_out_unidentified.csv',index=False)
base=p[p.sensitivity=='baseline'];q=p.merge(base[['matrix','rule','specification','term','ring','beta','p_value']].rename(columns={'beta':'baseline_beta','p_value':'baseline_p'}),on=['matrix','rule','specification','term','ring']);q['shift']=q.beta-q.baseline_beta;q['sign_reversal']=q.beta*q.baseline_beta<0;q['nominal_sig']=q.p_value<.05
summ=q[q.sensitivity!='baseline'].groupby(['matrix','rule','specification','term','ring','sensitivity']).agg(baseline_beta=('baseline_beta','first'),baseline_p=('baseline_p','first'),beta_min=('beta','min'),beta_max=('beta','max'),exclusions=('beta','size'),sign_reversals=('sign_reversal','sum'),nominal_sig_count=('nominal_sig','sum')).reset_index();summ.to_csv(O/'nonwater_approval_leave_one_out_summary.csv',index=False)
i=q[q.sensitivity!='baseline'].copy();i['abs_shift']=i['shift'].abs();i=i.sort_values('abs_shift',ascending=False).groupby(['matrix','rule','specification','term','ring','sensitivity']).head(3);i.to_csv(O/'nonwater_approval_leave_one_out_top_influence.csv',index=False)
print('Complete',len(p),'rows;',len(skipped),'unidentified')

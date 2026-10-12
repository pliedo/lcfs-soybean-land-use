from pathlib import Path
import pandas as pd,numpy as np,matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];p=pd.read_csv(R/'output/tables/nonwater_refinery_individual_rings_average_summary.csv');p=p[p.outcome=='soy_share_nonwater'].copy()
y=pd.read_csv(R/'data/clean/crop_outcomes_nonwater_exclusive.csv');b=y[(y.year==2024)&(y.nonwater_valid_acres>0)].groupby('outer_miles')[['soy_acres','nonwater_valid_acres']].sum();p['baseline_share_percent']=p.outer_miles.map(100*b.soy_acres/b.nonwater_valid_acres);p['predicted_share_percent']=p.baseline_share_percent+p.share_change_pp
p['holm_p_six_rings']=np.nan
for _,g in p.groupby(['matrix_scenario','rule','scenario','specification','contrast']):
 order=g.sort_values('p_value');adj=np.maximum.accumulate(order.p_value.to_numpy()*np.arange(len(order),0,-1));p.loc[order.index,'holm_p_six_rings']=np.minimum(adj,1)
p.to_csv(R/'output/tables/refinery_100mgy_individual_ring_share_predictions.csv',index=False)
labels={'road':'Road','geodesic':'Straight line','baseline':'Mode cost','rail_rate_x0.5':'Rail cost ×0.5','rail_rate_x2':'Rail cost ×2'}
models=[('approval_year','lag1_only','model_total','Stock: lag one','#176c93'),('approval_year','current_plus_lag1','model_total','Stock: current + lag one','#d47a18'),('annual_change','lag1_only','model_total','Annual change: lag one','#795595')]
fig,axs=plt.subplots(2,3,figsize=(15,9))
for ax,ring in zip(axs.flat,[25,50,75,100,125,150]):
 for k,(timing,spec,contrast,name,color) in enumerate(models):
  q=p[(p.outer_miles==ring)&(p.rule=='inverse_square50_sum1')&(p.scenario=='physical_onset_snapshot_capacity|'+timing)&(p.specification==spec)&(p.contrast==contrast)].set_index('matrix_scenario').loc[list(labels)]
  ax.errorbar(q.share_change_pp,np.arange(5)+(k-1)*.20,xerr=[q.share_change_pp-q.share_ci_low_pp,q.share_ci_high_pp-q.share_change_pp],fmt='o',color=color,label=name,capsize=3)
 ax.axvline(0,color='gray',lw=1);ax.set_yticks(range(5),list(labels.values()));ax.invert_yaxis();ax.set_title(f'{ring-25}–{ring} miles');ax.set_xlabel('Aggregate share change within this ring (pp)');ax.grid(axis='x',alpha=.15)
fig.suptitle('A 100-million-gallon refinery approval: predicted share response by ring',fontsize=17)
fig.legend(*axs.flat[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,.95),ncol=3,frameon=False)
fig.text(.02,.015,'Average over 16 refinery locations; area-weighted across crushers within each individual ring, not combined across rings.\nNormalized inverse-square weights; matched 2016–2025 sample; 95% crusher-clustered intervals; nominal inference. Annual-change model predicts a one-time increment response.',fontsize=10)
fig.tight_layout(rect=(0,.07,1,.90))
for ext in ['png','pdf']:fig.savefig(R/f'output/figures/results/refinery_approval_individual_ring_sensitivity.{ext}',dpi=180)
for name in ['coefficients','contrasts']:
 z=R/f'output/tables/nonwater_refinery_individual_rings_{name}.csv';pd.read_csv(z).to_csv(str(z)+'.gz',index=False,compression='gzip')
q=p[(p.matrix_scenario=='road')&(p.rule=='inverse_square50_sum1')&(p.scenario=='physical_onset_snapshot_capacity|approval_year')&(p.specification=='lag1_only')];print(q[['outer_miles','share_change_pp','share_ci_low_pp','share_ci_high_pp','p_value','baseline_share_percent','predicted_share_percent']].to_string(index=False))

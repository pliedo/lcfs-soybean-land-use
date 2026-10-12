from pathlib import Path
import pandas as pd,numpy as np,matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];p=pd.read_csv(R/'output/tables/all_refineries_2024_capacity_ring_share_predictions.csv')
labels={'road':'Road','geodesic':'Straight line','baseline':'Mode cost','rail_rate_x0.5':'Rail cost ×0.5','rail_rate_x2':'Rail cost ×2'}
rules=[('inverse_square50_sum1','Inverse-square','#176c93'),('exp100_sum1','Exponential','#d47a18'),('nearest_eligible','Lowest-cost only','#795595')]
for spec,title in [('lag1_only','Lag-one stock'),('current_plus_lag1','Current + lag-one stock: combined response')]:
 fig,axs=plt.subplots(2,3,figsize=(15,9))
 for ax,ring in zip(axs.flat,range(1,7)):
  for k,(rule,name,color) in enumerate(rules):
   q=p[(p.ring==ring)&(p.rule==rule)&(p.specification==spec)].set_index('matrix').loc[list(labels)]
   ax.errorbar(q.share_change_pp,np.arange(5)+(k-1)*.2,xerr=[q.share_change_pp-q.ci_low,q.ci_high-q.share_change_pp],fmt='o',color=color,label=name,capsize=3)
  ax.axvline(0,color='gray',lw=1);ax.set_yticks(range(5),list(labels.values()));ax.invert_yaxis();ax.set_title(f'{(ring-1)*25}–{ring*25} miles');ax.set_xlabel('All-refinery share contribution (pp)');ax.grid(axis='x',alpha=.15)
 fig.suptitle('All 16 refineries, 5,108 million gal/year — '+title,fontsize=16)
 fig.legend(*axs.flat[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,.95),ncol=3,frameon=False)
 fig.text(.02,.015,'Actual 2024 eligible capacities and locations. Separate rings; 2024 non-water area weights; matched 2016–2025 sample.\n95% crusher-clustered coefficient-only intervals. Model-implied contribution versus zero exposure; no established national causal counterfactual.',fontsize=10)
 fig.tight_layout(rect=(0,.07,1,.90))
 for ext in ['png','pdf']:fig.savefig(R/f'output/figures/results/all_refinery_transport_sensitivity_{spec}.{ext}',dpi=180)
print(p.query("matrix=='road' and rule=='inverse_square50_sum1' and specification=='lag1_only'")[['ring','baseline_2024_share_percent','share_change_pp','illustrative_share_without_exposure_percent']].to_string(index=False))

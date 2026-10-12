from pathlib import Path
import pandas as pd,numpy as np,matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];O=R/'output/figures/results';O.mkdir(parents=True,exist_ok=True)
p=pd.read_csv(R/'output/tables/nonwater_lag1_matrix_average_summary.csv')
y=pd.read_csv(R/'data/clean/crop_outcomes_nonwater_exclusive.csv')
labels={'baseline':'Mode-adjusted cost','rail_rate_x0.5':'Cost: rail rate ×0.5','rail_rate_x2':'Cost: rail rate ×2','road':'Road distance','geodesic':'Straight-line distance'}
rules={'inverse_square50_sum1':('Inverse-square','#176a91'),'exp100_sum1':('Exponential','#cf7c19'),'nearest_eligible':('Lowest-cost only','#765692')}
fig,axes=plt.subplots(2,2,figsize=(14,9),sharex='row');rows=[]
for ci,cutoff in enumerate([50,75]):
 for ri,outcome in enumerate(['soy_share_nonwater','soy_acres']):
  ax=axes[ri,ci]
  for k,(rule,(name,color)) in enumerate(rules.items()):
   q=p[(p.rule==rule)&(p.outer_miles==cutoff)&(p.outcome==outcome)].set_index('matrix_scenario').loc[list(labels)]
   val=q.share_change_pp if ri==0 else q.predicted_acres_change/1000
   lo=q.share_ci_low_pp if ri==0 else q.ci_low_acres/1000;hi=q.share_ci_high_pp if ri==0 else q.ci_high_acres/1000
   pos=np.arange(5)+(k-1)*.2
   ax.errorbar(val,pos,xerr=[val-lo,hi-val],fmt='o',color=color,label=name,capsize=3,ms=5)
  ax.axvline(0,color='#888888',lw=1);ax.set_yticks(range(5),list(labels.values()));ax.invert_yaxis();ax.grid(axis='x',alpha=.18)
  ax.set_title(f'Cumulative 0–{cutoff} miles',fontsize=14)
  ax.set_xlabel('Change in soybean share (percentage points)' if ri==0 else 'Direct acreage estimate (thousand acres)')
  for spine in ['top','right']:ax.spines[spine].set_visible(False)
fig.suptitle('Simple lag-one model: sensitivity to transport matrix and weights',fontsize=18,y=.99)
fig.legend(*axes[0,0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,.955),ncol=3,frameon=False)
fig.text(.02,.018,'100 million gal/year added capacity, averaged equally over 16 refinery locations. 95% crusher-clustered intervals.\nSame 2015–2025 sample; crusher–ring and ring–year fixed effects. Non-water denominator; exploratory estimates, no multiple-testing adjustment.',fontsize=10)
fig.tight_layout(rect=(0,.07,1,.91))
for ext in ['png','pdf']:fig.savefig(O/f'nonwater_simple_lag1_matrix_comparison.{ext}',dpi=180)
for cutoff in [50,75]:
 b=y[(y.year==2024)&(y.outer_miles<=cutoff)&(y.nonwater_valid_acres>0)];area=b.nonwater_valid_acres.sum();soy=b.soy_acres.sum();baseline=100*soy/area
 for _,q in p[p.outer_miles==cutoff].iterrows():
  rows.append({**q.to_dict(),'baseline_2024_share_percent':baseline,'baseline_2024_soy_acres':soy,'baseline_2024_nonwater_acres':area,'illustrative_new_share_percent':baseline+q.share_change_pp if q.outcome=='soy_share_nonwater' else np.nan,'illustrative_new_soy_acres':soy+q.predicted_acres_change})
pd.DataFrame(rows).to_csv(R/'output/tables/nonwater_lag1_matrix_baseline_examples.csv',index=False)
print(p.query("matrix_scenario=='road' and rule=='inverse_square50_sum1'")[['outer_miles','outcome','predicted_acres_change','ci_low_acres','ci_high_acres','share_change_pp','p_value']].to_string(index=False))

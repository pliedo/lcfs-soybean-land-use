from pathlib import Path
import pandas as pd,numpy as np,matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];p=pd.read_csv(R/'output/tables/nonwater_stock_vs_changes_coefficients.csv');O=R/'output/figures/results'
fig,axs=plt.subplots(2,2,figsize=(13,8.2))
colors=['#5c7181','#176e9b','#d1791a']
for ci,(matrix,title) in enumerate([('road','Road distance'),('baseline','Mode-adjusted transport cost')]):
 for ri,outcome in enumerate(['soy_share_nonwater','soy_acres']):
  ax=axs[ri,ci]
  for k,(term,label) in enumerate([('approval_year','Stock: lag one'),('annual_change','Annual change: lag one')]):
   q=p[(p.matrix_scenario==matrix)&(p.rule=='inverse_square50_sum1')&(p.scenario=='physical_onset_snapshot_capacity|'+term)&(p.specification=='lag1_only')&(p.outcome==outcome)&(p.term=='lag1')].sort_values('ring');scale=1 if ri==0 else 1000
   ax.errorbar(q.beta/scale,np.arange(6)+(k-1)*.19,xerr=[(q.beta-q.ci_low)/scale,(q.ci_high-q.beta)/scale],fmt='o',color=colors[k],label=label,capsize=3)
  ax.axvline(0,color='gray',lw=1);ax.set_yticks(range(6),['0–25','25–50','50–75','75–100','100–125','125–150']);ax.invert_yaxis();ax.set_title(title);ax.set_ylabel('Distance ring (miles)');ax.set_xlabel('Soybean share: percentage points' if ri==0 else 'Soybean acres: thousands');ax.grid(axis='x',alpha=.15)
fig.suptitle('Approval-year exposure: lag-one stock versus annual changes',fontsize=17)
fig.legend(*axs[0,0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,.95),ncol=3,frameon=False)
fig.text(.02,.02,'Per 100 million gal/year of weighted crusher exposure; refinery-normalized inverse-square weights.\n2016–2025; crusher–ring and ring–year FE; 95% crusher-clustered intervals. These are ring coefficients, not average-refinery cumulative predictions.',fontsize=9.5)
fig.tight_layout(rect=(0,.08,1,.89))
for ext in ['png','pdf']:fig.savefig(O/f'approval_stock_vs_changes_all_rings.{ext}',dpi=180)
for name in ['coefficients','contrasts']:
 z=R/f'output/tables/nonwater_stock_vs_changes_{name}.csv';pd.read_csv(z).to_csv(str(z)+'.gz',index=False,compression='gzip')
q=p.query("matrix_scenario=='road' and rule=='inverse_square50_sum1' and scenario=='physical_onset_snapshot_capacity|approval_year' and outcome=='soy_share_nonwater'");print(q[['ring','term','beta','p_value']].to_string(index=False))

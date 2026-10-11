"""Report full sensitivity counts and four focal contrasts, without sign selection."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];O=R/'output/tables';F=R/'output/figures/results'
p=pd.read_csv(O/'transport_matrix_sensitivity_average_summary.csv')
q=p[p.outcome.isin(['soy_share_all_land','soy_acres'])].copy();q['positive_sig']=(q.predicted_acres_change>0)&(q.p_value<.05)
s=q.groupby(['rule','specification','outcome','outer_miles']).agg(matrices=('matrix_scenario','size'),positive=('predicted_acres_change',lambda s:int((s>0).sum())),positive_sig=('positive_sig','sum'),min_acres=('predicted_acres_change','min'),max_acres=('predicted_acres_change','max')).reset_index()
s.to_csv(O/'transport_matrix_sensitivity_stability.csv',index=False)
panels=[('inverse_square50_sum1','distributed_0_2','soy_share_all_land','Normalized inverse-square: share → acres'),('inverse_square50_sum1','distributed_0_2','soy_acres','Normalized inverse-square: direct acres'),('nearest_eligible','lag2','soy_share_all_land','Nearest crusher: share converted to acres'),('nearest_eligible','lag2','soy_acres','Nearest crusher: direct acres')]
fig,axes=plt.subplots(2,2,figsize=(16,9));fig.subplots_adjust(left=.18,right=.98,bottom=.15,top=.84,wspace=.32,hspace=.40)
labels={'baseline':'Baseline','truck_rate_x0.5':'Truck cost ×0.5','truck_rate_x2':'Truck cost ×2','rail_rate_x0.5':'Rail cost ×0.5','rail_rate_x2':'Rail cost ×2','barge_rate_x0.5':'Barge cost ×0.5','barge_rate_x2':'Barge cost ×2','ocean_rate_x0.5':'Ocean cost ×0.5','ocean_rate_x2':'Ocean cost ×2','assumed_transfer_fee_5':'Transfer fee $5/t','assumed_transfer_fee_15':'Transfer fee $15/t','no_Lemont_transfer_candidate':'Exclude Lemont candidate','no_StRose_truck_rail_candidate':'Exclude St Rose truck–rail'}
for ax,(rule,spec,outcome,title) in zip(axes.flat,panels):
 z=p[(p.rule==rule)&(p.specification==spec)&(p.outcome==outcome)&(p.outer_miles==75)].copy();ii=range(len(z))
 ax.errorbar(z.predicted_acres_change/1000,ii,xerr=[(z.predicted_acres_change-z.ci_low_acres)/1000,(z.ci_high_acres-z.predicted_acres_change)/1000],fmt='o',markersize=4,capsize=2,color='#176b87')
 ax.scatter(z.iloc[0].predicted_acres_change/1000,0,s=45,color='#db7b2b',zorder=5)
 ax.axvline(0,color='#888888',ls='--',lw=.8);ax.set_yticks(list(ii),[labels[x] for x in z.matrix_scenario],fontsize=8);ax.invert_yaxis();ax.set_title(title,fontsize=13);ax.spines[['top','right']].set_visible(False);ax.set_xlabel('Predicted additional soybean acres (thousands)',fontsize=10)
fig.suptitle('Transport-cost sensitivity: average +100 million gal/year, cumulative 0–75 miles',fontsize=19,y=.97)
fig.text(.05,.055,'Normalized inverse-square: distributed current + lags 1–2. Nearest allocation: lag 2. Full crusher-clustered 95% intervals.\nModal multipliers and transfer fees are assumed stress tests. Routes reselected within documented-mode candidate sets.\nFixed baseline truck-cost unit and decay scales. Equal mean across 16 refinery sites. Multiple testing; observational estimates.',fontsize=10,color='#555555')
for ext in ['png','pdf']:fig.savefig(F/f'transport_matrix_sensitivity_75mile.{ext}',dpi=180)

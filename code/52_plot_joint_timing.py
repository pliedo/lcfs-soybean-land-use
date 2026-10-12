"""Show conditional lead/lag coefficients and matched-sample timing evidence."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];O=R/'output/tables';F=R/'output/figures/results'
c=pd.read_csv(O/'nonwater_timing_coefficients.csv')
p=pd.read_csv(O/'nonwater_timing_average_summary.csv')
j=pd.read_csv(O/'nonwater_timing_joint_tests.csv')
focus=c[(c.scenario=='physical_onset_snapshot_capacity')&(c.rule=='inverse_square50_sum1')&(c.specification=='full_lead_lag')&(c.outcome=='soy_share_nonwater')&(c.ring<=3)].copy()
focus.to_csv(O/'nonwater_timing_focal_ring_coefficients.csv',index=False)
terms=['lead2','lead1','dose','lag1','lag2'];labels=['Lead 2','Lead 1','Current','Lag 1','Lag 2']
fig,axes=plt.subplots(1,3,figsize=(16,9),sharey=True);fig.subplots_adjust(left=.08,right=.98,top=.81,bottom=.25,wspace=.13)
for ax,ring in zip(axes,[1,2,3]):
 z=focus[focus.ring==ring].set_index('term').loc[terms]
 ax.errorbar(range(5),z.beta,yerr=[z.beta-z.ci_low,z.ci_high-z.beta],fmt='o',capsize=5,color='#176b87',markersize=7)
 ax.axhline(0,color='#888888',ls='--',lw=1);ax.axvline(1.5,color='#dddddd',lw=1);ax.set_xticks(range(5),labels,rotation=25);ax.set_title(f'{25*(ring-1)}–{25*ring} miles',fontsize=17);ax.spines[['top','right']].set_visible(False)
axes[0].set_ylabel('Soybean-share percentage points\nper 100 million gal/year weighted crusher exposure',fontsize=13)
fig.suptitle('Anticipation, current exposure and delayed response estimated jointly',fontsize=20,y=.96)
fig.text(.08,.12,'Normalized inverse-square transport-cost allocation. All five exposure terms enter the same regression.\nNon-water soybean share; crusher–ring and ring–year fixed effects; crusher-clustered 95% intervals.',fontsize=12)
fig.text(.08,.035,'2016–2023 common sample: two leads exclude 2024–2025 outcomes. Conditional stock-exposure coefficients, not an approval-event study.\nLag-one coefficients are contributions, not net one-year effects. Multiple testing; observational estimates.',fontsize=10,color='#555555')
F.mkdir(parents=True,exist_ok=True)
for ext in ['png','pdf']:fig.savefig(F/f'nonwater_joint_timing_first_three_rings.{ext}',dpi=180)
plt.close(fig)
fig,axes=plt.subplots(1,3,figsize=(16,9),sharey=False);fig.subplots_adjust(left=.08,right=.98,top=.80,bottom=.25,wspace=.30)
for ax,(rule,label) in zip(axes,[('inverse_square50_sum1','Normalized inverse-square'),('exp100_sum1','Normalized exponential'),('nearest_eligible','Nearest eligible crusher')]):
 z=p[(p.rule==rule)&(p.specification=='full_lead_lag')&(p.outcome=='soy_share_nonwater')&(p.outer_miles==75)].set_index('contrast').loc[terms]
 ax.errorbar(range(5),z.share_change_pp,yerr=[z.share_change_pp-z.share_ci_low_pp,z.share_ci_high_pp-z.share_change_pp],fmt='o',capsize=5,color='#176b87',markersize=7)
 ax.axhline(0,color='#888888',ls='--',lw=1);ax.set_xticks(range(5),labels,rotation=25);ax.set_title(label,fontsize=15);ax.spines[['top','right']].set_visible(False)
axes[0].set_ylabel('Share contribution, percentage points\n0–75-mile aggregate footprint',fontsize=12)
fig.suptitle('Conditional timing contributions: average +100 million gal/year addition',fontsize=20,y=.96)
fig.text(.08,.12,'Equal-location mean across 16 refinery sites; non-water share converted using 2024 polygon areas.\nAll leads and lags included jointly; crusher-clustered 95% intervals. Separate vertical scales.',fontsize=12)
fig.text(.08,.035,'2016–2023 common sample. Individual contributions must be combined to obtain a net response to a capacity path.\nFuture-exposure terms are diagnostics, not proof of anticipation. Multiple testing; observational estimates.',fontsize=10,color='#555555')
for ext in ['png','pdf']:fig.savefig(F/f'nonwater_joint_timing_average_contributions.{ext}',dpi=180)
# Lossless compressed copy for large contrasts; original CSV remains intact.
pd.read_csv(O/'nonwater_timing_contrasts.csv').to_csv(O/'nonwater_timing_contrasts.csv.gz',index=False,compression={'method':'gzip','mtime':0})
c.to_csv(O/'nonwater_timing_coefficients.csv.gz',index=False,compression={'method':'gzip','mtime':0})

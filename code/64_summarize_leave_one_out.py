from pathlib import Path
import pandas as pd,numpy as np,matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];O=R/'output/tables';p=pd.read_csv(O/'nonwater_approval_leave_one_out_coefficients.csv.gz');s=pd.read_csv(O/'nonwater_approval_leave_one_out_summary.csv');top=pd.read_csv(O/'nonwater_approval_leave_one_out_top_influence.csv')
fig,axs=plt.subplots(1,2,figsize=(13,6),sharey=True)
for ax,matrix,title in zip(axs,['road','baseline'],['Road','Mode-adjusted cost']):
 b=p[(p.matrix==matrix)&(p.rule=='inverse_square50_sum1')&(p.specification=='lag1_only')&(p.sensitivity=='baseline')].sort_values('ring');ax.errorbar(b.beta,np.arange(6)-.18,xerr=[b.beta-b.ci_low,b.ci_high-b.beta],fmt='o',color='#176c93',capsize=3,label='Baseline: 95% interval')
 for k,(sens,label,color) in enumerate([('leave_hub_out','Crusher exclusions: coefficient range','#d47a18'),('leave_refinery_out','Refinery exclusions: coefficient range','#795595')]):
  q=s[(s.matrix==matrix)&(s.rule=='inverse_square50_sum1')&(s.specification=='lag1_only')&(s.sensitivity==sens)].sort_values('ring');mid=(q.beta_min+q.beta_max)/2;ax.errorbar(mid,np.arange(6)+k*.18,xerr=[mid-q.beta_min,q.beta_max-mid],fmt='|',color=color,capsize=3,label=label)
 ax.axvline(0,color='gray',lw=1);ax.set_yticks(range(6),['0–25','25–50','50–75','75–100','100–125','125–150']);ax.set_title(title);ax.set_xlabel('Share coefficient (pp / 100 mgy weighted exposure)');ax.grid(axis='x',alpha=.15)
axs[0].invert_yaxis();fig.suptitle('Leave-one-out influence: current non-water approval-year stock model',fontsize=16);fig.legend(*axs[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,.95),ncol=1,frameon=False,fontsize=10)
fig.text(.02,.02,'Lag-one only; normalized inverse-square weights; 2016–2025. Orange/purple bars are coefficient ranges, NOT confidence intervals.\nRefinery exclusion removes its shock without reallocating weights. Baseline retained; no exclusion selected for sign or significance.',fontsize=10);fig.tight_layout(rect=(0,.1,1,.82))
for ext in ['png','pdf']:fig.savefig(R/f'output/figures/results/nonwater_approval_leave_one_out.{ext}',dpi=180)
report='''# Updated leave-one-out diagnostics

Source63: nonwater share only, approval-calendar eligible capacity stock; matched2016–2025, crusher-ring and ring-year FE, crusher clustered. Road and baseline mode-cost; inverse-square sum-normalized, exponential sum-normalized, nearest eligible. Lag1-only and current+lag1; record components and full-covariance sum. Each of57crusher exclusions removes outcomes; originalweights retained. Each16refinery exclusions removes its eligible capacity contribution, fixedweights, sameoutcomes. No shock redistribution. Baseline retained. 10656coefficientrows, zero unidentified. Baseline matches source57 within8.1e-16. Holm six-ring p retained but model search not adjusted.

Road inverse-square lag1-only: 0–25 baseline+.059166pp,p=.018688. 56of57hub exclusions remainpositive and nominallysignificant. Removinghub51 changescoefficient to-.199951pp,p=.882102, so sign flips but estimate is extremely imprecise; not evidence of negative causal effect. All16refinery exclusions keep signpositive;15significant. RemovingStBernard: +.048974,p=.088322. RemovingDiamondGreenDiesel: +.283554,p=.021296; coefficient increases because regressor/exposure changes, not comparable capacity-normalized procurement effect.

Mode-cost inverse-square 0–25 baseline+.111124pp,p=.380472; removinghub51 flips sign to-.433861; allotherspositive, none nominallysignificant. Allrefinery exclusionspositive but none significant. The single-hub influence warrants checking exposure concentration/identification, not automatic removal or an outcome-based exclusion.

Road andmodecost inverse-square lag1-only outer75–150coefficients remainnegative in everyhub/refineryexclusion. This rules out a single excluded unit as sufficient explanation, not confounding/mismeasured exposure/commonregiontrends. Roadsignificance survives56of57hubexclusions in eachouterring; modecost75–100 remainsimprecise.50–75sign fluctuates nearzero. Allrules/components in CSVs; do not infer significance fromrangeplots.

These diagnostics concern observational influence, not causalvalidation. Intervals conditionon matrix/capacity/measurement; no transportuncertainty. No winsorization, no outlier deletion inmainresults, no rasterrepeat. Code64plots baselineconfidenceintervalsandexclusioncoefficientranges distinctly.
'''
(R/'doc/nonwater-approval-leave-one-out.md').write_text(report)
print(s.query("ring==1 and specification=='lag1_only'")[['matrix','rule','sensitivity','sign_reversals','nominal_sig_count','exclusions']].to_string(index=False))

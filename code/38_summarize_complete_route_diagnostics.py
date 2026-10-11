"""Summarize complete route-cost diagnostics without selecting specifications by sign."""
from pathlib import Path
import pandas as pd, numpy as np
R=Path(__file__).resolve().parents[1]; O=R/"output"/"tables"
d=pd.read_csv(O/"complete_route_cost_influence_period_diagnostics.csv")
u=pd.read_csv(O/"complete_route_cost_diagnostic_unidentified.csv")
v=pd.read_csv(O/"complete_route_cost_exposure_variation.csv")
keys=["proxy","rule","ring","specification","outcome","term"]
base=d[d.sensitivity=="baseline"].copy()
base["nominal_sig"]=base.p_value.lt(.05)
summary=(base.groupby(["outcome","ring","specification"]).agg(models=("term","size"),median_beta=("beta_pp_per_100mgy","median"),positive_share=("beta_pp_per_100mgy",lambda x:(x>0).mean()),nominal_positive=("beta_pp_per_100mgy",lambda x:((x>0)&base.loc[x.index,"nominal_sig"]).sum()),nominal_negative=("beta_pp_per_100mgy",lambda x:((x<0)&base.loc[x.index,"nominal_sig"]).sum()),median_within_sd_effect=("within_sd_effect","median")).reset_index())
summary.to_csv(O/"complete_route_cost_baseline_diagnostic_summary.csv",index=False)
b=base[keys+["beta_pp_per_100mgy"]].rename(columns={"beta_pp_per_100mgy":"baseline_beta"})
c=d.merge(b,on=keys,how="left");c["sign_reversal"]=c.beta_pp_per_100mgy*c.baseline_beta<0
sens=(c[c.sensitivity!="baseline"].groupby("sensitivity").agg(models=("term","size"),matched=("baseline_beta","count"),sign_reversals=("sign_reversal","sum"),sign_reversal_share=("sign_reversal","mean")).reset_index())
sens.to_csv(O/"complete_route_cost_sensitivity_stability.csv",index=False)
lead=d[d.sensitivity=="anticipation_diagnostic"].copy();lead["nominal_sig"]=lead.p_value.lt(.05)
leadsum=(lead.groupby("term").agg(models=("term","size"),positive_share=("beta_pp_per_100mgy",lambda x:(x>0).mean()),nominal_significant=("nominal_sig","sum")).reset_index())
leadsum.to_csv(O/"complete_route_cost_lead_diagnostic_summary.csv",index=False)
ranges=(v.groupby(["proxy","rule"]).agg(exposure_sd_min=("exposure_sd","min"),exposure_sd_max=("exposure_sd","max"),lag_correlation_min=("lag1_lag2_correlation","min"),lag_correlation_max=("lag1_lag2_correlation","max"),within_covariance_min=("within_hub_covariance","min"),within_covariance_max=("within_hub_covariance","max")).reset_index())
ranges.to_csv(O/"complete_route_cost_exposure_variation_summary.csv",index=False)
def table(x): return x.to_markdown(index=False,floatfmt=".3g")
focus=summary[(summary.outcome.isin(["soy_share_all_land","soy_share_cropland"]))&(summary.specification.isin(["current","lag1"]))].copy()
report="""# Complete route-cost diagnostic evidence

This report summarizes a prespecified diagnostic grid; it does not select estimates for their sign or significance. Route weights measure potential exposure, not observed procurement. Nominal p-values are unadjusted and face extensive multiple testing.

## Baseline direction across route proxies and weights

Each cell summarizes baseline estimates across three route proxies and three weighting rules. Positive share is descriptive consistency, not a posterior probability. Coefficients remain in each outcome's native reported scale.

"""+table(focus)+"""

## Sensitivity stability

Sign reversals compare each sensitivity estimate with its exactly matched baseline. They diagnose fragility; they do not determine which estimate is correct.

"""+table(sens)+"""

## Lead and anticipation diagnostics

A significant lead would be inconsistent with a simple no-anticipation interpretation, but multiple testing and serially correlated exposure make isolated nominal significance weak evidence.

"""+table(leadsum)+"""

## Exposure identification

"""+table(ranges)+f"""

There are {len(d):,} estimated diagnostic coefficient rows and {len(u):,} unidentified specifications. Lag-1/lag-2 exposure correlations are high, so separate lag coefficients and distributed-lag components are difficult to interpret independently. Identifying variation is differential within-hub change after hub and year fixed effects, not the national soybean trend.

## Interpretation boundary

Closer-ring share estimates are often positive but imprecise, while outer-ring estimates are more often negative. Period, hub-trend, leave-one-hub and leave-one-refinery checks show meaningful sign instability in portions of the grid. The current evidence therefore does not establish that LCFS-linked capacity caused either an increase or decrease in soybean planting. Full coefficient files retain positive, negative and unidentified results. Empty exclusive polygons are excluded from acreage regressions rather than coded as zero production. Fixed valid-pixel counts are not proof of a fixed pixel mask; the separate six-band forest/classification audit remains the relevant validation.
"""
(R/"doc"/"complete-route-cost-diagnostic-evidence.md").write_text(report)
print({"rows":len(d),"unidentified":len(u),"baseline":len(base)})

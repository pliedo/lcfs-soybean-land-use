"""Predefined sensitivity diagnostics. Never exclude observations to obtain a sign."""
from pathlib import Path
import importlib,json
import numpy as np,pandas as pd
m=importlib.import_module("17_estimate_distance_dose");R=m.ROOT;C=m.CLEAN;O=m.OUT
def fit_record(data,outcome,cols,meta,rows,unidentified,trend=False):
 f=m.fit(data,outcome,cols,trend)
 if not f:unidentified.append(dict(**meta,outcome=outcome,reason="rank_or_sample_insufficient"))
 for row in f:
  row.update(meta);row["outcome"]=outcome;row["within_sd_effect"]=row["beta_pp_per_100mgy"]*row["within_exposure_sd"];rows.append(row)
def main():
 y=pd.read_csv(C/"crop_outcomes_exclusive.csv");y=y[y.year.between(2014,2025)].copy()
 y["log_soy_acres"]=np.log1p(y.soy_acres)/100;y["level_soy_acres"]=y.soy_acres/100
 support=y.groupby(["hub_id","ring_index"]).agg(years=("year","nunique"),min_valid=("all_valid_pixels","min"),max_valid=("all_valid_pixels","max"),min_crop=("cropland_pixels","min"),max_crop=("cropland_pixels","max")).reset_index()
 support["balanced_12year"]=support.years.eq(12);support["fixed_valid_support"]=support.min_valid.eq(support.max_valid)
 support.to_csv(O/"linehaul_land_support_audit.csv",index=False)
 base2014=y[y.year==2014][["hub_id","ring_index","all_valid_pixels"]].rename(columns={"all_valid_pixels":"valid2014"})
 y=y.merge(base2014,on=["hub_id","ring_index"],validate="many_to_one");y["soy_share_fixed2014_denominator"]=y.soy_pixels/y.valid2014.replace(0,np.nan)
 e=pd.read_csv(C/"crusher_year_linehaul_cost_exposure.csv")
 selected_proxies=["direct_truck","direct_rail","Rodeo_rail_gulf_marine_ocean1","Rodeo_river_gulf_marine_ocean1"]
 selected_rules=["relative_exp100","inverse50","exp100_sum1"]
 e=e[(e.scenario=="physical_onset_snapshot_capacity")&e.proxy.isin(selected_proxies)&e.rule.isin(selected_rules)]
 w=pd.read_csv(C/"refinery_crusher_linehaul_cost_weights.csv")
 dose=pd.concat([pd.read_csv(C/"lcfs_preplant_capacity_dose_scenarios.csv").query("year<=2024"),pd.read_csv(C/"lcfs_2025_preplant_projection.csv")])
 dose=dose[dose.scenario=="physical_onset_snapshot_capacity"]
 assert not dose.duplicated(["physical_plant_id","year"]).any()
 rows=[];unidentified=[];variation=[];leverage=[]
 for (proxy,rule),ee in e.groupby(["proxy","rule"]):
  ee=ee.sort_values(["hub_id","year"]).copy()
  for k in [2,3]:ee[f"lead{k}"]=ee.groupby("hub_id").dose.shift(-k)
  p=y.merge(ee,on=["hub_id","year"],validate="many_to_one")
  ww=w[(w.proxy==proxy)&(w.rule==rule)]
  contribution=ww.merge(dose[["physical_plant_id","year","planting_aligned_dose_mgy"]],on="physical_plant_id")
  contribution["contribution"]=contribution.weight*contribution.planting_aligned_dose_mgy/100
  assert not contribution.duplicated(["hub_id","physical_plant_id","year"]).any()
  for ring in range(1,7):
   b=p[p.ring_index==ring].copy();m.FE_CACHE.clear()
   between=b.groupby("hub_id")[["dose","soy_share_all_land"]].mean().cov().iloc[0,1]
   within=b[["dose","soy_share_all_land"]]-b.groupby("hub_id")[["dose","soy_share_all_land"]].transform("mean")
   variation.append(dict(proxy=proxy,rule=rule,ring=ring,between_covariance=between,within_hub_covariance=within.cov().iloc[0,1],exposure_sd=b.dose.std(),lag1_lag2_correlation=b[["lag1","lag2"]].corr().iloc[0,1],n=len(b),hubs=b.hub_id.nunique()))
   for hub,g in b.groupby("hub_id"):
    leverage.append(dict(proxy=proxy,rule=rule,ring=ring,hub_id=hub,exposure_max=g.dose.max(),exposure_change=g.dose.iloc[-1]-g.dose.iloc[0],soy_share_change=g.soy_share_all_land.iloc[-1]-g.soy_share_all_land.iloc[0],soy_share_min=g.soy_share_all_land.min(),soy_share_max=g.soy_share_all_land.max()))
   for outcome in ["soy_share_all_land","soy_share_cropland","log_soy_acres","level_soy_acres"]:
    for spec,col in [("current","dose"),("lag1","lag1")]:
     meta=dict(proxy=proxy,rule=rule,ring=ring,specification=spec)
     fit_record(b,outcome,[col],dict(**meta,sensitivity="baseline",excluded=""),rows,unidentified)
     for hub in sorted(b.hub_id.unique()):
      fit_record(b[b.hub_id!=hub],outcome,[col],dict(**meta,sensitivity="leave_one_hub_out",excluded=str(hub)),rows,unidentified)
     for plant,cc in contribution.groupby("physical_plant_id"):
      z=ee.merge(cc[["hub_id","year","contribution"]],on=["hub_id","year"],how="left",validate="one_to_one")
      z["dose"]=z.dose-z.contribution.fillna(0)
      z["lag1"]=z.groupby("hub_id").dose.shift(1)
      zz=y[y.ring_index==ring].merge(z[["hub_id","year","dose","lag1"]],on=["hub_id","year"],validate="many_to_one")
      fit_record(zz,outcome,[col],dict(**meta,sensitivity="leave_one_refinery_shock_out_fixed_weights",excluded=plant),rows,unidentified)
     for name,lo,hi in [("2014_2024",2014,2024),("2016_2025",2016,2025),("2014_2018",2014,2018),("2020_2025",2020,2025)]:
      fit_record(b[b.year.between(lo,hi)],outcome,[col],dict(**meta,sensitivity=name,excluded=""),rows,unidentified)
     fixed=support[(support.ring_index==ring)&support.balanced_12year&support.fixed_valid_support].hub_id
     fit_record(b[b.hub_id.isin(fixed)],outcome,[col],dict(**meta,sensitivity="balanced_fixed_valid_support",excluded=""),rows,unidentified)
     fit_record(b[~b.year.isin([2019,2021])],outcome,[col],dict(**meta,sensitivity="exclude2019_2021_classification_sensitivity",excluded="2019|2021"),rows,unidentified)
     fit_record(b,outcome,[col],dict(**meta,sensitivity="hub_linear_trends",excluded=""),rows,unidentified,True)
    fit_record(b,outcome,["dose","lead1","lead2","lead3"],dict(proxy=proxy,rule=rule,ring=ring,specification="leads1_3",sensitivity="anticipation_diagnostic",excluded=""),rows,unidentified)
   fit_record(b,"soy_share_fixed2014_denominator",["dose"],dict(proxy=proxy,rule=rule,ring=ring,specification="current",sensitivity="fixed2014_denominator_not_fixed_pixel_mask",excluded=""),rows,unidentified)
   print(proxy,rule,ring,len(rows),flush=True)
 pd.DataFrame(rows).to_csv(O/"linehaul_cost_influence_period_diagnostics.csv",index=False)
 pd.DataFrame(unidentified).to_csv(O/"linehaul_cost_diagnostic_unidentified.csv",index=False)
 pd.DataFrame(variation).to_csv(O/"linehaul_cost_exposure_variation.csv",index=False)
 pd.DataFrame(leverage).to_csv(O/"linehaul_cost_hub_outcome_leverage.csv",index=False)
 r=pd.DataFrame(rows);baseline=r[r.sensitivity=="baseline"]
 comparison=r.merge(baseline[["proxy","rule","ring","specification","outcome","term","beta_pp_per_100mgy"]].rename(columns={"beta_pp_per_100mgy":"baseline_beta"}),on=["proxy","rule","ring","specification","outcome","term"],how="left")
 comparison["delta_from_baseline"]=comparison.beta_pp_per_100mgy-comparison.baseline_beta
 comparison["sign_reversal"]=(comparison.beta_pp_per_100mgy*comparison.baseline_beta<0)
 comparison.groupby("sensitivity").agg(models=("term","size"),largest_absolute_shift=("delta_from_baseline",lambda x:x.abs().max()),sign_reversals=("sign_reversal","sum")).to_csv(O/"linehaul_cost_diagnostic_summary.csv")
 report="# Linehaul-proxy diagnostics\n\n"
 report+=f"Computed {len(rows)} coefficient rows and recorded {len(unidentified)} unidentified specifications. Baseline retained.\n\n"
 report+="Predefined focal grid: truck, rail, Rodeo rail-Gulf and river-Gulf alternatives; relative exponential, absolute inverse, sum-normalized exponential. Full original grid remains in linehaul_cost_dose_regressions_2025.csv. All six rings and four outcomes; current/lag1 influence; leads1–3 diagnostic. Leave-refinery-out removes its capacity contribution with weights held fixed, rather than reallocating it.\n\n"
 report+="Period windows are descriptive sensitivity checks, not selected for significance. Balanced fixed-valid-count support is not proof of an identical pixel mask. The fixed2014 denominator does not recover a fixed spatial land mask. Forest-specific evidence still requires class-transition or class-composition audit; omitting2019/2021 alone does not solve it.\n\n"
 report+="Inspect coefficient CSV, uncertainty, variation, and leverage together. Nominal p-values face multiple testing. These remain observational linehaul-proxy associations; routing, oil freight and identification limitations prevent causal claims. No winsorization or sign-based sample exclusion.\n"
 (R/"doc/linehaul-cost-diagnostics.md").write_text(report)
if __name__=="__main__":main()

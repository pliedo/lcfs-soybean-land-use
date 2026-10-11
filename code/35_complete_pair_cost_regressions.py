"""Exploratory transport exposure grid. Report all identified models, not selected signs."""
from pathlib import Path
import importlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
m=importlib.import_module("17_estimate_distance_dose")
R=Path(__file__).resolve().parents[1]; C=R/"data/clean"; O=R/"output/tables"; F=R/"output/figures/results"
O.mkdir(parents=True,exist_ok=True);F.mkdir(parents=True,exist_ok=True)
d=pd.read_csv(C/"refinery_crusher_transport_matrix.csv")
cross=pd.read_csv(C/"lcfs_physical_plant_crosswalk.csv").drop_duplicates("physical_plant_id")
ca=set(cross.loc[cross["Standard Location"].str.endswith(", CA"),"physical_plant_id"])
d["california"]=d.physical_plant_id.isin(ca)
assert len(d)==928 and not d.duplicated(["hub_id","physical_plant_id"]).any()
dose=pd.read_csv(C/"lcfs_preplant_capacity_dose_scenarios.csv")
project=pd.read_csv(C/"lcfs_2025_preplant_projection.csv")
dose=pd.concat([dose[dose.year<=2024],project],ignore_index=True)
dose=dose[dose.scenario.isin(["physical_onset_snapshot_capacity","exclude_both_disputed_sites"])]
assert not dose.duplicated(["scenario","physical_plant_id","year"]).any()
y=pd.read_csv(C/"crop_outcomes_exclusive.csv");y=y[y.year.between(2014,2025)].copy()
y["log_soy_acres"]=np.log1p(y.soy_acres)/100
y["level_soy_acres"]=y.soy_acres/100
routes=pd.read_csv(C/"refinery_crusher_transport_cost_matrix.csv")
proxies={}
def candidate(name,route,mult=1,rodeo_only=False):
 a=routes[(routes.route==route)&(routes.ocean_rate_multiplier==mult)].copy()
 if rodeo_only:a=a[a.physical_plant_id.str.contains("Rodeo",case=False)]
 a=a[a.access_screen_eligible.astype(str).str.lower().eq("true")]
 a=a[["hub_id","physical_plant_id","cost_proxy_truck_equivalent_km"]]
 return d[["hub_id","physical_plant_id"]].merge(a,on=["hub_id","physical_plant_id"],how="left",validate="one_to_one").cost_proxy_truck_equivalent_km
for route in ["direct_truck","direct_rail","inland_barge"]:
 v=candidate(route,route);proxies[route]=(v,v.notna())
for route in ["rail_gulf_marine","river_gulf_marine"]:
 for mult in [0.5,1,2]:
  direct=candidate("direct","direct_rail")
  gulf=candidate("gulf",route,mult,True)
  rodeo=d.physical_plant_id.str.contains("Rodeo",case=False)
  v=direct.where(~rodeo,gulf)
  proxies[f"Rodeo_{route}_ocean{mult}"]=(v,v.notna())
# These are linehaul proxy sensitivities, not the final full transportation matrix.

for terminal in ["Lemont","StRose"]:
 direct=candidate("direct","direct_rail")
 transfer=candidate("transfer","truck_"+terminal+"_rail")
 v=direct.fillna(transfer)
 proxies["rail_with_"+terminal+"_road_access"]=(v,v.notna())
for route in ["rail_Lemont_barge_StRose_marine_Rodeo","rail_via_Artesia_pretreatment"]:
 direct=candidate("direct","direct_rail")
 alt=candidate("alt",route)
 affected=d.physical_plant_id.str.contains("Rodeo",case=False) if "Lemont" in route else d.physical_plant_id.isin(["sinclair_wy","Cheyenne Renewable Diesel Company LLC (F00494)"])
 v=direct.where(~affected,alt)
 proxies[route]=(v,v.notna())

weights=[]; exposures=[]; results=[]; skipped=[]
for proxy,(distance,eligible) in proxies.items():
 distance=pd.Series(distance,index=d.index)
 eligible=pd.Series(eligible,index=d.index).astype(bool)&distance.notna()&(distance>0)
 for rule in ["relative_exp100","relative_inverse50","inverse50","inverse_square50","absolute_exp100","exp100_sum1","nearest_eligible"]:
  v=pd.Series(0.,index=d.index)
  minimum=distance.where(eligible).groupby(d.physical_plant_id).transform("min")
  if rule=="relative_exp100":v.loc[eligible]=np.exp(-(distance[eligible]-minimum[eligible])/100)
  elif rule=="relative_inverse50":v.loc[eligible]=(minimum[eligible]+50)/(distance[eligible]+50)
  elif rule=="inverse50":v.loc[eligible]=50/(distance[eligible]+50)
  elif rule=="inverse_square50":v.loc[eligible]=(50/(distance[eligible]+50))**2
  elif rule=="nearest_eligible":
   v.loc[eligible&distance.eq(minimum)]=1
   v=v/v.groupby(d.physical_plant_id).transform("sum").replace(0,np.nan);v=v.fillna(0)
  else:
   v.loc[eligible]=np.exp(-distance[eligible]/100)
   if rule.endswith("sum1"):v=v/v.groupby(d.physical_plant_id).transform("sum").replace(0,np.nan);v=v.fillna(0)
  w=d[["hub_id","physical_plant_id","california"]].copy();w["weight"]=v;w["proxy"]=proxy;w["rule"]=rule;weights.append(w)
  for scenario,c in dose.groupby("scenario"):
   a=w.merge(c[["physical_plant_id","year","planting_aligned_dose_mgy"]],on="physical_plant_id",validate="many_to_many")
   a["dose"]=a.weight*a.planting_aligned_dose_mgy/100
   a["ca_dose"]=a.dose*a.california
   e=a.groupby(["hub_id","year"],as_index=False)[["dose","ca_dose"]].sum().sort_values(["hub_id","year"])
   e["other_dose"]=e.dose-e.ca_dose
   for k in [1,2,3]:e[f"lag{k}"]=e.groupby("hub_id").dose.shift(k)
   e["lead1"]=e.groupby("hub_id").dose.shift(-1)
   e["proxy"]=proxy;e["rule"]=rule;e["scenario"]=scenario;exposures.append(e)
   p=y.merge(e,on=["hub_id","year"],validate="many_to_one")
   specs=[("current",["dose"],False,[]),("lag1",["lag1"],False,[]),("lag2",["lag2"],False,[]),("lag3",["lag3"],False,[]),("distributed_0_2",["dose","lag1","lag2"],False,[]),("lead_diagnostic",["dose","lead1"],False,[]),("hub_trends",["dose"],True,[]),("exclude2019",["dose"],False,[2019]),("CA_vs_other",["ca_dose","other_dose"],False,[])]
   for ring in range(1,7):
    base=p[p.ring_index==ring].copy()
    m.FE_CACHE.clear()
    for outcome in ["soy_share_all_land","soy_share_cropland","log_soy_acres","level_soy_acres"]:
     for spec,cols,trend,omit in specs:
      data=base[~base.year.isin(omit)]
      fitted=m.fit(data,outcome,cols,trend)
      if not fitted:skipped.append(dict(proxy=proxy,rule=rule,scenario=scenario,ring=ring,outcome=outcome,specification=spec,reason="insufficient observations or residualized rank"))
      for row in fitted:
       row.update(proxy=proxy,rule=rule,scenario=scenario,ring=ring,outcome=outcome,specification=spec,units="log points per 100mgy" if outcome=="log_soy_acres" else ("acres per 100mgy" if outcome=="level_soy_acres" else "percentage points per 100mgy"))
       results.append(row)
r=pd.DataFrame(results);r.to_csv(O/"complete_route_cost_dose_regressions_2025.csv",index=False)
pd.DataFrame(skipped).to_csv(O/"complete_route_cost_dose_unidentified_models.csv",index=False)
pd.concat(weights).to_csv(C/"refinery_crusher_complete_route_cost_weights.csv",index=False)
pd.concat(exposures).to_csv(C/"crusher_year_complete_route_cost_exposure.csv",index=False)
z=r[(r.scenario=="physical_onset_snapshot_capacity")&(r.outcome=="soy_share_all_land")&(r.specification=="lag1")&(r.rule=="relative_exp100")]
fig,axes=plt.subplots(4,4,figsize=(16,12),sharey=True)
for ax,(proxy,_) in zip(axes.flat,proxies.items()):
 a=z[z.proxy==proxy].sort_values("ring")
 if len(a):ax.errorbar(a.beta_pp_per_100mgy,a.ring,xerr=[a.beta_pp_per_100mgy-a.ci_low,a.ci_high-a.beta_pp_per_100mgy],fmt="o",capsize=3)
 ax.axvline(0,color="grey",ls=":");ax.set_title(proxy.replace("_"," "),fontsize=8);ax.set_yticks(range(1,7),[f"{25*(i-1)}–{25*i}" for i in range(1,7)]);ax.invert_yaxis()
fig.suptitle("Calibrated freight proxy sensitivity: one-year lag",fontsize=18)
fig.supxlabel("Soybean-share percentage points per 100 million gal/year exposure")
fig.tight_layout(rect=[0,.09,1,.94])
fig.text(.02,.015,"Exploratory TWFE, 2014–2025; crusher-clustered 95% intervals. Linehaul only; excludes handling/access. Multiple testing; not causal.\nRelative decay: 100 truck-equivalent km; assumed scale. 2025 dose uses 2024 capacity and known approval history.",fontsize=9)
for ext in ["png","pdf"]:fig.savefig(F/f"complete_route_cost_exposure_sensitivity_2025.{ext}",dpi=240)
print("Estimated coefficient rows",len(r),"unidentified models",len(skipped),flush=True)

summary=r.groupby(["proxy","rule","outcome","specification"]).agg(models=("p_value","size"),positive=("beta_pp_per_100mgy",lambda x:int((x>0).sum())),nominal_p_below_05=("p_value",lambda x:int((x<.05).sum()))).reset_index()
summary.to_csv(O/"complete_route_cost_model_inventory.csv",index=False)
report="# Complete-pair candidate route exposure grid\n\n"
report+=f"Estimated {len(r)} coefficient rows; {len(skipped)} unidentified models. All estimated specifications are exported.\n\n"
report+="These use source-calibrated broad-freight and grain-ocean linehaul proxies, excluding unmeasured access and handling. They are not total oil shipment costs. Gulf routes apply only to Rodeo; other plants retain direct rail. A separate scenario preserves Artesia as a pretreatment intermediate for Sinclair and Cheyenne. Alternatives do not substitute finished-fuel routes for feedstock routes. Alternatives are separate scenarios, never shipment shares. Access-screen exclusions are eligibility assumptions.\n\n"
report+="Crusher and year fixed effects; crusher-clustered intervals. Current, lag1/2/3, distributed0–2, lead diagnostic, hub trends, exclude2019, and California/other decomposition. Shares, log and level soybean acres. 2025 capacity is provisional. Offsets50 and decay100 truck-equivalent km are transparent assumed sensitivity scales. Nearest allocation splits tied minima evenly. Simultaneous physical refinery shocks are summed once per plant.\n\n"
report+="Nominal p-values are not adjusted for the many specifications. Observational coefficients are not established causal effects. Leave-one-out influence, balanced-support and forest-break diagnostics remain outstanding; do not treat this report as the final requested diagnostic report.\n"
(R/"doc/complete-route-cost-regression-status.md").write_text(report)

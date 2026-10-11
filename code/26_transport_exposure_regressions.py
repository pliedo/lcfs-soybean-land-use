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
y["log_soy_acres"]=np.log1p(y.soy_acres)/100 # fit multiplies outcome by 100
rail=d.rail_screen_5km.astype(str).str.lower().eq("true")
water=d.water_screen_10km.astype(str).str.lower().eq("true")
front=(d.crusher_riverfront.fillna(0).astype(float)>0)|(d.crusher_oceanfront.fillna(0).astype(float)>0)
proxies={
 "road":(d.road_km,np.ones(len(d))),
 "air":(d.air_km,np.ones(len(d))),
 "rail5":(d.rail_with_connectors_km,rail),
 "rail10":(d.rail_with_connectors_km,d.rail_screen_10km.astype(str).str.lower().eq("true")),
 "water10":(d.water_with_connectors_km,water),
 "road_or_rail5":(pd.concat([d.road_km,d.rail_with_connectors_km.where(rail)],axis=1).min(axis=1),np.ones(len(d))),
 "california_front_road":(d.road_km,(~d.california)|front),
 "california_front_rail":(d.rail_with_connectors_km,rail&((~d.california)|front)),
}
weights=[]; exposures=[]; results=[]; skipped=[]
for proxy,(distance,eligible) in proxies.items():
 distance=pd.Series(distance,index=d.index)
 eligible=pd.Series(eligible,index=d.index).astype(bool)&distance.notna()&(distance>0)
 for rule in ["relative_exp300mi","relative_inverse","absolute_exp1000mi","exp1000mi_sum1","access_only"]:
  v=pd.Series(0.,index=d.index)
  minimum=distance.where(eligible).groupby(d.physical_plant_id).transform("min")
  if rule=="relative_exp300mi":v.loc[eligible]=np.exp(-(distance[eligible]-minimum[eligible])/(300*1.609344))
  elif rule=="relative_inverse":v.loc[eligible]=minimum[eligible]/distance[eligible]
  elif rule=="access_only":v.loc[eligible]=1.
  else:
   v.loc[eligible]=np.exp(-distance[eligible]/(1000*1.609344))
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
    for outcome in ["soy_share_all_land","soy_share_cropland","log_soy_acres"]:
     for spec,cols,trend,omit in specs:
      data=base[~base.year.isin(omit)]
      fitted=m.fit(data,outcome,cols,trend)
      if not fitted:skipped.append(dict(proxy=proxy,rule=rule,scenario=scenario,ring=ring,outcome=outcome,specification=spec,reason="insufficient observations or residualized rank"))
      for row in fitted:
       row.update(proxy=proxy,rule=rule,scenario=scenario,ring=ring,outcome=outcome,specification=spec,units="log points per 100mgy" if outcome=="log_soy_acres" else "percentage points per 100mgy")
       results.append(row)
r=pd.DataFrame(results);r.to_csv(O/"transport_dose_regressions_2025.csv",index=False)
pd.DataFrame(skipped).to_csv(O/"transport_dose_unidentified_models.csv",index=False)
pd.concat(weights).to_csv(C/"refinery_crusher_transport_weights.csv",index=False)
pd.concat(exposures).to_csv(C/"crusher_year_transport_exposure.csv",index=False)
z=r[(r.scenario=="physical_onset_snapshot_capacity")&(r.outcome=="soy_share_all_land")&(r.specification=="lag1")&(r.rule=="relative_exp300mi")]
fig,axes=plt.subplots(2,4,figsize=(12.8,7.2),sharey=True)
for ax,(proxy,_) in zip(axes.flat,proxies.items()):
 a=z[z.proxy==proxy].sort_values("ring")
 if len(a):ax.errorbar(a.beta_pp_per_100mgy,a.ring,xerr=[a.beta_pp_per_100mgy-a.ci_low,a.ci_high-a.beta_pp_per_100mgy],fmt="o",capsize=3)
 ax.axvline(0,color="grey",ls=":");ax.set_title(proxy.replace("_"," "),fontsize=10);ax.set_yticks(range(1,7),[f"{25*(i-1)}–{25*i}" for i in range(1,7)]);ax.invert_yaxis()
fig.suptitle("Transport exposure sensitivity: one-year lag",fontsize=18)
fig.supxlabel("Soybean-share percentage points per 100 million gal/year exposure")
fig.tight_layout(rect=[0,.09,1,.94])
fig.text(.02,.015,"Exploratory TWFE, 2014–2025; crusher-clustered 95% intervals. Access proxies are not verified shipments.\nRelative decay: 300 mi. 2025 dose uses 2024 capacity and known approval history.",fontsize=9)
for ext in ["png","pdf"]:fig.savefig(F/f"transport_exposure_sensitivity_2025.{ext}",dpi=240)
print("Estimated coefficient rows",len(r),"unidentified models",len(skipped),flush=True)

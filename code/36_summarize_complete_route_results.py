"""Prespecified presentation display; every coefficient remains in full grid."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];O=R/"output/tables";F=R/"output/figures/results"
def main():
 r=pd.read_csv(O/"complete_route_cost_dose_regressions_2025.csv")
 r["positive"]=r.beta_pp_per_100mgy>0;r["nominal_p05"]=r.p_value<.05
 r.groupby(["proxy","rule","outcome","specification","scenario"]).agg(coefficients=("term","size"),positive=("positive","sum"),nominal_p05=("nominal_p05","sum"),min_n=("n","min"),max_n=("n","max")).reset_index().to_csv(O/"complete_route_cost_coefficient_inventory.csv",index=False)
 b=r[(r.scenario=="physical_onset_snapshot_capacity")&(r.proxy=="lowest_supported_mode_candidate")&(r.rule=="relative_exp100")&r.specification.isin(["current","lag1","lag2","lag3"])]
 b.to_csv(O/"complete_route_cost_focal_coefficient_table.csv",index=False)
 for outcome in ["soy_share_all_land","soy_share_cropland","log_soy_acres","level_soy_acres"]:
  fig,axes=plt.subplots(1,4,figsize=(12.8,7.2),sharey=True)
  for ax,spec in zip(axes,["current","lag1","lag2","lag3"]):
   z=b[(b.outcome==outcome)&(b.specification==spec)].sort_values("ring")
   ax.errorbar(z.beta_pp_per_100mgy,z.ring,xerr=[z.beta_pp_per_100mgy-z.ci_low,z.ci_high-z.beta_pp_per_100mgy],fmt="o",capsize=3,color="#164b73")
   ax.axvline(0,color="grey",ls=":");ax.set_title(spec);ax.set_yticks(range(1,7),[f"{25*(i-1)}–{25*i}" for i in range(1,7)]);ax.invert_yaxis()
  units="share percentage points" if "share" in outcome else ("log points" if outcome=="log_soy_acres" else "soybean acres")
  fig.suptitle(outcome.replace("_"," ").capitalize(),fontsize=21,x=.08,ha="left")
  fig.supxlabel(units+" per100 million gal/year weighted capacity")
  fig.subplots_adjust(left=.08,right=.98,top=.81,bottom=.25,wspace=.4)
  fig.text(.08,.07,"Lowest supported-mode candidate; relative exponential decay100 truck-equivalent km.\nCrusher/year FE; crusher-clustered95% intervals;2014–2025.2025 capacity provisional.\nInferred terminals; grain ocean proxy; handling excluded. Exploratory associations; multiple testing.",fontsize=9)
  for ext in ["png","pdf"]:fig.savefig(F/f"complete_route_cost_focal_{outcome}.{ext}",dpi=240)
  plt.close(fig)
 report="# Candidate route-cost evidence\n\n"
 report+=f"All {len(r):,} estimated coefficient rows retained. Separate CSV records unidentified models.\n\n"
 report+="Focal display is prespecified by route plausibility, never by sign: lowest eligible supported-mode candidate within an inferred terminal set; relative decay100 truck-equivalent km. This is not actual procurement or exhaustive route optimization.\n\n"
 report+=b[["outcome","specification","ring","beta_pp_per_100mgy","ci_low","ci_high","p_value","n","hubs","within_exposure_sd"]].to_markdown(index=False,floatfmt=".4g")+"\n\n"
 report+="Earlier linehaul influence diagnostics retain48,024 coefficients, but are not yet recomputed on this updated matrix. Their mixed outcome units must not be combined when comparing raw shifts. No winsorization or sign-based period selection.\n\n"
 report+="Forest evidence: see forest-classification-evidence.md. Inner-band paired2018–2019 audit found net forest-to-soy gain, not a source of soybean loss. Outer-band aggregate forest shifts do not prove conversion or establish paired transitions. Equal denominator counts do not establish a fixed pixel mask.\n\n"
 report+="Fixed effects identify differential within-hub changes, not the national upward trend. Exposure measures potential linkage, not procurement shares. Physical refinery shocks sum once. Nominal p-values face multiple testing; observational coefficients are not established causal effects. Grain freight, inferred terminals, unmeasured handling/access, spatial inference and fixed-mask validation remain limitations.\n"
 (R/"doc/complete-route-cost-evidence-report.md").write_text(report)
 print("Summarized",len(r),"coefficient rows",flush=True)
if __name__=="__main__":main()

"""Summarize paired 2018-2019 CDL transitions across six exclusive distance bands."""
from pathlib import Path
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];D=R/"output"/"diagnostics"
x=pd.read_csv(D/"cdl_2018_2019_all_bands_forest_transitions.csv")
c=pd.read_csv(D/"cdl_2018_2019_all_bands_forest_coverage.csv")
assert x[["hub_id","ring_index"]].drop_duplicates().shape[0]==348
assert c[["hub_id","ring_index"]].drop_duplicates().shape[0]==348
assert x.hub_id.nunique()==58 and x.ring_index.nunique()==6
forest=["deciduous_forest","evergreen_forest","mixed_forest"]
rows=[]
for ring,g in x.groupby("ring_index"):
 total=int(g.pixels.sum())
 def n(fr=None,to=None):
  z=g
  if fr is not None:z=z[z.from_2018.isin(fr)]
  if to is not None:z=z[z.to_2019.isin(to)]
  return int(z.pixels.sum())
 soy18=n(fr=["soy"]);soy19=n(to=["soy"])
 f18=n(fr=forest);f19=n(to=forest)
 rows.append(dict(ring_index=ring,common_pixels=total,soy_2018=soy18,soy_2019=soy19,
  soy_change_pixels=soy19-soy18,soy_change_pp=100*(soy19-soy18)/total,
  forest_2018=f18,forest_2019=f19,forest_change_pixels=f19-f18,
  forest_change_pp=100*(f19-f18)/total,forest_to_soy=n(fr=forest,to=["soy"]),
  soy_to_forest=n(fr=["soy"],to=forest),net_forest_to_soy=n(fr=forest,to=["soy"])-n(fr=["soy"],to=forest),
  mixed_forest_change_pp=100*(n(to=["mixed_forest"])-n(fr=["mixed_forest"]))/total,
  deciduous_forest_change_pp=100*(n(to=["deciduous_forest"])-n(fr=["deciduous_forest"]))/total))
s=pd.DataFrame(rows);s.to_csv(D/"cdl_2018_2019_forest_transition_summary_by_ring.csv",index=False)
loss=x[(x.from_2018=="soy")&(x.to_2019!="soy")].groupby(["ring_index","to_2019"],as_index=False).pixels.sum()
loss["share_of_soy_loss"]=loss.pixels/loss.groupby("ring_index").pixels.transform("sum")
loss.sort_values(["ring_index","pixels"],ascending=[True,False]).to_csv(D/"cdl_2018_2019_soy_loss_destinations_by_ring.csv",index=False)
fig,ax=plt.subplots(figsize=(12.8,7.2))
q=s.melt("ring_index",value_vars=["soy_change_pp","forest_change_pp","mixed_forest_change_pp","deciduous_forest_change_pp"],var_name="series",value_name="change_pp")
labels={1:"0–25",2:"25–50",3:"50–75",4:"75–100",5:"100–125",6:"125–150"}
names={"soy_change_pp":"Soybeans","forest_change_pp":"All forest","mixed_forest_change_pp":"Mixed forest","deciduous_forest_change_pp":"Deciduous forest"}
for key,g in q.groupby("series"):
 ax.plot(g.ring_index.map(labels),g.change_pp,marker="o",linewidth=2,label=names[key])
ax.axhline(0,color="#555",linewidth=.8);ax.set_ylabel("Change in share of common valid pixels (pp)")
ax.set_xlabel("Distance from assigned crusher (miles)");ax.set_title("Paired CDL transitions, 2018–2019")
ax.legend(frameon=False,ncol=2);ax.grid(axis="y",alpha=.2);fig.tight_layout()
fig.savefig(D/"cdl_2018_2019_forest_transition_evidence.png",dpi=220)
fig.savefig(D/"cdl_2018_2019_forest_transition_evidence.pdf")
forest_net=int(s.net_forest_to_soy.sum()); soy_net=int(s.soy_change_pixels.sum())
top=loss.sort_values(["ring_index","share_of_soy_loss"],ascending=[True,False]).groupby("ring_index").head(3)
def md(z):return z.to_markdown(index=False,floatfmt=".4g")
report=f"""# Paired 2018–2019 CDL forest-classification audit

The audit aligns the 2019 CDL raster to each 2018 reference grid and compares identical common-valid pixels inside all 348 exclusive hub–ring polygons (58 hubs × six rings). Failed downloads raise errors; missing coverage is not coded as a land class.

## Ring-level evidence

{md(s)}

Across the six bands, net soybean change is {soy_net:,} pixels. Net forest-to-soy switching (forest→soy minus soy→forest) is {forest_net:,} pixels. Therefore forest reassignment cannot mechanically explain the aggregate soybean decline if the latter is negative. The separate mixed-forest and deciduous-forest columns expose within-forest relabeling that would be hidden by an aggregate forest category.

## Largest destinations of pixels leaving soybeans

{md(top)}

## Interpretation

This is a paired classification diagnostic, not evidence that every annual series uses a permanently fixed pixel mask. A pixel transition may reflect real land-use change or classification error. The broad, coordinated 2019 increase in mixed forest alongside a decline in deciduous forest is consistent with a classification-input break, so forest subtypes should not be interpreted as ecological conversion without external validation. The soybean outcome is less mechanically vulnerable to that particular within-forest relabeling, but its 2019 movement may still reflect weather, trade conditions, crop rotation and classification error. Regression checks that omit 2019 and 2021 are retained as sensitivities rather than preferred estimates.
"""
(R/"doc"/"forest-classification-six-band-evidence.md").write_text(report)
print(s.to_string(index=False))

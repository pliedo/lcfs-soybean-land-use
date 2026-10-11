"""Three actual-site capacity scenarios; shared model, location-specific weights."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
R=Path(__file__).resolve().parents[1];C=R/'data/clean';O=R/'output/tables';F=R/'output/figures/results';F.mkdir(parents=True,exist_ok=True)
average=pd.read_csv(O/'pooled_average_100mgy_refinery.csv')
average[(average.scenario=='physical_onset_snapshot_capacity')&average.outer_miles.isin([50,75])&average.specification.isin(['current','lag1','lag2','distributed_0_2'])].to_csv(O/'average_refinery_lags_0_2_summary.csv',index=False)
plants=[('Diamond Green Diesel LLC (81496)','Norco, Louisiana'),('Phillips 66 Rodeo (82191)','Rodeo, California'),('Marathon Dickinson Refinery (F00313)','Dickinson, North Dakota')]
pred=pd.read_csv(O/'pooled_100mgy_cumulative_scenarios.csv.gz');coef=pd.read_csv(O/'pooled_ring_capacity_coefficients.csv');routes=pd.read_csv(C/'refinery_crusher_lowest_supported_mode_cost_candidates.csv');h=pd.read_csv(C/'scenario_map_crusher_coordinates.csv');cross=pd.read_csv(C/'lcfs_physical_plant_crosswalk.csv').drop_duplicates('physical_plant_id').set_index('physical_plant_id')
y=pd.read_csv(C/'crop_outcomes_exclusive.csv');y=y[(y.year==2024)&(y.ring_index<=3)&y.all_valid_acres.gt(0)]
b=coef[(coef.rule=='relative_exp100')&(coef.scenario=='physical_onset_snapshot_capacity')&(coef.specification=='lag1')&(coef.outcome=='soy_share_all_land')].set_index('ring').beta
country=json.loads((C/'scenario_map_usa_outline.geojson').read_text());geom=country.get('geometry',country.get('features',[{}])[0].get('geometry',{}));polys=geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]
panels=[]
for plant,label in plants:
 w=routes[routes.physical_plant_id==plant].copy();w['weight']=np.exp(-(w.cost_proxy_truck_equivalent_km-w.cost_proxy_truck_equivalent_km.min())/100)
 a=y.merge(w[['hub_id','weight']],on='hub_id');a['predicted_acres_change']=a.all_valid_acres/100*a.ring_index.map(b)*a.weight
 a=a.groupby('hub_id',as_index=False).predicted_acres_change.sum();a=h.merge(a,on='hub_id',how='left').fillna({'predicted_acres_change':0});a['physical_plant_id']=plant;panels.append(a)
values=pd.concat(panels);values.to_csv(O/'refinery_location_map_predictions.csv',index=False);vmax=values.predicted_acres_change.max()
fig,axes=plt.subplots(1,3,figsize=(16,9));fig.subplots_adjust(left=.025,right=.90,top=.85,bottom=.21,wspace=.05)
for ax,(plant,label),a in zip(axes,plants,panels):
 for poly in polys:
  ax.add_patch(Polygon(poly[0],closed=True,facecolor='#f1f3f5',edgecolor='#b9c0c8',linewidth=.6))
 pts=ax.scatter(a.longitude,a.latitude,c=a.predicted_acres_change,cmap='YlOrRd',vmin=0,vmax=vmax,s=30,edgecolor='#666666',linewidth=.3,zorder=3)
 lat,lon=map(float,cross.loc[plant,'coordinate_used'].split(','));ax.scatter([lon],[lat],marker='*',s=150,color='#173b63',edgecolor='white',linewidth=.5,zorder=5)
 ax.set(xlim=(-126,-66),ylim=(24,50));ax.set_aspect(1/np.cos(np.deg2rad(38)));ax.set_axis_off();ax.set_title(label,fontsize=15,color='#173b63')
 z=pred[(pred.physical_plant_id==plant)&(pred.rule=='relative_exp100')&(pred.scenario=='physical_onset_snapshot_capacity')&(pred.specification=='lag1')&(pred.outcome=='soy_share_all_land')&(pred.outer_miles==75)].iloc[0]
 ax.text(.5,-.10,f"0–75 miles: {z.predicted_acres_change:+,.0f} acres\n95% CI [{z.ci_low_acres:,.0f}, {z.ci_high_acres:,.0f}]",transform=ax.transAxes,ha='center',fontsize=12)
cb=fig.colorbar(pts,cax=fig.add_axes([.925,.35,.015,.30]));cb.set_label('Predicted additional soybean acres per crusher\n(sum across its first three rings)',fontsize=10)
fig.suptitle('Same +100 million gal/year capacity addition, different refinery locations',fontsize=21,color='#173b63',y=.96)
fig.text(.035,.12,'★ Refinery location     ● Crusher location',fontsize=12)
fig.text(.035,.045,'All-land share model converted to acres; one-year lag; relative exponential transport-cost decay.\n2024 land baseline. Common response coefficients; location-specific mode/cost weights. Potential exposure, not procurement.\nIntervals reflect coefficient uncertainty only. Observational scenario predictions; no causal or national extrapolation.',fontsize=10,color='#555555')
for ext in ['png','pdf']:fig.savefig(F/f'refinery_location_scenarios_100mgy.{ext}',dpi=180)
plt.close(fig)
fig,axes=plt.subplots(1,3,figsize=(16,9),sharey=True);fig.subplots_adjust(left=.08,right=.98,top=.82,bottom=.24,wspace=.20)
for ax,(plant,label) in zip(axes,plants):
 for rule,spec,color,offset,legend in [('nearest_eligible','lag2','#007f73',-.10,'Nearest crusher, lag 2'),('relative_exp100','lag1','#b95c21',.10,'Exponential decay, lag 1')]:
  z=pred[(pred.physical_plant_id==plant)&(pred.rule==rule)&(pred.scenario=='physical_onset_snapshot_capacity')&(pred.specification==spec)&(pred.outcome=='soy_acres')&pred.outer_miles.isin([50,75])].sort_values('outer_miles')
  xx=np.arange(2)+offset;ax.errorbar(xx,z.predicted_acres_change/1000,yerr=[(z.predicted_acres_change-z.ci_low_acres)/1000,(z.ci_high_acres-z.predicted_acres_change)/1000],fmt='o',capsize=5,color=color,label=legend)
 ax.axhline(0,color='#888888',ls='--',lw=1);ax.set_xticks([0,1],['0–50 miles','0–75 miles']);ax.set_title(label,fontsize=15);ax.spines[['top','right']].set_visible(False)
axes[0].set_ylabel('Predicted additional soybean acres (thousands)',fontsize=12);axes[1].legend(loc='upper center',bbox_to_anchor=(.5,-.12),frameon=False,ncol=2)
fig.suptitle('Location scenarios: direct-acreage estimates and 95% intervals',fontsize=21,y=.96)
fig.text(.07,.07,'Each scenario adds 100 million gal/year of eligible capacity. All three sites share estimated response coefficients.\nNearest allocation gives the same aggregate acres at every location; exponential weights allow location differences.\nModel and lag sensitivity are shown explicitly. Nominal intervals; multiple testing; observational estimates.',fontsize=11,color='#555555')
for ext in ['png','pdf']:fig.savefig(F/f'refinery_location_direct_acres_comparison.{ext}',dpi=180)

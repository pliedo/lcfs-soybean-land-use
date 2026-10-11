"""Perturb modal cost assumptions before route selection; preserve documented modes."""
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];C=R/'data/clean'
routes=pd.read_csv(C/'refinery_crusher_transport_cost_matrix.csv')
rates=pd.read_csv(C/'calibrated_modal_freight_proxy_rates.csv').set_index('mode').usd2013_per_metric_tonne_km.to_dict()
audit=pd.read_csv(C/'pathway_transport_leg_audit_reviewed.csv')
mode_map={plant:set('|'.join(g.loc[g.US_crusher_oil_route_evidence.astype(str).str.lower().eq('true'),'feedstock_modes'].fillna('')).split('|')) for plant,g in audit.groupby('physical_plant_id')}
a=routes[routes.ocean_rate_multiplier.eq(1)&routes.access_screen_eligible.astype(str).str.lower().eq('true')].copy()
def supported(r):
 modes=mode_map.get(r.physical_plant_id,set());route=r.route
 return (route=='direct_rail' and 'rail' in modes) or (route=='direct_truck' and 'truck' in modes) or (route=='inland_barge' and 'barge' in modes) or (route.startswith('truck_') and 'rail' in modes) or route=='rail_via_Artesia_pretreatment' or ('Rodeo' in r.physical_plant_id and route in ['rail_gulf_marine','river_gulf_marine','rail_Lemont_barge_StRose_marine_Rodeo'])
a=a[a.apply(supported,axis=1)&a.linehaul_cost_proxy_usd2013_per_tonne.notna()].copy()
settings=[dict(matrix_scenario='baseline',mode='',multiplier=1,handling_per_transfer=0)]
for mode in ['truck','rail','barge','ocean']:
 for mult in [.5,2]:settings.append(dict(matrix_scenario=f'{mode}_rate_x{mult:g}',mode=mode,multiplier=mult,handling_per_transfer=0))
for fee in [5,15]:settings.append(dict(matrix_scenario=f'assumed_transfer_fee_{fee}',mode='',multiplier=1,handling_per_transfer=fee))
settings.extend([dict(matrix_scenario='no_Lemont_transfer_candidate',mode='',multiplier=1,handling_per_transfer=0),dict(matrix_scenario='no_StRose_truck_rail_candidate',mode='',multiplier=1,handling_per_transfer=0)])
allpairs=routes[['hub_id','physical_plant_id']].drop_duplicates();outputs=[];diagnostics=[]
for cfg in settings:
 z=a.copy();cost=z.linehaul_cost_proxy_usd2013_per_tonne.copy()
 if cfg['mode']:
  mode=cfg['mode'];cost+=z[mode+'_km'].fillna(0)*rates[mode]*(cfg['multiplier']-1)
 modes_present=np.column_stack([z[m+'_km'].fillna(0).gt(0) for m in ['truck','rail','barge','ocean']]).sum(axis=1)
 cost+=cfg['handling_per_transfer']*np.maximum(modes_present-1,0)
 z['sensitivity_cost_usd2013_per_tonne']=cost
 if cfg['matrix_scenario']=='no_Lemont_transfer_candidate':z=z[~z.route.str.contains('Lemont')]
 if cfg['matrix_scenario']=='no_StRose_truck_rail_candidate':z=z[~z.route.eq('truck_StRose_rail')]
 best=z.sort_values('sensitivity_cost_usd2013_per_tonne').drop_duplicates(['hub_id','physical_plant_id'])
 out=allpairs.merge(best[['hub_id','physical_plant_id','route','sensitivity_cost_usd2013_per_tonne']],on=['hub_id','physical_plant_id'],how='left',validate='one_to_one')
 out['cost_proxy_truck_equivalent_km']=out.sensitivity_cost_usd2013_per_tonne/rates['truck']
 out['matrix_scenario']=cfg['matrix_scenario'];out['cost_basis']='fixed baseline truck-unit numeraire; modes constrained; route reselected after cost perturbation'
 outputs.append(out);diagnostics.append(dict(**cfg,n_pairs=len(out),eligible_pairs=int(out.route.notna().sum()),assumption_status='baseline sourced modal proxies; multipliers and fees are assumed stress tests, not observed rates'))
res=pd.concat(outputs,ignore_index=True);res.to_csv(C/'transport_matrix_sensitivity_candidates.csv',index=False)
res.to_csv(C/'transport_matrix_sensitivity_candidates.csv.gz',index=False,compression={'method':'gzip','mtime':0})
pd.DataFrame(diagnostics).to_csv(R/'output/tables/transport_matrix_sensitivity_assumptions.csv',index=False)
baseline=res[res.matrix_scenario=='baseline'].merge(pd.read_csv(C/'refinery_crusher_lowest_supported_mode_cost_candidates.csv'),on=['hub_id','physical_plant_id'],suffixes=('_new','_old'))
assert len(baseline)==928 and np.allclose(baseline.cost_proxy_truck_equivalent_km_new,baseline.cost_proxy_truck_equivalent_km_old)
print('Validated baseline; generated',len(settings),'matrices, with route reselection')

"""Distance-weighted capacity exposure and exploratory continuous-dose TWFE.

Dependencies: numpy, pandas, scipy, matplotlib, openpyxl. No raster requests.
Report coefficients as pp soybean share per 100 million gal/year exposure.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
CLEAN=ROOT/'data/clean'; OUT=ROOT/'output/tables'; FIG=ROOT/'output/figures/results'
for p in [OUT,FIG]:p.mkdir(parents=True,exist_ok=True)

def great_circle(lat1,lon1,lat2,lon2):
 a,b=np.deg2rad(lat1),np.deg2rad(lat2)
 z=np.sin((a-b)/2)**2+np.cos(a)*np.cos(b)*np.sin(np.deg2rad(lon1-lon2)/2)**2
 return 6371.0088*2*np.arcsin(np.sqrt(np.clip(z,0,1)))

def build_exposure():
 h=pd.read_excel(ROOT/'data/raw/soy_crushing_facilities.xlsx')
 h=h[(h.type.str.strip().str.lower()=='elevator')&(h.bankrupt.fillna(0)==0)].sort_values('number')
 assert len(h)==58
 cross=pd.read_csv(CLEAN/'lcfs_physical_plant_crosswalk.csv')
 raw=pd.read_csv(ROOT/'data/raw/road_distance_matrix_km.csv',index_col=0)
 raw.index=raw.index.astype(int)
 assert set(h.number)<=set(raw.index)
 rows=[]
 for plant,g in cross.groupby('physical_plant_id',sort=True):
  key=g.key.iloc[0]
  if plant=='wynnewood_ok': key='WYNNEWOOD REFINING COMPANY (82420)'
  if plant=='sinclair_wy': key='Sinclair Wyoming Refining Company (83388)'
  lat,lon=map(float,g.coordinate_used.iloc[0].split(','))
  air=great_circle(h.lon.to_numpy(),h.lat.to_numpy(),lat,lon)
  for i,hub in enumerate(h.number):
   road=raw.loc[hub,key]
   legacy=raw.loc[hub,'Wyoming Renewable Diesel Company LLC (82441)'] if plant=='sinclair_wy' else road
   rows.append(dict(hub_id=int(hub),physical_plant_id=plant,road_km=float(road),legacy_road_km=float(legacy),air_km=float(air[i]),source_carb_key=key))
 dist=pd.DataFrame(rows)
 assert (dist.road_km>=dist.air_km*.999).all(), 'Road shorter than straight-line distance: coordinate/unit audit required'
 dist.to_csv(CLEAN/'refinery_crusher_distances_physical.csv',index=False)
 dose=pd.read_csv(CLEAN/'lcfs_preplant_capacity_dose_scenarios.csv')
 weights=[];exposures=[]
 names=['inverse_1','inverse_2','exp_50mi','exp_150mi','exp_300mi','nearest_only','excess_cutoff_100mi','excess_cutoff_250mi','excess_cutoff_500mi','exp150_sum1']
 for metric in ['road_km','legacy_road_km','air_km']:
  for name in names:
   w=dist[['hub_id','physical_plant_id']].copy()
   d=dist[metric]; mn=d.groupby(dist.physical_plant_id).transform('min'); excess=d-mn
   if name.startswith('inverse'): values=(mn/d)**int(name[-1])
   elif name.startswith('excess_cutoff'): values=(excess<=float(name.split('_')[-1].replace('mi',''))*1.609344).astype(float)
   elif name=='nearest_only':
    values=np.isclose(d,mn,rtol=0,atol=.001).astype(float)
    values=values/pd.Series(values).groupby(dist.physical_plant_id).transform('sum')
   else:
    scale=150 if name=='exp150_sum1' else float(name.split('_')[-1].replace('mi',''))
    values=np.exp(-excess/(scale*1.609344))
    if name=='exp150_sum1':values=values/pd.Series(values).groupby(dist.physical_plant_id).transform('sum')
   w['weight']=np.asarray(values);w['weight_rule']=name;w['distance_metric']=metric
   weights.append(w)
   joined=dose[['scenario','physical_plant_id','year','planting_aligned_dose_mgy']].merge(w,on='physical_plant_id',validate='many_to_many')
   joined['dose_100mgy']=joined.planting_aligned_dose_mgy*joined.weight/100
   e=joined.groupby(['scenario','distance_metric','weight_rule','hub_id','year'],as_index=False).dose_100mgy.sum()
   exposures.append(e)
 pd.concat(weights,ignore_index=True).to_csv(CLEAN/'refinery_crusher_distance_weights.csv',index=False)
 exposure=pd.concat(exposures,ignore_index=True).sort_values(['scenario','distance_metric','weight_rule','hub_id','year'])
 groups=['scenario','distance_metric','weight_rule','hub_id']
 for lag in [1,2,3]:exposure[f'dose_lag{lag}']=exposure.groupby(groups).dose_100mgy.shift(lag)
 exposure['dose_lead1']=exposure.groupby(groups).dose_100mgy.shift(-1)
 exposure.to_csv(CLEAN/'crusher_year_lcfs_exposure_scenarios.csv',index=False)
 baseline=exposure[(exposure.scenario=='physical_onset_snapshot_capacity')&(exposure.distance_metric=='road_km')]
 baseline.pivot(index=['hub_id','year'],columns='weight_rule',values='dose_100mgy').reset_index().to_csv(CLEAN/'crusher_year_lcfs_exposure_baseline.csv',index=False)
 ww=pd.concat(weights,ignore_index=True)
 ww[ww.distance_metric=='road_km'].pivot(index=['hub_id','physical_plant_id'],columns='weight_rule',values='weight').reset_index().to_csv(CLEAN/'refinery_crusher_weights_baseline.csv',index=False)
 return exposure

FE_CACHE={}
def fit(data,y,xcols,trend=False):
 d=data.dropna(subset=[y]+xcols).copy()
 if len(d)<50:return []
 idx=tuple(d.index); cachekey=(idx,trend)
 if cachekey not in FE_CACHE:
  hub=pd.get_dummies(d.hub_id,drop_first=True,dtype=float).to_numpy()
  year=pd.get_dummies(d.year,drop_first=True,dtype=float).to_numpy()
  F=np.column_stack([np.ones(len(d)),hub,year])
  if trend:
   hh=pd.get_dummies(d.hub_id,dtype=float).to_numpy()
   F=np.column_stack([F,hh*(d.year.to_numpy()-2014)[:,None]])
  # SVD handles trend/year collinearity explicitly.
  u,sv,_=np.linalg.svd(F,full_matrices=False)
  rank=int((sv>sv[0]*1e-10).sum()); Q=u[:,:rank]
  FE_CACHE[cachekey]=(Q,rank)
 Q,rank=FE_CACHE[cachekey]
 X=d[xcols].to_numpy(float);Y=d[y].to_numpy(float)*100
 xr=X-Q@(Q.T@X);yr=Y-Q@(Q.T@Y)
 if np.linalg.matrix_rank(xr,tol=1e-9)<len(xcols):return []
 bread=np.linalg.inv(xr.T@xr);beta=bread@(xr.T@yr);res=yr-xr@beta
 clusters=d.hub_id.to_numpy();ids=np.unique(clusters);G=len(ids);N=len(d);K=rank+len(xcols)
 scores=np.stack([(xr[clusters==g]*res[clusters==g,None]).sum(axis=0) for g in ids])
 vcov=bread@(scores.T@scores)@bread*(G/(G-1))*((N-1)/(N-K))
 se=np.sqrt(np.maximum(np.diag(vcov),0));crit=stats.t.ppf(.975,G-1)
 result=[]
 for j,name in enumerate(xcols):
  result.append(dict(term=name,beta_pp_per_100mgy=beta[j],se=se[j],ci_low=beta[j]-crit*se[j],ci_high=beta[j]+crit*se[j],p_value=2*stats.t.sf(abs(beta[j]/se[j]),G-1),n=N,hubs=G,year_min=d.year.min(),year_max=d.year.max(),within_exposure_sd=xr[:,j].std(),exposure_sd=d[name].std(),beta_pp_per_exposure_sd=beta[j]*d[name].std()))
 return result

def estimate(exposure):
 outcomes=pd.read_csv(CLEAN/'crop_outcomes_exclusive.csv')
 outcomes=outcomes[outcomes.year.between(2014,2024)].copy()
 allresults=[]
 # Each dose series merged onto fixed outcome row indices, so FE cache is valid.
 for (scenario,metric,rule),e in exposure.groupby(['scenario','distance_metric','weight_rule']):
  panel=outcomes.merge(e[['hub_id','year','dose_100mgy','dose_lag1','dose_lag2','dose_lag3','dose_lead1']],on=['hub_id','year'],validate='many_to_one')
  baseline=scenario=='physical_onset_snapshot_capacity' and metric=='road_km'
  specs=[('current',['dose_100mgy'],'soy_share_all_land',None,False)]
  if baseline:
   specs += [('lag2',['dose_lag2'],'soy_share_all_land',None,False),('lag3',['dose_lag3'],'soy_share_all_land',None,False),('distributed_1_3',['dose_lag1','dose_lag2','dose_lag3'],'soy_share_all_land',None,False),('exclude_2024',['dose_100mgy'],'soy_share_all_land',[2024],False),('lag1',['dose_lag1'],'soy_share_all_land',None,False),('distributed_0_2',['dose_100mgy','dose_lag1','dose_lag2'],'soy_share_all_land',None,False),('exclude_2019',['dose_100mgy'],'soy_share_all_land',[2019],False),('exclude_2019_2021',['dose_100mgy'],'soy_share_all_land',[2019,2021],False),('cropland_denominator',['dose_100mgy'],'soy_share_cropland',None,False),('hub_trends',['dose_100mgy'],'soy_share_all_land',None,True),('lead_diagnostic',['dose_100mgy','dose_lead1'],'soy_share_all_land',None,False)]
  for r in range(1,7):
   base=panel[panel.ring_index==r]
   for spec,cols,y,omit,trend in specs:
    d=base if omit is None else base[~base.year.isin(omit)]
    for result in fit(d,y,cols,trend):
     result.update(scenario=scenario,distance_metric=metric,weight_rule=rule,ring_index=r,specification=spec,outcome=y)
     allresults.append(result)
 results=pd.DataFrame(allresults)
 results.to_csv(OUT/'continuous_dose_twfe_robustness.csv',index=False)
 primary=results[(results.scenario=='physical_onset_snapshot_capacity')&(results.distance_metric=='road_km')&(results.weight_rule=='exp_150mi')&(results.specification=='current')]
 primary.to_csv(OUT/'continuous_dose_twfe_baseline.csv',index=False)
 return results

def plot(results):
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
 b=results[(results.scenario=='physical_onset_snapshot_capacity')&(results.distance_metric=='road_km')&(results.specification=='current')]
 fig,axes=plt.subplots(1,2,figsize=(12.8,7.2),gridspec_kw={'width_ratios':[1,1.7]})
 p=b[b.weight_rule=='exp_150mi'].sort_values('ring_index');r=p.ring_index.to_numpy()
 axes[0].errorbar(p.beta_pp_per_100mgy,r,xerr=[p.beta_pp_per_100mgy-p.ci_low,p.ci_high-p.beta_pp_per_100mgy],fmt='o',color='#163D64',capsize=4)
 axes[0].axvline(0,color='#999999',ls=':');axes[0].set_yticks(range(1,7),[f'{(i-1)*25}–{i*25} mi' for i in range(1,7)])
 axes[0].invert_yaxis();axes[0].set_xlabel('pp per 100 million gal/year');axes[0].set_title('Baseline: exponential decay, 150 miles',loc='left',fontsize=12)
 rules=['inverse_1','inverse_2','exp_50mi','exp_150mi','exp_300mi','nearest_only','excess_cutoff_100mi','excess_cutoff_250mi','excess_cutoff_500mi','exp150_sum1']
 z=b.pivot(index='weight_rule',columns='ring_index',values='beta_pp_per_100mgy').reindex(rules)
 # Standardize exposure scale before comparing allocation with nearest=1 weights.
 std=b.pivot(index='weight_rule',columns='ring_index',values='beta_pp_per_exposure_sd').reindex(rules)
 lim=np.nanmax(abs(std.to_numpy()));im=axes[1].imshow(std,cmap='RdBu_r',vmin=-lim,vmax=lim,aspect='auto')
 axes[1].set_yticks(range(len(rules)),['Inverse distance','Inverse squared','Exp: 50 mi','Exp: 150 mi','Exp: 300 mi','Nearest only','Excess cutoff: 100 mi','Excess cutoff: 250 mi','Excess cutoff: 500 mi','Exp 150: sum-to-one'])
 axes[1].set_xticks(range(6),['0–25','25–50','50–75','75–100','100–125','125–150']);axes[1].tick_params(axis='x',labelsize=9)
 axes[1].set_xlabel('Distance band (miles)');axes[1].set_title('Weighting robustness: pp per exposure SD',loc='left',fontsize=12)
 for i in range(len(rules)):
  for j in range(6):axes[1].text(j,i,f'{std.iloc[i,j]:+.2f}',ha='center',va='center',fontsize=9,color='white' if abs(std.iloc[i,j])>lim*.6 else '#222222')
 fig.colorbar(im,ax=axes[1],fraction=.045,pad=.02)
 fig.suptitle('Preliminary soybean-share regressions',x=.08,ha='left',fontsize=20,weight='bold',y=.97)
 fig.subplots_adjust(left=.10,right=.97,top=.85,bottom=.22,wspace=.65)
 fig.text(.10,.065,'2014–2024; crusher and year fixed effects. Equal weight per observed crusher-year.\nLeft: 95% intervals clustered by crusher. Missing/zero-area bands excluded.\nExploratory associations: parallel trends, exposure validity and spatial inference remain to be established.',fontsize=10,color='#555555')
 for ext in ['png','pdf']:fig.savefig(FIG/f'continuous_dose_baseline_robustness.{ext}',dpi=200,facecolor='white')

if __name__=='__main__':
 exposure=build_exposure();results=estimate(exposure);plot(results)
 print('Regressions/coefficient rows:',len(results))
 print(pd.read_csv(OUT/'continuous_dose_twfe_baseline.csv')[['ring_index','beta_pp_per_100mgy','ci_low','ci_high','p_value','n','hubs']].to_string(index=False))

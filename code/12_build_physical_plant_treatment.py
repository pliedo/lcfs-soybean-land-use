"""Physical-plant approval/capacity panel with explicit mapping sensitivities.

Preserves original workbooks. First-ever approval is first observed in snapshot;
retired pathways remain in onset history, not an estimate of active status.
"""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw'; CLEAN=ROOT/'data/clean'; OUT=ROOT/'output/diagnostics'
for p in [CLEAN,OUT]: p.mkdir(parents=True,exist_ok=True)
f=RAW/'rd_pathways_ca_lcfs.xlsx'
pathways=pd.read_excel(f,'soy_pathways'); pathways.columns=pathways.columns.str.strip()
caps=pd.read_excel(f,'capacities'); caps.columns=caps.columns.map(str).str.strip()
locations=pd.read_excel(f,'facilities')
WY='Wyoming Renewable Diesel Company LLC (82441)'
OLD_WY='Sinclair Wyoming Refining Company (83388)'
WYN='WYNNEWOOD REFINING COMPANY (82420)'
NEW_WYN='CVR RENEWABLES WYN, LLC (83001)'
mapping=locations[['key','Standardized Name','Standard Location','coordinates']].copy()
mapping['physical_plant_id']=mapping.key
mapping.loc[mapping.key.isin([WYN,NEW_WYN]),'physical_plant_id']='wynnewood_ok'
mapping.loc[mapping.key.isin([WY,OLD_WY]),'physical_plant_id']='sinclair_wy'
mapping['mapping_status']='single_key_not_independently_audited'
mapping.loc[mapping.key.isin([WYN,NEW_WYN]),'mapping_status']='same_site_supported_by_CARB'
mapping.loc[mapping.key==WY,'mapping_status']='Sinclair_site_verified_by_CARB'
mapping.loc[mapping.key==OLD_WY,'mapping_status']='same_site_provisional_alias'
mapping['coordinate_used']=mapping.coordinates
# Representative source point at Sinclair; original coordinates retained.
sinclair_point=locations.loc[locations.key==OLD_WY,'coordinates'].iloc[0]
wyn_point=locations.loc[locations.key==WYN,'coordinates'].iloc[0]
mapping.loc[mapping.key.isin([WY,OLD_WY]),'coordinate_used']=sinclair_point
mapping.loc[mapping.key.isin([WYN,NEW_WYN]),'coordinate_used']=wyn_point
mapping['coordinate_status']='original_unverified_point'
mapping.loc[mapping.key.isin([WY,OLD_WY]),'coordinate_status']='representative_Sinclair_point_exact_point_not_independently_verified'
mapping.loc[mapping.key.isin([WYN,NEW_WYN]),'coordinate_status']='representative_Wynnewood_point'
mapping.to_csv(CLEAN/'lcfs_physical_plant_crosswalk.csv',index=False)

assert set(pathways.key)<=set(mapping.key)
pathways=pathways.merge(mapping[['key','physical_plant_id','mapping_status']],on='key',validate='many_to_one')
pathways['retired_snapshot_flag']=pathways['Retired Pathway'].fillna('').astype(str).str.strip().ne('')
pathways.to_csv(CLEAN/'lcfs_soy_pathway_history.csv',index=False)
capacity=caps.melt(id_vars=['key','Standardized Name','Location'],value_vars=[str(y) for y in range(2013,2025)],var_name='year',value_name='capacity_mgy')
capacity.year=capacity.year.astype(int)
capacity=capacity.merge(mapping[['key','physical_plant_id','coordinate_used']],on='key',validate='many_to_one')
# Duplicated keys must agree before taking a single physical capacity.
assert capacity.groupby(['physical_plant_id','year']).capacity_mgy.nunique().max()==1
farmdoc=pd.read_excel(RAW/'hefa_capacity.xlsx','farmdoc')
rows=[]
scenarios=['physical_onset_snapshot_capacity','physical_onset_farmdoc_targeted_capacity','exclude_unverified_83388','exclude_both_disputed_sites']
for scenario in scenarios:
    hist=pathways.copy(); cap=capacity.copy()
    if scenario=='exclude_unverified_83388':
        hist=hist[hist.key!=OLD_WY]; cap=cap[cap.key!=OLD_WY]
    if scenario=='exclude_both_disputed_sites':
        hist=hist[~hist.physical_plant_id.isin(['sinclair_wy','wynnewood_ok'])]
        cap=cap[~cap.physical_plant_id.isin(['sinclair_wy','wynnewood_ok'])]
    first=hist.groupby('physical_plant_id')['Certification Date'].min()
    cap=cap.drop_duplicates(['physical_plant_id','year']).copy()
    cap['capacity_source']='original_compiled_workbook'
    if scenario=='physical_onset_farmdoc_targeted_capacity':
        # Override only the two audited plants and only observed farmdoc years.
        for plant,company in [('sinclair_wy','Wyoming Renewable Diesel CO'),('wynnewood_ok','CVR Renewables Wynnewood LLC')]:
            source=farmdoc.loc[farmdoc.Company.str.strip()==company].iloc[0]
            for year in range(2020,2025):
                val=pd.to_numeric(source[year],errors='coerce')
                if pd.isna(val): val=0 # farmdoc dash = not yet operating in its table
                ix=(cap.physical_plant_id==plant)&(cap.year==year)
                cap.loc[ix,'capacity_mgy']=val
                cap.loc[ix,'capacity_source']='farmdoc_2024_11_06_targeted_override'
    for r in cap.to_dict('records'):
        approval=first.loc[r['physical_plant_id']]
        cutoff=pd.Timestamp(year=r['year'],month=5,day=1)
        rows.append(dict(scenario=scenario,physical_plant_id=r['physical_plant_id'],year=r['year'],first_observed_soy_approval=approval,
                         capacity_mgy=r['capacity_mgy'],capacity_source=r['capacity_source'],coordinates=r['coordinate_used'],
                         calendar_dose_mgy=r['capacity_mgy'] if approval.year<=r['year'] else 0,
                         planting_cutoff_dose_mgy=r['capacity_mgy'] if approval<=cutoff else 0,
                         next_year_dose_mgy=r['capacity_mgy'] if approval.year<r['year'] else 0))
panel=pd.DataFrame(rows)
assert not panel[['scenario','physical_plant_id','year']].duplicated().any()
panel.to_csv(CLEAN/'lcfs_physical_plant_year_treatment_scenarios.csv',index=False)
panel.groupby(['scenario','year'])[['capacity_mgy','calendar_dose_mgy','planting_cutoff_dose_mgy','next_year_dose_mgy']].sum().to_csv(OUT/'lcfs_physical_plant_sensitivity_totals.csv')
print('Original CARB keys:',caps.key.nunique(),'Physical plants with provisional Sinclair alias:',mapping.physical_plant_id.nunique())
print(panel[panel.year==2024].groupby('scenario')[['capacity_mgy','calendar_dose_mgy']].sum().to_string())

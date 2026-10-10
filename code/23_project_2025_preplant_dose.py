"""Provisional 2025 dose using 2024 capacity and observed approval history.
Not a complete 2025 CARB approval update. Preserves primary source scenarios.
"""
from pathlib import Path
import pandas as pd
R=Path(__file__).resolve().parents[1];c=pd.read_csv(R/'data/clean/lcfs_preplant_capacity_dose_scenarios.csv');c=c[c.year==2024].copy();c['year']=2025;c['preplant_capacity_mgy']=c.capacity_mgy;c['eligible']=pd.to_datetime(c.first_observed_soy_approval)<=pd.Timestamp('2025-05-01');c['planting_aligned_dose_mgy']=c.preplant_capacity_mgy*c.eligible;c['status']='2024_capacity_with_known_approval_history_only'
c[['scenario','physical_plant_id','year','first_observed_soy_approval','preplant_capacity_mgy','eligible','planting_aligned_dose_mgy','status']].to_csv(R/'data/clean/lcfs_2025_preplant_projection.csv',index=False)

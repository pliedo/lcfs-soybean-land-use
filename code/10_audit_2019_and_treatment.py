"""Reproduce marginal CDL break diagnostics and source-workbook linkage audit.

No marginal totals are interpreted as pixel transitions. Run from any directory.
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/diagnostics'
OUT.mkdir(parents=True, exist_ok=True)
c = pd.read_csv(ROOT / 'data/clean/cdl_class_composition_exclusive.csv')
c = c[c.cdl_code != 0].copy()
c['forest'] = c.cdl_code.isin([141,142,143])
totals = c.groupby(['ring_index','year']).pixel_count.sum()
groups = {'soy': [5], 'corn': [1], 'fallow_idle': [61], 'deciduous_forest':[141],
          'evergreen_forest':[142], 'mixed_forest':[143], 'all_forest':[141,142,143]}
rows=[]
for name,codes in groups.items():
    counts=c[c.cdl_code.isin(codes)].groupby(['ring_index','year']).pixel_count.sum().reindex(totals.index,fill_value=0)
    for (ring,year), count in counts.items():
        rows.append(dict(ring_index=ring,year=year,category=name,pixel_count=count,
                         all_valid_pixels=totals.loc[ring,year],share_pp=100*count/totals.loc[ring,year]))
pd.DataFrame(rows).to_csv(OUT/'cdl_2019_category_shares.csv',index=False)
# Check coverage stability within every hub-ring, not just aggregate totals.
v=c.groupby(['hub_id','ring_index','year']).pixel_count.sum().unstack('year')
v['valid_pixel_change_2018_2019']=v[2019]-v[2018]
v[[2018,2019,'valid_pixel_change_2018_2019']].to_csv(OUT/'cdl_2019_coverage_check.csv')

f=ROOT/'data/raw/rd_pathways_ca_lcfs.xlsx'
p=pd.read_excel(f,sheet_name='soy_pathways'); p.columns=p.columns.str.strip()
cap=pd.read_excel(f,sheet_name='capacities'); cap.columns=cap.columns.map(str).str.strip()
loc=pd.read_excel(f,sheet_name='facilities')
assert not cap.key.duplicated().any(), 'Duplicate capacity key'
assert not loc.key.duplicated().any(), 'Duplicate location key'
assert p.key.notna().all(), 'Missing pathway key'
assert set(p.key)<=set(cap.key), 'Unmatched pathway-capacity key'
assert set(p.key)<=set(loc.key), 'Unmatched pathway-location key'
p['soy_flag']=p.Feedstock.astype(str).str.contains('soy',case=False)
assert p.soy_flag.all(), 'Non-soy feedstock in soy_pathways'
p['retired']=p['Retired Pathway'].fillna('').astype(str).str.strip().ne('')
approvals=p.groupby('key').agg(first_soy_approval=('Certification Date','min'),
                              pathway_rows=('key','size'),retired_rows=('retired','sum')).reset_index()
approvals.merge(cap,on='key',validate='one_to_one').to_csv(OUT/'lcfs_approval_capacity_audit.csv',index=False)
dupes=cap[cap.duplicated(['Standardized Name','Location'],keep=False)]
dupes.to_csv(OUT/'lcfs_possible_duplicate_physical_refineries.csv',index=False)
print(f'{len(p)} soy pathway rows; {p.key.nunique()} CARB keys; {p.retired.sum()} retired rows')
print(f'{len(dupes)} capacity rows share physical name/location; unresolved, not silently deduplicated')
print(f'Hub-ring denominator changes: {(v.valid_pixel_change_2018_2019 != 0).sum()}')

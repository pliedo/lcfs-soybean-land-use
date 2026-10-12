"""Read existing CSVs only: determine classes explaining valid-area jumps."""
from pathlib import Path
import csv
from collections import defaultdict
R=Path(__file__).resolve().parents[1]
counts=defaultdict(lambda:defaultdict(int))
with (R/'data/clean/cdl_class_composition_exclusive.csv').open() as f:
 for a in csv.DictReader(f):
  if int(a['year']) not in [2024,2025]:continue
  counts[int(a['hub_id']),int(a['ring_index']),int(a['year'])][int(a['cdl_code'])]+=int(a['pixel_count'])
rows=[]
with (R/'data/clean/crop_outcomes_exclusive.csv').open() as f:
 for a in csv.DictReader(f):
  year=int(a['year'])
  if year not in [2024,2025]:continue
  hub,ring=int(a['hub_id']),int(a['ring_index']);v=counts[hub,ring,year]
  valid=sum(n for c,n in v.items() if c>0)
  assert valid==int(a['all_valid_pixels']),(hub,ring,year,valid,a['all_valid_pixels'])
  rows.append(dict(hub_id=hub,ring_index=ring,year=year,all_valid_pixels=valid,water_pixels=v[111],soy_pixels=v[5],other_nonwater_pixels=valid-v[111]-v[5]))
lookup={(a['hub_id'],a['ring_index'],a['year']):a for a in rows};changes=[]
for a in rows:
 if a['year']!=2025:continue
 b=lookup.get((a['hub_id'],a['ring_index'],2024))
 if not b or b['all_valid_pixels']==0:continue
 dv=a['all_valid_pixels']-b['all_valid_pixels'];dw=a['water_pixels']-b['water_pixels']
 changes.append(dict(hub_id=a['hub_id'],ring_index=a['ring_index'],valid_2024=b['all_valid_pixels'],valid_2025=a['all_valid_pixels'],valid_change=dv,valid_change_pct=100*dv/b['all_valid_pixels'],water_2024=b['water_pixels'],water_2025=a['water_pixels'],water_change=dw,water_fraction_of_valid_change=dw/dv if dv else None,nonwater_valid_change=dv-dw,soy_2024=b['soy_pixels'],soy_2025=a['soy_pixels']))
out=R/'output/diagnostics/coverage_2024_2025_class_count_audit.csv';out.parent.mkdir(parents=True,exist_ok=True)
with out.open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(changes[0]));w.writeheader();w.writerows(changes)
for a in sorted(changes,key=lambda a:abs(a['valid_change_pct']),reverse=True)[:6]:print(a)
print('Verified existing composition counts against outcomes; no raster requests')

"""Derive non-water shares from existing class counts; never alter original outcomes."""
from pathlib import Path
import csv,json
from collections import defaultdict
R=Path(__file__).resolve().parents[1];C=R/'data/clean';D=R/'output/diagnostics'
classes=defaultdict(lambda:defaultdict(int))
with (C/'cdl_class_composition_exclusive.csv').open() as f:
 for a in csv.DictReader(f):classes[int(a['hub_id']),int(a['ring_index']),int(a['year'])][int(a['cdl_code'])]+=int(a['pixel_count'])
rows=[];checks=[]
with (C/'crop_outcomes_exclusive.csv').open() as f:
 for a in csv.DictReader(f):
  v=classes[int(a['hub_id']),int(a['ring_index']),int(a['year'])]
  total=sum(n for code,n in v.items() if code>0)
  assert total==int(a['all_valid_pixels']);assert v[5]==int(a['soy_pixels'])
  water=v[83]+v[111];cloud=v[81];den=total-water-cloud
  assert den>=v[5]>=0
  pixarea=float(a['all_valid_acres'])/total if total else 900/4046.8564224
  b=dict(a,water_pixels=water,cloud_no_data_pixels=cloud,nonwater_valid_pixels=den,nonwater_valid_acres=den*pixarea,soy_share_nonwater=v[5]/den if den else '')
  rows.append(b);checks.append(dict(hub_id=a['hub_id'],ring_index=a['ring_index'],year=a['year'],water_pixels=water,cloud_no_data_pixels=cloud,nonwater_valid_pixels=den))
with (C/'crop_outcomes_nonwater_exclusive.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
with (D/'nonwater_denominator_audit.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(checks[0]));w.writeheader();w.writerows(checks)
print('Derived',len(rows),'rows; original soybean counts/acres unchanged; excluded water83/111 and clouds/no-data81')

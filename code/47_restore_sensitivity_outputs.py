"""Restore already-computed artifacts; verify hashes; never rerun analysis."""
from pathlib import Path
import gzip,hashlib,json
R=Path(__file__).resolve().parents[1]
manifest=json.loads((R/'output/publish_sensitivity_parts/manifest.json').read_text())
for item in manifest:
 data=[]
 for part in item['parts']:
  b=(R/part['path']).read_bytes()
  assert len(b)==part['bytes'] and hashlib.sha256(b).hexdigest()==part['sha256'],part['path']
  data.append(b)
 result=b''.join(data)
 if item['decode']=='gzip':result=gzip.decompress(result)
 assert hashlib.sha256(result).hexdigest()==item['target_sha256'],item['target']
 target=R/item['target']
 if target.exists():
  assert hashlib.sha256(target.read_bytes()).hexdigest()==item['target_sha256'],'Refusing to overwrite differing result: '+item['target']
 else:
  target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(result)
 print('Verified',item['target'],len(result),'bytes')

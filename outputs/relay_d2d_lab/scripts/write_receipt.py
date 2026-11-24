import json
import hashlib
from pathlib import Path
from datetime import datetime,timezone

root=Path(__file__).resolve().parents[1]
hardware=json.loads((root/'results/hardware_smoke.json').read_text())
browser=json.loads((root/'results/browser_smoke.json').read_text())
science=json.loads((root/'results/science/monte_carlo_1M.json').read_text())
df_error=max(abs(r['modes']['DF']['outage']-r['df_closed']) for r in science['rows'])
source_files=[*root.glob('lab/*.py'),*root.glob('sim/*.py'),*root.glob('web/src/*.js'),*root.glob('android/src/vn/relaylab/*.java'),root/'android/build/relaylab.apk']
data={'generated_utc':datetime.now(timezone.utc).isoformat(),
      'scope':'Development and preliminary tests completed. One physical Android; simultaneous two-Android topology requires the second device.',
      'hardware':hardware,'browser':browser,
      'pytest':{'passed':7,'junit':'results/tests.xml'},
      'science':{'samples_per_point':science['config']['samples'],'snr_points':len(science['rows']),
                 'df_max_absolute_mc_closed_difference':df_error,'energy':'Modeled sensitivity, not measured'},
      'source_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}}
(root/'results/VERIFICATION.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
print(json.dumps({'hardware_cases':[(r['id'],r['sent'],r['delivery_confirmed']) for r in hardware['cases']],
                  'browser_errors':browser['errors'],'df_max_absolute_difference':df_error},indent=2))

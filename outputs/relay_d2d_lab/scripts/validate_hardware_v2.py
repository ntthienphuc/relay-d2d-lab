"""Exercise only vn.relaylab on one explicitly selected, connected Android.

Does not claim two-phone/ESP32 validation. Run sequentially with other bench tools.
"""
import argparse
import json
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/validation_v2'
OUT.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--serial',required=True);args=parser.parse_args()
def api(path,data=None):
    req=urllib.request.Request('http://127.0.0.1:8765/api/'+path,
        data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=20) as r:return json.load(r)
def adb(*argv):return subprocess.check_output(['adb','-s',args.serial,*argv],text=True,encoding='utf-8').strip()
def activate(role):
    adb('shell','am','force-stop','vn.relaylab');host=api('status')['server_ip']
    adb('shell','am','start','-n','vn.relaylab/.MainActivity','--es','server',host,'--es','role',role,'--ez','auto','true')
    deadline=time.time()+20
    while time.time()<deadline:
        for d in api('status')['devices']:
            if d.get('version')=='2.0.0' and d['role']==role and d['online'] and time.time()-d.get('last_seen',0)<1.5:
                return d['id']
        time.sleep(.3)
    raise RuntimeError('Device did not register as '+role)
def wait(run):
    deadline=time.time()+run['config']['duration']+25
    while time.time()<deadline:
        time.sleep(.3);r=api('status')['run']
        if r['id']==run['id'] and r['finished']:
            time.sleep(1);return api('replay/'+str(r['id']))['summary']
    raise RuntimeError('Run timeout')
def start(**extra):
    return api('run',{'environment':'live','route':'direct','duration':10,'rate':20,'payload':128,
                     'source_id':'laptop','relay_id':'','destination_id':'laptop',**extra})
cases=[]
def keep(name,result):
    cases.append({'case':name,'summary':result});print(name,result['sent'],result['delivery_confirmed'],flush=True)
    (OUT/'hardware_v2.json').write_text(json.dumps({'scope':'One physical Android, alternated source/relay/sink. ESP32 radio and simultaneous two Android not tested.',
        'cases':cases},indent=2),encoding='utf-8')
source=activate('source')
r=wait(start(source_id=source,duration=50,experiment_label='v2 hardware Android source 1000'))
assert r['sent']==1000 and r['acked']>0 and r['received_observed']>0 and r['complete_send'];keep('android_source_1000',r)
r=wait(start(source_id=source,corrupt_every=5,experiment_label='v2 intentional CRC corruption'))
assert r['sent']==200 and 0<r['acked']<=160 and r['invalid']>0;keep('source_corruption',r)
relay=activate('relay')
r=wait(start(route='relay',relay_id=relay,duration=50,experiment_label='v2 Android relay 1000'))
assert r['sent']==1000 and r['acked']>0;keep('android_relay_1000',r)
r=start(route='relay',relay_id=relay,duration=8,experiment_label='v2 controlled pause')
time.sleep(2);api('pause-relay',{});time.sleep(2);api('pause-relay',{});r=wait(r)
assert 0<r['acked']<r['sent'] and r['dropped_by_relay']>0;keep('relay_pause',r)
r=wait(start(route='relay',relay_id=relay,drop_every=4,experiment_label='v2 relay injected drop'))
assert r['dropped_by_relay']>0 and 0<r['acked']<=150;keep('relay_injected_loss',r)
sink=activate('sink')
r=wait(start(destination_id=sink,payload=512,experiment_label='v2 Android sink 512B'))
assert r['sent']==200 and r['acked']>0 and r['received_observed']>0;keep('android_sink',r)
source=activate('source');r=start(source_id=source,duration=20,experiment_label='v2 operator stop')
time.sleep(2);api('stop',{});r=wait(r)
assert not r['complete_send'] and r['stop_reason']=='operator_stop';keep('source_cancel',r)
print('Hardware v2 validation complete',flush=True)
